# =====================================================================
#  CONFIGURAÇÃO DO ROBÔ DE PROMOÇÕES ABSURDAS
#  Edite à vontade: é aqui que você decide o que é "absurdo" pra você.
#  Tudo é comparado sem acento e em minúsculas.
# =====================================================================

# ---------------------------------------------------------------------
# 1) FONTES
# ---------------------------------------------------------------------
# Canais PÚBLICOS do Telegram (só o @ do canal, sem o @).
# O robô lê a página pública t.me/s/<canal>, então não precisa entrar neles.
# Rode `python bot.py --checar-fontes` para ver quais estão respondendo.
CANAIS_TELEGRAM_HARDWARE = [
    "ofertaskabum",
    "promobit",
    "achadosdotb",
    "pichauofertas",
    "pelandobr",
    "terabyteshopoficial",
]

CANAIS_TELEGRAM_MILHAS = [
    # adicione canais públicos de milhas, se quiser
]

# Feeds RSS (blogs WordPress costumam ter /feed/)
FEEDS_RSS_HARDWARE = [
    # ex.: "https://algum-site.com.br/feed/"
]

FEEDS_RSS_MILHAS = [
    "https://passageirodeprimeira.com/feed/",
    "https://www.melhoresdestinos.com.br/feed",
    "https://pontospravoar.com/feed/",
]

# Ignora posts mais velhos que isso (em horas), quando a fonte informa a data
IDADE_MAXIMA_HORAS = 36

# ---------------------------------------------------------------------
# 2) HARDWARE: o que conta como "item de PC"
# ---------------------------------------------------------------------
# Ordem importa: a primeira categoria que bater é a usada.
CATEGORIAS = {
    "Placa de vídeo": [r"placa de video", r"\brtx ?\d{4}", r"\bgtx ?\d{4}", r"\brx ?\d{4}", r"\barc [ab]\d{3}"],
    "Placa-mãe":      [r"placa[ -]mae", r"\b[abhxz]\d{3}m?\b.*(ddr|am[45]|lga)"],
    "Processador":    [r"processador", r"\bryzen [3579]\b", r"\bcore (i[3579]|ultra)\b"],
    "Memória RAM":    [r"memoria ram", r"\bddr[45]\b"],
    "SSD":            [r"\bssd\b", r"\bnvme\b"],
    "HD":             [r"\bhd (interno|externo)\b", r"\bhdd\b"],
    "Fonte":          [r"\bfonte\b.*\b\d{3,4} ?w\b", r"80 ?plus"],
    "Gabinete":       [r"\bgabinete\b"],
    "Refrigeração":   [r"water ?cooler", r"air ?cooler", r"\bcooler\b", r"pasta termica", r"\bfans?\b"],
    "Monitor":        [r"\bmonitor\b"],
    "Mouse":          [r"\bmouse\b(?! ?pad)"],
    "Teclado":        [r"\bteclado\b"],
    "Headset/Fone":   [r"\bheadset\b", r"fone de ouvido"],
    "Mousepad":       [r"mouse ?pad"],
    "Webcam/Mic":     [r"\bwebcam\b", r"microfone"],
    "Rede":           [r"roteador", r"adaptador (wi-?fi|bluetooth)", r"placa de rede", r"\bmesh\b"],
    "Controle":       [r"\bcontrole\b.*(pc|xbox|dualsense|sem fio)"],
}

# Se aparecer qualquer um destes, a oferta é descartada
TERMOS_EXCLUIDOS = [
    "pc gamer", "computador completo", "kit upgrade", "notebook", "celular",
    "smartphone", "iphone", "smart tv", "capinha", "pelicula", "usado",
    "recondicionado", "seminovo", "vitrine", "openbox", "open box",
]

# ---------------------------------------------------------------------
# 3) QUALIDADE: só marcas boas
# ---------------------------------------------------------------------
# Modo estrito: só alerta se aparecer pelo menos uma marca desta lista.
EXIGIR_MARCA_CONFIAVEL = True

MARCAS_CONFIAVEIS = [
    # processador / gpu / placa-mãe
    "amd", "intel", "nvidia", "asus", "rog", "tuf", "msi", "gigabyte", "aorus",
    "asrock", "zotac", "pny", "palit", "galax", "sapphire", "powercolor", "xfx",
    "inno3d", "gainward", "colorful", "evga",
    # armazenamento / memória
    "kingston", "fury", "samsung", "western digital", "wd black", "wd blue", "wd_black",
    "crucial", "sandisk", "seagate", "corsair", "xpg", "adata", "lexar",
    "teamgroup", "t-force", "kingston fury", "solidigm", "sk hynix", "hiksemi",
    # periféricos
    "logitech", "razer", "steelseries", "hyperx", "redragon", "attack shark",
    "zowie", "pulsar", "lamzu", "keychron", "akko", "royal kludge", "rk ",
    "fifine", "elgato", "jbl", "sony", "edifier", "8bitdo", "gamesir", "xbox", "dualsense",
    # monitores
    "lg ", "lg ultragear", "dell", "alienware", "aoc", "acer", "predator", "nitro",
    "benq", "philips", "koorui", "lenovo", "legion",
    # fontes / gabinetes / cooler
    "cooler master", "nzxt", "lian li", "thermaltake", "deepcool", "noctua",
    "arctic", "be quiet", "seasonic", "super flower", "fsp", "montech", "pcyes",
    "thermalright", "id-cooling", "rise mode", "fractal",
    # rede
    "tp-link", "tp link", "mercusys", "ubiquiti", "intelbras",
]

# Marcas/termos que você NÃO quer de jeito nenhum
MARCAS_BLOQUEADAS = [
    "generico", "sem marca", "replica", "kingspec", "goldenfir", "knup",
    "exbom", "lehmox", "b-max", "kapbom", "tomate", "inova", "xtrad",
    "mbtech", "hoopson", "shinka", "kit gamer",
]

# ---------------------------------------------------------------------
# 4) O QUE É "ABSURDO" (preço-alvo)
# ---------------------------------------------------------------------
# Se o preço ficar ABAIXO do valor, a oferta ganha muitos pontos.
# ATENÇÃO: valores de partida (nov/2026), com RAM e SSD caros por causa
# da crise de memória. Ajuste para a sua realidade.
# Formato: (regex no texto, preço máximo em R$, nome)
PRECOS_ALVO = [
    (r"(ssd|nvme).*\b1 ?tb\b|\b1 ?tb\b.*(ssd|nvme)",           380,  "SSD 1TB"),
    (r"(ssd|nvme).*\b2 ?tb\b|\b2 ?tb\b.*(ssd|nvme)",           750,  "SSD 2TB"),
    (r"(ssd|nvme).*\b(480|500|512) ?gb\b",                      200,  "SSD 500GB"),
    (r"ddr5.*\b32 ?gb\b|\b32 ?gb\b.*ddr5",                     1600, "DDR5 32GB"),
    (r"ddr5.*\b16 ?gb\b|\b16 ?gb\b.*ddr5",                     850,  "DDR5 16GB"),
    (r"ddr4.*\b16 ?gb\b|\b16 ?gb\b.*ddr4",                     550,  "DDR4 16GB"),
    (r"rtx ?5060 ?ti",                                          2400, "RTX 5060 Ti"),
    (r"rtx ?5060(?! ?ti)",                                      1750, "RTX 5060"),
    (r"rtx ?5070 ?ti",                                          4600, "RTX 5070 Ti"),
    (r"rtx ?5070(?! ?ti)",                                      3500, "RTX 5070"),
    (r"rtx ?5080",                                              6500, "RTX 5080"),
    (r"rx ?9060 ?xt",                                           2100, "RX 9060 XT"),
    (r"rx ?9070 ?xt",                                           4000, "RX 9070 XT"),
    (r"ryzen 5 ?(7600|9600)",                                   750,  "Ryzen 5 7600/9600"),
    (r"ryzen 7 ?(7800|9800) ?x3d",                              2000, "Ryzen 7 X3D"),
    (r"ryzen 7 ?(7700|9700)",                                   1200, "Ryzen 7 7700/9700"),
    (r"b650",                                                   650,  "Placa-mãe B650"),
    (r"b850",                                                   800,  "Placa-mãe B850"),
    (r"monitor.*(27|32).*(1440p|qhd|2k).*(1[4-9]\d|2\d\d) ?hz", 1000, "Monitor QHD 144Hz+"),
    (r"monitor.*(24|23|27).*(1080p|full ?hd|fhd).*(1[4-9]\d|2\d\d) ?hz", 550, "Monitor FHD 144Hz+"),
    (r"fonte.*(650|700|750) ?w.*gold|gold.*(650|700|750) ?w", 380,  "Fonte 650-750W Gold"),
    (r"g203|g ?pro.*hero|viper mini",                           80,   "Mouse de entrada bom"),
    (r"superlight|viper v3|g ?pro x",                           550,  "Mouse top"),
    (r"teclado.*mecanico",                                      180,  "Teclado mecânico"),
    (r"headset|fone de ouvido",                                 150,  "Headset"),
]

# ---------------------------------------------------------------------
# 5) PONTUAÇÃO (só alerta acima do mínimo)
# ---------------------------------------------------------------------
PONTUACAO_MINIMA = 3

PALAVRAS_DE_OFERTA_ABSURDA = [
    "bug", "erro de preco", "preco errado", "menor preco historico",
    "minimo historico", "menor preco ja visto", "preco historico",
    "nunca esteve tao barato", "absurdo", "insano",
]

# ---------------------------------------------------------------------
# 6) MILHAS
# ---------------------------------------------------------------------
PALAVRAS_MILHAS = [
    "milhas", "milheiro", "smiles", "latam pass", "tudoazul", "azul fidelidade",
    "livelo", "esfera", "tap miles", "avios", "iberia", "aadvantage", "pontos",
    "transferencia bonificada", "passagens", "passagem",
]

# Bônus de transferência a partir deste % é considerado absurdo
BONUS_TRANSFERENCIA_MINIMO = 90

# Preço máximo do milheiro (R$ por 1.000 milhas/pontos) por programa
MILHEIRO_MAXIMO = {
    "smiles": 15.0,
    "latam": 23.0,
    "azul": 15.0,
    "tudoazul": 15.0,
    "livelo": 36.0,
    "esfera": 32.0,
    "tap": 25.0,
    "padrao": 15.0,
}

PALAVRAS_ERRO_TARIFARIO = [
    "erro tarifario", "tarifa erro", "erro de tarifa", "tarifa bugada",
    "passagem bugada", "erro de preco",
]

# ---------------------------------------------------------------------
# 7) ENVIO
# ---------------------------------------------------------------------
MAX_ALERTAS_POR_RODADA = 15
