"""Testes offline do robô: python -m unittest discover tests"""
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import bot  # noqa: E402

TELEGRAM_HTML = """
<div class="tgme_widget_message_wrap js-widget_message_wrap"><div class="tgme_widget_message" data-post="canal/101">
<div class="tgme_widget_message_text js-message_text" dir="auto">🔥 SSD Kingston NV3 1TB NVMe M.2<br/><br/>De R$ 599,90<br/>Por R$ 299,90<br/>🎟️ Cupom R$ 20 OFF<br/>👉 <a href="https://www.kabum.com.br/produto/123">kabum.com.br/produto/123</a></div>
<time datetime="{agora}" class="time">10:00</time></div></div>
<div class="tgme_widget_message_wrap js-widget_message_wrap"><div class="tgme_widget_message" data-post="canal/102">
<div class="tgme_widget_message_text js-message_text" dir="auto">SSD Genérico 1TB NVMe<br/>Por R$ 149,90<br/><a href="https://shopee.com.br/x">link</a></div>
<time datetime="{agora}" class="time">10:01</time></div></div>
<div class="tgme_widget_message_wrap js-widget_message_wrap"><div class="tgme_widget_message" data-post="canal/103">
<div class="tgme_widget_message_text js-message_text" dir="auto">Mouse Logitech G502 Hero<br/>Por R$ 219,90<br/><a href="https://amazon.com.br/x">link</a></div>
<time datetime="{agora}" class="time">10:02</time></div></div>
<div class="tgme_widget_message_wrap js-widget_message_wrap"><div class="tgme_widget_message" data-post="canal/104">
<div class="tgme_widget_message_text js-message_text" dir="auto">Placa de Vídeo Gigabyte RTX 5060 Ti 16GB<br/>12x de R$ 199,00<br/>Por R$ 2.199,00 no PIX<br/><a href="https://pichau.com.br/x">link</a></div>
<time datetime="{agora}" class="time">10:03</time></div></div>
<div class="tgme_widget_message_wrap js-widget_message_wrap"><div class="tgme_widget_message" data-post="canal/105">
<div class="tgme_widget_message_text js-message_text" dir="auto">PC Gamer Ryzen 5 RTX 5060 SSD 1TB<br/>Por R$ 1.999,00<br/><a href="https://x.com/y">link</a></div>
<time datetime="{agora}" class="time">10:04</time></div></div>
"""

RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Blog</title>
<item><title>Smiles oferece até 100% de bônus nas transferências da Livelo</title>
<link>https://blog.exemplo/smiles-100</link><guid>a1</guid><pubDate>{data}</pubDate>
<description>A Smiles está oferecendo bônus de até 100% para clientes do clube.</description></item>
<item><title>LATAM Pass oferece 25% de bônus nas transferências</title>
<link>https://blog.exemplo/latam-25</link><guid>a2</guid><pubDate>{data}</pubDate>
<description>Promoção comum.</description></item>
<item><title>Smiles vende milhas com milheiro a R$ 13,50 hoje</title>
<link>https://blog.exemplo/milheiro</link><guid>a3</guid><pubDate>{data}</pubDate>
<description>Compra de milhas com desconto.</description></item>
<item><title>Review: como é voar na executiva da TAP</title>
<link>https://blog.exemplo/review</link><guid>a4</guid><pubDate>{data}</pubDate>
<description>Viagem com milhas.</description></item>
</channel></rss>"""


def estado_novo():
    return {"vistos": {}, "conteudo": {}, "historico": {}, "iniciado": True}


class TestRobo(unittest.TestCase):
    def setUp(self):
        agora_iso = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
        self.tg = bot.ler_telegram(TELEGRAM_HTML.replace("{agora}", agora_iso), "canal")
        data_rss = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
        self.rss = bot.ler_rss(RSS.replace("{data}", data_rss), "blog.exemplo")

    def test_le_telegram(self):
        self.assertEqual(len(self.tg), 5)
        self.assertEqual(self.tg[0]["link"], "https://www.kabum.com.br/produto/123")
        self.assertIsNotNone(self.tg[0]["data"])

    def test_extrai_precos_ignorando_cupom_e_parcela(self):
        t = bot.normalizar(self.tg[0]["texto"])
        self.assertEqual(bot.extrair_precos(t), (299.90, 599.90))
        t = bot.normalizar(self.tg[3]["texto"])
        self.assertEqual(bot.extrair_precos(t)[0], 2199.00)

    def test_ssd_de_marca_abaixo_do_alvo_alerta(self):
        av = bot.avaliar_hardware(self.tg[0], {})
        self.assertEqual(av["categoria"], "SSD")
        self.assertGreaterEqual(av["pontos"], 3)

    def test_marca_generica_descartada(self):
        self.assertIsNone(bot.avaliar_hardware(self.tg[1], {}))

    def test_pc_montado_descartado(self):
        self.assertIsNone(bot.avaliar_hardware(self.tg[4], {}))

    def test_preco_normal_nao_alerta(self):
        av = bot.avaliar_hardware(self.tg[2], {})
        self.assertIsNotNone(av)
        self.assertLess(av["pontos"], 3)

    def test_gpu_abaixo_do_alvo(self):
        av = bot.avaliar_hardware(self.tg[3], {})
        self.assertEqual(av["categoria"], "Placa de vídeo")
        self.assertGreaterEqual(av["pontos"], 3)

    def test_historico_detecta_queda(self):
        item = dict(self.tg[2])
        av = bot.avaliar_hardware(item, {})
        hist = {av["chave"]: [[400.0, 0], [420.0, 0], [410.0, 0]]}
        av2 = bot.avaliar_hardware(item, hist)
        self.assertGreaterEqual(av2["pontos"], 2)

    def test_milhas(self):
        res = [bot.avaliar_milhas(i) for i in self.rss]
        self.assertIsNotNone(res[0])           # 100% bônus
        self.assertIsNone(res[1])              # 25% é comum
        self.assertIsNotNone(res[2])           # milheiro barato
        self.assertIsNone(res[3])              # review, sem promoção

    def test_processar_sem_duplicar(self):
        est = estado_novo()
        alertas = bot.processar(self.tg + self.rss, est, enviar=False, log=lambda *_: None)
        titulos = [i["titulo"] for i, _ in alertas]
        self.assertEqual(len(alertas), 4, titulos)
        # rodar de novo não repete
        self.assertEqual(bot.processar(self.tg + self.rss, est, enviar=False, log=lambda *_: None), [])


if __name__ == "__main__":
    unittest.main()
