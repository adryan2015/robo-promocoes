#!/usr/bin/env python3
"""
Robô de promoções ABSURDAS (hardware de PC e milhas) -> alerta no Telegram.

Uso:
  python bot.py                  roda uma vez (é o que o GitHub Actions faz)
  python bot.py --testar-telegram  manda uma mensagem de teste
  python bot.py --checar-fontes    mostra quais fontes estão respondendo
  python bot.py --simular          roda sem enviar nada (mostra no terminal)

Variáveis de ambiente: TELEGRAM_TOKEN e TELEGRAM_CHAT_ID.
Não usa nenhuma biblioteca externa: só Python 3.9+.
"""
import email.utils
import hashlib
import html
import json
import os
import re
import statistics
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import config

ARQUIVO_ESTADO = os.environ.get("ARQUIVO_ESTADO", "state.json")
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
AGORA = time.time()


# ============================== utilidades ==============================

def normalizar(txt):
    """minúsculas, sem acento, espaços simples."""
    txt = unicodedata.normalize("NFKD", txt or "")
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", txt.lower()).strip()


def limpar_html(txt):
    txt = re.sub(r"<br\s*/?>", "\n", txt or "", flags=re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = html.unescape(txt)
    return re.sub(r"[ \t]+", " ", txt).strip()


def baixar(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "pt-BR,pt;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def tem_termo(texto_norm, termo):
    termo = normalizar(termo)
    return re.search(r"(?<![a-z0-9])" + re.escape(termo) + r"(?![a-z0-9])", texto_norm) is not None


def fmt_reais(v):
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + s


def hash_curto(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


# ============================== coleta ==============================

def ler_rss(xml_txt, fonte):
    """Lê RSS 2.0 ou Atom e devolve lista de itens."""
    itens = []
    xml_txt = re.sub(r"^[^<]+", "", xml_txt)  # lixo antes do XML
    raiz = ET.fromstring(xml_txt)
    atom = "{http://www.w3.org/2005/Atom}"
    content_ns = "{http://purl.org/rss/1.0/modules/content/}encoded"
    for it in raiz.iter("item"):
        titulo = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        desc = it.findtext("description") or it.findtext(content_ns) or ""
        guid = (it.findtext("guid") or link or titulo).strip()
        data = it.findtext("pubDate")
        itens.append(_item(fonte, guid, titulo, limpar_html(desc)[:1500], link, _data_rss(data)))
    for it in raiz.iter(atom + "entry"):
        titulo = (it.findtext(atom + "title") or "").strip()
        el_link = it.find(atom + "link")
        link = el_link.get("href") if el_link is not None else ""
        desc = it.findtext(atom + "summary") or it.findtext(atom + "content") or ""
        guid = (it.findtext(atom + "id") or link or titulo).strip()
        data = it.findtext(atom + "updated") or it.findtext(atom + "published")
        itens.append(_item(fonte, guid, titulo, limpar_html(desc)[:1500], link, _data_iso(data)))
    return itens


def _data_rss(s):
    try:
        return email.utils.parsedate_to_datetime(s).timestamp() if s else None
    except Exception:
        return None


def _data_iso(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() if s else None
    except Exception:
        return None


def ler_telegram(html_txt, canal):
    """Lê a página pública t.me/s/<canal>."""
    itens = []
    blocos = re.split(r'(?=<div class="tgme_widget_message_wrap)', html_txt)
    for b in blocos:
        m_post = re.search(r'data-post="([^"]+)"', b)
        m_txt = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', b, re.S)
        if not m_post or not m_txt:
            continue
        bruto = m_txt.group(1)
        texto = limpar_html(bruto)
        links = [html.unescape(u) for u in re.findall(r'href="(https?://[^"]+)"', bruto)]
        links = [u for u in links if "t.me/" not in u] or [f"https://t.me/{m_post.group(1)}"]
        m_data = re.search(r'<time[^>]+datetime="([^"]+)"', b)
        linhas = [l.strip() for l in texto.split("\n") if l.strip()]
        titulo = linhas[0][:200] if linhas else texto[:200]
        itens.append(_item(f"@{canal}", m_post.group(1), titulo, texto[:1500], links[0],
                           _data_iso(m_data.group(1)) if m_data else None,
                           link_post=f"https://t.me/{m_post.group(1)}"))
    return itens


def _item(fonte, guid, titulo, texto, link, data, link_post=None):
    return {
        "id": hash_curto(fonte + "|" + guid),
        "fonte": fonte,
        "titulo": titulo,
        "texto": texto,
        "link": link,
        "link_post": link_post,
        "data": data,
    }


def todas_as_fontes():
    fontes = []
    for c in config.CANAIS_TELEGRAM_HARDWARE + config.CANAIS_TELEGRAM_MILHAS:
        fontes.append(("telegram", c, f"https://t.me/s/{c}"))
    for u in config.FEEDS_RSS_HARDWARE + config.FEEDS_RSS_MILHAS:
        fontes.append(("rss", urllib.parse.urlparse(u).netloc, u))
    return fontes


def coletar(log=print):
    itens, erros = [], []
    for tipo, nome, url in todas_as_fontes():
        try:
            bruto = baixar(url)
            novos = ler_telegram(bruto, nome) if tipo == "telegram" else ler_rss(bruto, nome)
            if tipo == "telegram" and not novos:
                raise ValueError("canal sem posts públicos (nome errado ou canal privado?)")
            itens.extend(novos)
            log(f"  ok   {nome}: {len(novos)} posts")
        except Exception as e:
            erros.append((nome, str(e)[:120]))
            log(f"  ERRO {nome}: {str(e)[:120]}")
    return itens, erros


# ============================== preços ==============================

RE_PRECO = re.compile(r"r\$\s*(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{1,2}))?")


def extrair_precos(texto_norm):
    """Devolve (preco_atual, preco_antigo) ou (None, None)."""
    validos, preco_por, preco_de = [], None, None
    for m in RE_PRECO.finditer(texto_norm):
        valor = float(m.group(1).replace(".", "") + "." + (m.group(2) or "0"))
        antes = texto_norm[max(0, m.start() - 25):m.start()]
        depois = texto_norm[m.end():m.end() + 14]
        if re.search(r"\boff\b|desconto|de volta|cashback", depois):
            continue
        if re.search(r"acima de|minimo|compras? de|frete|cashback|parcela|\d+ ?x ?(de)?\s*$", antes):
            continue
        if valor < 5:
            continue
        validos.append(valor)
        if re.search(r"\bpor\s*$|por apenas\s*$|sai por\s*$|\bagora\s*$|🔥\s*$", antes):
            preco_por = valor
        if re.search(r"\bde\s*$|era\s*$|antes\s*$", antes):
            preco_de = valor
    if not validos:
        return None, None
    atual = preco_por if preco_por is not None else min(validos)
    antigo = preco_de if preco_de and preco_de > atual else (max(validos) if max(validos) > atual * 1.05 else None)
    return atual, antigo


def chave_produto(categoria, texto_norm):
    """Identidade aproximada do produto, p/ montar histórico de preço."""
    tokens = re.findall(r"[a-z0-9\-]+", texto_norm.split("r$")[0])
    modelo = sorted({t for t in tokens if re.search(r"\d", t) and re.search(r"[a-z]", t) and 2 < len(t) < 15})
    marcas = sorted({normalizar(mc).strip() for mc in config.MARCAS_CONFIAVEIS if tem_termo(texto_norm, mc.strip())})
    if not modelo:
        return None
    return f"{categoria}|{' '.join(marcas[:2])}|{' '.join(modelo[:5])}"


# ============================== avaliação ==============================

def avaliar_hardware(item, historico):
    t = normalizar(item["titulo"] + "\n" + item["texto"])
    if any(tem_termo(t, x) for x in config.TERMOS_EXCLUIDOS):
        return None
    categoria = next((c for c, pads in config.CATEGORIAS.items() if any(re.search(p, t) for p in pads)), None)
    if not categoria:
        return None
    if any(tem_termo(t, b.strip()) for b in config.MARCAS_BLOQUEADAS):
        return None
    marcas = [m.strip() for m in config.MARCAS_CONFIAVEIS if tem_termo(t, m.strip())]
    if config.EXIGIR_MARCA_CONFIAVEL and not marcas:
        return None
    preco, antigo = extrair_precos(t)
    if preco is None:
        return None

    pontos, motivos = 0, []
    for padrao, maximo, nome in config.PRECOS_ALVO:
        if re.search(padrao, t):
            if preco <= maximo:
                pontos += 3
                motivos.append(f"abaixo do preço-alvo de {nome} ({fmt_reais(maximo)})")
                if preco <= maximo * 0.85:
                    pontos += 1
            break

    if antigo:
        desc = 1 - preco / antigo
        if desc >= 0.60:
            pontos += 2
            motivos.append(f"{desc:.0%} de desconto")
        elif desc >= 0.45:
            pontos += 1
            motivos.append(f"{desc:.0%} de desconto")

    palavras = [p for p in config.PALAVRAS_DE_OFERTA_ABSURDA if tem_termo(t, p)]
    if palavras:
        pontos += 2
        motivos.append("anunciado como " + ", ".join(f'"{p}"' for p in palavras[:2]))

    chave = chave_produto(categoria, t)
    if chave:
        precos_ant = [p for p, _ in historico.get(chave, [])]
        if len(precos_ant) >= 3:
            mediana = statistics.median(precos_ant)
            if preco <= mediana * 0.75:
                pontos += 2
                motivos.append(f"{1 - preco / mediana:.0%} abaixo do que o robô já viu ({fmt_reais(mediana)})")

    return {
        "tipo": "hardware", "categoria": categoria, "preco": preco, "antigo": antigo,
        "marcas": marcas, "pontos": pontos, "motivos": motivos, "chave": chave,
        "chave_conteudo": f"{chave or hash_curto(t[:80])}|{round(preco)}",
    }


def _programa(t):
    for p in ["smiles", "latam", "tudoazul", "azul", "livelo", "esfera", "tap"]:
        if tem_termo(t, p):
            return p
    return "padrao"


def avaliar_milhas(item):
    t = normalizar(item["titulo"] + "\n" + item["texto"])
    if not any(tem_termo(t, p) for p in config.PALAVRAS_MILHAS):
        return None
    if re.search(r"encerrad[ao]|\[encerrada\]", t):
        return None
    programa = _programa(t)
    pontos, motivos = 0, []

    bonus = [int(x) for x in re.findall(r"(\d{2,3}) ?% (?:de )?(?:bonus|milhas bonus|pontos bonus|de milhas extras)", t)]
    bonus += [int(x) for x in re.findall(r"bonus (?:de )?(?:ate )?(\d{2,3}) ?%", t)]
    bonus_max = max(bonus) if bonus else 0
    if bonus_max >= config.BONUS_TRANSFERENCIA_MINIMO:
        pontos += 3
        motivos.append(f"{bonus_max}% de bônus")

    m = re.search(r"milheiro[^0-9]{0,40}r\$ ?(\d+(?:,\d{1,2})?)", t)
    milheiro = float(m.group(1).replace(",", ".")) if m else None
    limite = config.MILHEIRO_MAXIMO.get(programa, config.MILHEIRO_MAXIMO["padrao"])
    if milheiro and milheiro <= limite:
        pontos += 3
        motivos.append(f"milheiro a {fmt_reais(milheiro)} (limite {fmt_reais(limite)})")

    if any(tem_termo(t, p) for p in config.PALAVRAS_ERRO_TARIFARIO):
        pontos += 3
        motivos.append("possível erro tarifário")

    if not pontos:
        return None
    return {
        "tipo": "milhas", "categoria": f"Milhas ({programa})" if programa != "padrao" else "Milhas",
        "pontos": pontos, "motivos": motivos,
        "chave_conteudo": f"milhas|{programa}|{bonus_max}|{milheiro}|{hash_curto(t[:60]) if not (bonus_max or milheiro) else ''}",
    }


# ============================== telegram ==============================

def montar_mensagem(item, av):
    e = html.escape
    linhas = [f"🔥 <b>PROMOÇÃO ABSURDA · {e(av['categoria'])}</b>", "", f"<b>{e(item['titulo'][:220])}</b>"]
    if av["tipo"] == "hardware":
        p = f"💰 <b>{fmt_reais(av['preco'])}</b>"
        if av.get("antigo"):
            p += f"  (antes {fmt_reais(av['antigo'])}, -{1 - av['preco'] / av['antigo']:.0%})"
        linhas.append(p)
    linhas.append("✅ " + e("; ".join(av["motivos"])))
    if av.get("marcas"):
        linhas.append("🏷️ Marca: " + e(", ".join(av["marcas"][:2])))
    linhas += ["", f"🔗 {e(item['link'])}"]
    fonte = item["fonte"]
    if item.get("link_post"):
        fonte = f'<a href="{e(item["link_post"])}">{e(fonte)}</a>'
    linhas.append(f"📡 Fonte: {fonte}")
    if av["tipo"] == "hardware":
        linhas.append("<i>Confira preço, vendedor e frete antes de comprar.</i>")
    else:
        linhas.append("<i>Leia o regulamento: bônus máximo costuma exigir clube.</i>")
    return "\n".join(linhas)


def enviar_telegram(texto):
    token, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        raise SystemExit("Faltam TELEGRAM_TOKEN e/ou TELEGRAM_CHAT_ID.")
    dados = urllib.parse.urlencode({"chat_id": chat, "text": texto, "parse_mode": "HTML",
                                    "disable_web_page_preview": "false"}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=dados)
    with urllib.request.urlopen(req, timeout=20) as r:
        resp = json.loads(r.read())
    if not resp.get("ok"):
        raise RuntimeError(resp)


# ============================== estado ==============================

def carregar_estado():
    try:
        with open(ARQUIVO_ESTADO, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"vistos": {}, "conteudo": {}, "historico": {}, "iniciado": False}


def salvar_estado(est):
    limite_vistos = AGORA - 14 * 86400
    est["vistos"] = {k: v for k, v in est["vistos"].items() if v > limite_vistos}
    est["conteudo"] = {k: v for k, v in est["conteudo"].items() if v > AGORA - 3 * 86400}
    limite_hist = AGORA - 120 * 86400
    hist = {}
    for k, obs in est["historico"].items():
        obs = [o for o in obs if o[1] > limite_hist][-30:]
        if obs:
            hist[k] = obs
    est["historico"] = hist
    with open(ARQUIVO_ESTADO, "w", encoding="utf-8") as f:
        json.dump(est, f, ensure_ascii=False, separators=(",", ":"))


# ============================== principal ==============================

def processar(itens, est, enviar, log=print):
    """Avalia os itens, atualiza o estado e envia alertas. Devolve os alertas."""
    alertas = []
    for item in itens:
        if item["id"] in est["vistos"]:
            continue
        est["vistos"][item["id"]] = AGORA
        if item["data"] and AGORA - item["data"] > config.IDADE_MAXIMA_HORAS * 3600:
            continue
        av = avaliar_hardware(item, est["historico"]) or avaliar_milhas(item)
        if not av:
            continue
        if av["tipo"] == "hardware" and av["chave"]:
            est["historico"].setdefault(av["chave"], []).append([av["preco"], AGORA])
        if av["pontos"] < config.PONTUACAO_MINIMA:
            continue
        if av["chave_conteudo"] in est["conteudo"]:
            continue  # mesma oferta já avisada por outra fonte
        est["conteudo"][av["chave_conteudo"]] = AGORA
        alertas.append((item, av))

    alertas.sort(key=lambda x: -x[1]["pontos"])
    for item, av in alertas[:config.MAX_ALERTAS_POR_RODADA]:
        msg = montar_mensagem(item, av)
        if enviar and est.get("iniciado"):
            try:
                enviar_telegram(msg)
                time.sleep(1.2)
            except Exception as e:
                log(f"  falha ao enviar: {e}")
        else:
            log("\n" + re.sub(r"<[^>]+>", "", msg) + "\n" + "-" * 50)
    return alertas


def main():
    args = set(sys.argv[1:])
    if "--testar-telegram" in args:
        enviar_telegram("✅ <b>Robô de promoções conectado!</b>\nVocê vai receber aqui só as ofertas absurdas.")
        print("Mensagem de teste enviada.")
        return
    if "--checar-fontes" in args:
        print("Checando fontes...")
        _, erros = coletar()
        print(f"\n{len(erros)} fonte(s) com problema." if erros else "\nTodas as fontes responderam.")
        return

    simular = "--simular" in args
    est = carregar_estado()
    print("Coletando...")
    itens, erros = coletar()
    primeira_vez = not est.get("iniciado")
    alertas = processar(itens, est, enviar=not simular)
    print(f"\n{len(itens)} posts lidos, {len(alertas)} promoção(ões) absurda(s).")

    if primeira_vez and not simular:
        # 1ª execução: só aprende o que já existe, sem inundar o chat com posts velhos
        est["iniciado"] = True
        ok = len(todas_as_fontes()) - len(erros)
        aviso = "\n⚠️ Sem resposta: " + ", ".join(n for n, _ in erros) if erros else ""
        enviar_telegram(f"🤖 <b>Robô ligado!</b>\nMonitorando {ok} fonte(s). "
                        f"A partir de agora só chegam aqui as promoções absurdas.{html.escape(aviso)}")
    if not simular:
        salvar_estado(est)


if __name__ == "__main__":
    main()
