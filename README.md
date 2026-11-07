# 🤖 Robô de Promoções Absurdas

Lê canais públicos de promoção do Telegram e blogs de milhas a cada 15 minutos.
Te avisa no Telegram **só** quando aparece:

- **Peça ou periférico de PC** de **marca confiável** com preço **muito abaixo do normal**
- **Milhas**: bônus de transferência de 90% ou mais, milheiro muito barato ou possível erro tarifário

Custo: **R$ 0**. Roda grátis no GitHub e você não precisa deixar o PC ligado.

---

## Como o robô decide o que é "absurdo"

Cada oferta passa por filtros e ganha pontos. Só chega pra você se fizer **3 pontos ou mais**.

| Filtro | O que faz |
|---|---|
| Categoria | Só aceita peças e periféricos de PC. PC montado, notebook, celular, usado e kit upgrade são descartados. |
| Marca | Só passa se tiver uma marca da lista de confiáveis. Marcas genéricas são bloqueadas. |
| Preço-alvo | Preço abaixo do valor-alvo daquele produto: **+3** (15% abaixo do alvo: +1 extra) |
| Desconto real | 45% ou mais: +1. 60% ou mais: +2 |
| Histórico | 25% ou mais abaixo do preço que o próprio robô já viu para o mesmo produto: **+2** |
| Palavras-chave | "bug", "erro de preço", "menor preço histórico"...: +2 |

O robô também **aprende**: guarda os preços que vê e, com o tempo, reconhece sozinho quando um produto caiu muito.

---

## Instalação (uns 10 minutos)

### 1. Crie o seu bot no Telegram
1. No Telegram, abra o **@BotFather** e mande `/newbot`.
2. Escolha um nome. Ele te devolve um **token** parecido com `123456789:AAH...`. Guarde.
3. Abra o seu bot novo e mande um "oi" pra ele.
4. No navegador, abra: `https://api.telegram.org/botSEU_TOKEN/getUpdates`
   e procure `"chat":{"id":123456789`. Esse número é o seu **chat id**.

### 2. Crie o repositório no GitHub
1. Crie uma conta grátis em github.com, se ainda não tiver.
2. Clique em **New repository**, dê um nome (ex.: `robo-promocoes`) e marque **Public**.
   *Repositório público tem minutos ilimitados de graça. Ninguém vê seu token. Se preferir privado,
   troque no arquivo `.github/workflows/robo.yml` o `*/15` por `*/30` para não passar do limite grátis.*
3. Clique em **uploading an existing file** e arraste **todo o conteúdo da pasta descompactada**,
   incluindo a pasta `.github`. Depois clique em **Commit changes**.
   - Se a pasta `.github` não subir (no Mac/Windows ela pode ficar oculta), use **Add file → Create new file**,
     digite o nome `.github/workflows/robo.yml` e cole o conteúdo do arquivo.

### 3. Guarde as senhas
No repositório: **Settings → Secrets and variables → Actions → New repository secret**. Crie dois:
- `TELEGRAM_TOKEN` = o token do BotFather
- `TELEGRAM_CHAT_ID` = o seu chat id

### 4. Ligue o robô
1. Abra a aba **Actions** e, se pedir, clique em **I understand... enable**.
2. Clique em **Robo de Promocoes → Run workflow**.
3. Em cerca de 1 minuto chega no Telegram a mensagem **"🤖 Robô ligado!"**. Ela também lista
   as fontes que não responderam.

Pronto. A partir daí ele roda sozinho a cada ~15 minutos. O GitHub às vezes atrasa alguns minutos.

---

## Ajustando (arquivo `config.py`)

Dá pra editar direto no site do GitHub, clicando no lápis ✏️:

- **`CANAIS_TELEGRAM_HARDWARE`**: os canais marcados "(verificar)" são palpites. Se a mensagem
  "Robô ligado" disser que algum não respondeu, troque pelo @ certo ou apague. Pode adicionar qualquer
  canal **público** de promoção que você conheça: só o nome, sem `@`.
- **`PRECOS_ALVO`**: o mais importante. Os valores iniciais são estimativas de nov/2026, com RAM e SSD
  caros por causa da crise de memória. Se estiver chegando coisa demais, baixe os valores. Se não
  chegar nada em uma semana, suba um pouco.
- **`MARCAS_CONFIAVEIS` / `MARCAS_BLOQUEADAS`**: coloque ou tire marcas.
- **`PONTUACAO_MINIMA`**: suba para 4 se quiser ainda menos alertas.
- **`BONUS_TRANSFERENCIA_MINIMO` / `MILHEIRO_MAXIMO`**: os limites para milhas.

## Comandos úteis (se quiser rodar no seu PC)
```bash
python bot.py --testar-telegram   # manda mensagem de teste
python bot.py --checar-fontes     # mostra quais fontes respondem
python bot.py --simular           # mostra no terminal o que seria enviado, sem enviar
python -m unittest discover tests # testes
```
No PC, defina antes as variáveis `TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID`. Não precisa instalar nada: é só Python 3.

## Limitações
- Amazon, Shopee, Mercado Livre e AliExpress não têm API grátis de preços. O robô pega as ofertas
  dessas lojas pelos canais de promoção que postam links delas.
- Promoção absurda acaba em minutos. O alerta chega com até ~15 minutos de atraso.
- Sempre confira vendedor (de preferência a própria loja, "vendido e entregue por"), frete e o preço final no carrinho.
