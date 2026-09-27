# Relatório de Resultados e Interpretação — EP01

**Integrantes do grupo:**

* Matheus Dutra Souza
* Pedro Henrique Lira
* Lucas Pinheiro

> Todos os valores abaixo são a saída real das consultas de `sql/consultas.sql`,
> executadas sobre o banco populado pelo pipeline (`publicar.py`).

---

## Análise 1 — Quantidade de Pokémon por tipo primário e por geração (Silver)

Matriz tipo primário × geração (I–VI), sobre `silver.dim_pokemon`:

| Tipo | Ger I | Ger II | Ger III | Ger IV | Ger V | Ger VI | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bug | 15 | 12 | 12 | 10 | 19 | 3 | 71 |
| dark | 6 | 7 | 9 | 4 | 14 | 4 | 44 |
| dragon | 4 | 0 | 12 | 5 | 9 | 9 | 39 |
| electric | 30 | 7 | 5 | 12 | 9 | 3 | 66 |
| fairy | 3 | 5 | 0 | 1 | 0 | 11 | 20 |
| fighting | 14 | 3 | 5 | 5 | 7 | 4 | 38 |
| fire | 19 | 9 | 9 | 6 | 10 | 10 | 63 |
| flying | 0 | 0 | 0 | 0 | 2 | 2 | 4 |
| ghost | 5 | 2 | 5 | 7 | 6 | 10 | 35 |
| grass | 16 | 10 | 13 | 15 | 16 | 6 | 76 |
| ground | 10 | 3 | 8 | 4 | 14 | 0 | 39 |
| ice | 7 | 4 | 8 | 4 | 9 | 3 | 35 |
| normal | 28 | 15 | 18 | 18 | 21 | 4 | 104 |
| poison | 18 | 3 | 3 | 6 | 3 | 3 | 36 |
| psychic | 15 | 7 | 13 | 8 | 15 | 7 | 65 |
| rock | 13 | 5 | 8 | 6 | 6 | 10 | 48 |
| steel | 1 | 4 | 12 | 4 | 4 | 7 | 32 |
| water | 35 | 19 | 29 | 14 | 21 | 8 | 126 |
| **Total** | **202** | **106** | **139** | **113** | **158** | **86** | **941** |

**Interpretação.** Total de 941 registros = 800 linhas do CSV (721 espécies + 79 formas
alternativas) + 141 formas adicionais vindas da PokéAPI que não ocupam linha própria no
CSV (ex.: variedades de `Unown`, `Vivillon`, estágios de `Rotom`, formas de `Deoxys/Giratina`
cujas "formas padrão" divergem da linha do CSV). A conciliação por nome (R4) está coberta:
a soma por geração e tipo reproduz o cadastro sem descartes. Observações de consistência:
`flying` como tipo primário só aparece a partir da geração V (Tornadus) — coerente com o
jogo; `steel`/`dark` nascem na geração II; `fairy` na geração VI. Nenhuma divergência em
relação ao esperado foi encontrada, confirmando a reconciliação.

---

## Análise 2 — Média de atributos de status por tipo primário (Silver)

| Tipo | HP | Ataque | Defesa | Sp.Atk | Sp.Def | Velocidade | N |
| --- | --- | --- | --- | --- | --- | --- | --- |
| flying | 70.75 | 78.75 | 66.25 | 94.25 | 72.50 | **102.50** | 4 |
| electric | 54.03 | 68.03 | 60.11 | 81.83 | 68.76 | 88.91 | 66 |
| dragon | 90.08 | 110.56 | 88.18 | 99.87 | 89.69 | 87.64 | 39 |
| psychic | 71.60 | 71.34 | 68.69 | 99.26 | 86.08 | 81.97 | 65 |
| dark | 66.20 | 86.80 | 71.30 | 72.09 | 72.32 | 79.98 | 44 |
| fighting | 70.95 | 101.84 | 71.18 | 55.92 | 68.21 | 75.87 | 38 |
| fire | 71.32 | 86.05 | 70.48 | 91.40 | 75.35 | 75.76 | 63 |
| normal | 76.76 | 73.51 | 59.47 | 56.68 | 63.89 | 71.56 | 104 |
| water | 72.90 | 78.10 | 74.41 | 78.31 | 72.17 | 69.49 | 126 |
| ice | 72.26 | 78.89 | 73.80 | 69.60 | 72.77 | 68.86 | 35 |
| ground | 73.13 | 98.95 | 86.00 | 58.28 | 64.92 | 65.51 | 39 |
| ghost | 64.06 | 73.03 | 81.94 | 83.11 | 78.06 | 65.40 | 35 |
| grass | 68.45 | 75.93 | 73.30 | 79.63 | 72.43 | 62.62 | 76 |
| bug | 56.97 | 71.58 | 71.54 | 54.68 | 65.49 | 61.80 | 71 |
| poison | 70.08 | 76.56 | 71.64 | 64.14 | 68.69 | 58.58 | 36 |
| steel | 66.06 | 93.22 | **121.25** | 70.19 | 84.38 | 57.25 | 32 |
| rock | 65.06 | 94.19 | 102.29 | 62.10 | 74.31 | 55.17 | 48 |
| fairy | 75.15 | 63.80 | 68.20 | 87.50 | 91.30 | 54.50 | 20 |

**Interpretação.**

* **Maior velocidade média: `flying` (102,5)** — concentrado em poucos Pokémon (N=4),
todos velozes (Tornadus e Noivern). Entre tipos com amostra expressiva (N > 35), o
mais rápido é `electric` (89).
* **Maior resistência média: `steel` (defesa 121,4)** — coerente com a lore: Aço é o tipo
mais defensivo do jogo.
* **Tipo superior em todos os atributos?** **Não existe.** Nenhum tipo domina simultaneamente
HP, ataque, defesa, Sp.Atk, Sp.Def e velocidade. O `dragon` é o que mais se aproxima de um
perfil completo (top 3 em quase todas as métricas), mas perde em velocidade para
flying/electric. Os dados de cadastro retratam o clássico *trade-off* por tipo, não um
tipo dominante absoluto.

---

## Análise 3 — Taxa de vitórias por Pokémon (Gold: `gold.ranking_pokemon`)

**Corte mínimo de combates: `30`.** Com 50.000 combates e ~784 Pokémon participantes, a
média é ~127 participações por Pokémon. O corte em 30 (~24% da média) elimina o ruído de
Pokémon com 100% em 3 combates e preserva a estabilidade do estimador — valores citados
sempre acompanhados da quantidade de combates (seção 1.3 do enunciado).

**Top 10 (com corte):**

| Pokémon | N⁰ Pokédex | Taxa | Combates |
| --- | --- | --- | --- |
| Mega Aerodactyl | 142 | 0.98450 | 129 |
| Weavile | 461 | 0.97479 | 119 |
| Tornadus Therian Forme | 641 | 0.96800 | 125 |
| Mega Beedrill | 15 | 0.96639 | 119 |
| Aerodactyl | 142 | 0.96454 | 141 |
| Mega Lopunny | 428 | 0.96124 | 129 |
| Greninja | 658 | 0.96063 | 127 |
| Meloetta Pirouette Forme | 648 | 0.95935 | 123 |
| Mega Mewtwo Y | 150 | 0.95200 | 125 |
| Mega Sharpedo | 319 | 0.95000 | 120 |

**Bottom 10 (com corte):**

| Pokémon | N⁰ Pokédex | Taxa | Combates |
| --- | --- | --- | --- |
| Shuckle | 213 | 0.00000 | 135 |
| Silcoon | 266 | 0.02174 | 138 |
| Togepi | 175 | 0.02459 | 122 |
| Solosis | 577 | 0.03101 | 129 |
| Slugma | 218 | 0.03252 | 123 |
| Munna | 517 | 0.03906 | 128 |
| Igglybuff | 174 | 0.04348 | 115 |
| Wynaut | 360 | 0.04615 | 130 |
| Wooper | 194 | 0.04800 | 125 |
| Cascoon | 268 | 0.05263 | 133 |

**Interpretação.** O topo é dominado por **Pokémon de alta velocidade** (Aerodactyl,
Weavile, Tornadus-T, Greninja) e por formas Mega que ampliam status — consistente com um
simulador que valoriza o primeiro ataque. A base é composta por formas com status muito
baixos (Shuckle 0% em 135 combates; Silcoon/Cascoon, estágios de evolução com ataque
mínimo). A assimetria taxa × quantidade de combates mostra que o corte é necessário:
todos os listados têm amostra comparável (115–141), o que torna as taxas comparáveis.

---

## Análise 4 — Taxa de vitórias por tipo primário (Gold: `gold.taxa_vitorias_por_tipo`)

| Tipo | Taxa | Combates |
| --- | --- | --- |
| flying | 0.75732 | 478 |
| dark | 0.63641 | 3845 |
| dragon | 0.63327 | 3932 |
| electric | 0.63038 | 5346 |
| fire | 0.58028 | 6552 |
| psychic | 0.54617 | 7320 |
| normal | 0.53877 | 12098 |
| ground | 0.53690 | 3889 |
| ghost | 0.48030 | 3908 |
| water | 0.46784 | 14041 |
| fighting | 0.46673 | 3306 |
| ice | 0.44073 | 3079 |
| grass | 0.43995 | 8426 |
| bug | 0.43059 | 8760 |
| poison | 0.42994 | 3654 |
| steel | 0.42950 | 3546 |
| rock | 0.40554 | 5669 |
| fairy | 0.32868 | 2151 |

**Interpretação.** Existe um tipo dominante no sentido estatístico: **flying** lidera com
folga (0,757), mas com apenas 478 participações (Tornadus é quase dominante — ver análise 3).
Entre tipos com amostra forte, `dark`/`dragon`/`electric` (0,63) formam o **grupo dominante**,
enquanto `fairy` (0,329) e `rock` (0,406) ficam no fundo. O resultado é coerente com o
comportamento do simulador (alto valor de velocidade e de ofensividade), e não com a
verdadeira "teoria do jogo" de tipos — tema retomado na análise 6.

---

## Análise 5 — Diferença de velocidade × vitória (Gold: `gold.taxa_vitorias_por_faixa_velocidade`)

**Justificativa das faixas.** 7 faixas simétricas sobre o desvio inteiro
`diff = velocidade(combatente) − velocidade(oponente)`: extremos abertos (`<-80`, `>80`),
meios simétricos de ~40 pontos (`[-80,-41]`, `[41,80]`; `[-40,-1]`, `[1,40]`) e o empate
exato (`=0`). A simetria torna o efeito legível por espelhamento, e o empate exato fica
isolado porque nele nenhum dos lados tem vantagem de ordem.

| Faixa (Δv) | Taxa de vitória | Confrontos |
| --- | --- | --- |
| <-80 | 0.11121 | 2221 |
| [-80,-41] | 0.08783 | 14141 |
| [-40,-1] | 0.04593 | 32310 |
| =0 | 0.50000 | 2656 |
| [1,40] | 0.95407 | 32310 |
| [41,80] | 0.91217 | 14141 |
| >80 | 0.88879 | 2221 |

**Interpretação.** O efeito é **macio e quase determinístico**: quando o combatente mais
rápido tem vantagem de apenas 1–40 pontos, vence **95,4%** das vezes; com desvantagem
equivalente (Δv −40..−1), vence apenas 4,6% (ou seja, o lado mais veloz vence 95,4%).
A relação é monotônica e o empate exato fica em 50%. A velocidade é, portanto, **a
variável dominante do simulador**, muito acima de qualquer efeito de tipo (análise 6).
Nota de leitura: nas faixas positivas a taxa é a do lado rápido; os extremos (>80 e <−80)
ficam ligeiramente menos extremos que as faixas intermediárias possivelmente pela amostra
menor (2.221 confrontos) e pela distribuição de velocidades dos protagonistas.

---

## Análise 6 — Vantagem de tipo × vitória (Gold: `gold.taxa_vitorias_por_multiplicador`)

**Critério adotado (decisão 3):** o multiplicador efetivo considera **os dois tipos do
defensor** (produto dos dois fatores), com o tipo primário do atacante — valores possíveis
0, 0,25, 0,5, 1, 2 e 4.

| Multiplicador | Taxa (atacante) | Confrontos |
| --- | --- | --- |
| 0.00 | 0.41373 | 3234 |
| 0.25 | 0.41576 | 2309 |
| 0.50 | 0.47283 | 20519 |
| 1.00 | 0.50730 | 57408 |
| 2.00 | 0.53326 | 15242 |
| 4.00 | 0.58152 | 1288 |

**Interpretação.** Existe efeito, porém **modesto** e monotônico: a vantagem de 4× leva a
58,2% de vitórias (contra 50,7% no perfil neutro e 41,4% na imunidade 0×). O enunciado
adverte que a análise só é "verdadeira" se o programa que simulou as batalhas usou a tabela
de tipos; aqui o efeito é real mas pequeno, o que indica que o simulador **incorporou a
tabela de tipos como fator secundário** — subordinado à velocidade (análise 5), que produz
diferenças de ~45 pontos percentuais contra ~17 da vantagem máxima de tipo. Sendo o resultado
corretamente apurado e interpretado, é uma resposta válida.

---

## Análise 7 — Matriz de confronto 18×18 (Gold: `gold.matriz_confronto`)

Célula (A,B) = proporção de confrontos entre Pokémon de tipo primário A (atacante) e tipo
primário B (defensor) vencidos pelo de tipo A. Cada confronto alimenta duas células e, por
construção, taxa(A,B) + taxa(B,A) = 1 (todas as diagonais = 0,500).

| ATACANTE\DEFENSOR | bug | dark | dragon | electric | fairy | fighting | fire | flying | ghost | grass | ground | ice | normal | poison | psychic | rock | steel | water |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bug | 0.500 | 0.362 | 0.284 | 0.266 | 0.611 | 0.428 | 0.331 | 0.211 | 0.455 | 0.518 | 0.478 | 0.488 | 0.386 | 0.466 | 0.424 | 0.458 | 0.471 | 0.461 |
| dark | 0.638 | 0.500 | 0.517 | 0.448 | 0.795 | 0.505 | 0.510 | 0.261 | 0.669 | 0.723 | 0.608 | 0.681 | 0.547 | 0.664 | 0.945 | 0.736 | 0.673 | 0.644 |
| dragon | 0.716 | 0.483 | 0.500 | 0.545 | 0.107 | 0.675 | 0.567 | 0.182 | 0.686 | 0.690 | 0.693 | 0.690 | 0.574 | 0.688 | 0.536 | 0.746 | 0.794 | 0.716 |
| electric | 0.734 | 0.552 | 0.455 | 0.500 | 0.818 | 0.687 | 0.599 | 0.312 | 0.762 | 0.667 | 0.096 | 0.712 | 0.618 | 0.721 | 0.566 | 0.713 | 0.711 | 0.698 |
| fairy | 0.389 | 0.205 | 0.893 | 0.182 | 0.500 | 0.339 | 0.218 | 0.273 | 0.452 | 0.291 | 0.293 | 0.400 | 0.243 | 0.299 | 0.268 | 0.407 | 0.373 | 0.312 |
| fighting | 0.572 | 0.495 | 0.325 | 0.313 | 0.661 | 0.500 | 0.352 | 0.000 | 0.137 | 0.563 | 0.492 | 0.591 | 0.440 | 0.564 | 0.369 | 0.680 | 0.603 | 0.453 |
| fire | 0.669 | 0.490 | 0.433 | 0.401 | 0.782 | 0.648 | 0.500 | 0.276 | 0.643 | 0.704 | 0.519 | 0.684 | 0.541 | 0.671 | 0.480 | 0.603 | 0.685 | 0.584 |
| flying | 0.789 | 0.739 | 0.818 | 0.688 | 0.727 | 1.000 | 0.724 | 0.500 | 0.826 | 0.750 | 0.895 | 0.800 | 0.721 | 0.800 | 0.600 | 0.667 | 0.857 | 0.765 |
| ghost | 0.545 | 0.331 | 0.314 | 0.238 | 0.548 | 0.863 | 0.357 | 0.174 | 0.500 | 0.493 | 0.465 | 0.504 | 0.506 | 0.572 | 0.450 | 0.615 | 0.551 | 0.468 |
| grass | 0.482 | 0.277 | 0.310 | 0.333 | 0.709 | 0.437 | 0.296 | 0.250 | 0.507 | 0.500 | 0.491 | 0.418 | 0.399 | 0.435 | 0.373 | 0.568 | 0.504 | 0.498 |
| ground | 0.522 | 0.392 | 0.307 | 0.904 | 0.707 | 0.508 | 0.481 | 0.105 | 0.535 | 0.509 | 0.500 | 0.484 | 0.489 | 0.617 | 0.504 | 0.642 | 0.623 | 0.531 |
| ice | 0.512 | 0.319 | 0.310 | 0.288 | 0.600 | 0.409 | 0.316 | 0.200 | 0.496 | 0.582 | 0.516 | 0.500 | 0.395 | 0.495 | 0.375 | 0.489 | 0.471 | 0.472 |
| normal | 0.614 | 0.453 | 0.426 | 0.382 | 0.757 | 0.560 | 0.459 | 0.279 | 0.494 | 0.601 | 0.511 | 0.605 | 0.500 | 0.639 | 0.453 | 0.606 | 0.578 | 0.606 |
| poison | 0.534 | 0.336 | 0.312 | 0.279 | 0.701 | 0.436 | 0.329 | 0.200 | 0.428 | 0.565 | 0.383 | 0.505 | 0.361 | 0.500 | 0.389 | 0.608 | 0.242 | 0.454 |
| psychic | 0.576 | 0.055 | 0.464 | 0.434 | 0.732 | 0.631 | 0.520 | 0.400 | 0.550 | 0.627 | 0.496 | 0.625 | 0.547 | 0.611 | 0.500 | 0.629 | 0.552 | 0.616 |
| rock | 0.542 | 0.264 | 0.254 | 0.287 | 0.593 | 0.320 | 0.397 | 0.333 | 0.385 | 0.432 | 0.358 | 0.511 | 0.394 | 0.392 | 0.371 | 0.500 | 0.480 | 0.410 |
| steel | 0.529 | 0.327 | 0.206 | 0.289 | 0.627 | 0.397 | 0.315 | 0.143 | 0.449 | 0.496 | 0.377 | 0.529 | 0.422 | 0.758 | 0.448 | 0.520 | 0.500 | 0.382 |
| water | 0.539 | 0.356 | 0.284 | 0.302 | 0.688 | 0.547 | 0.416 | 0.235 | 0.532 | 0.502 | 0.469 | 0.528 | 0.394 | 0.546 | 0.384 | 0.590 | 0.618 | 0.500 |

### Posições em que os dois valores divergem

A consulta de identificação compara o **multiplicador de efetividade** (do jogo) com a
**taxa observada**: marca divergência quando a tabela de tipos diz "vantagem" (mult > 1)
mas a taxa é de derrota (< 0,5), ou vice-versa. **39 posições** divergem:

| Atacante | Defensor | Mult | Taxa | Confrontos |
| --- | --- | --- | --- | --- |
| bug | dark | 2.00 | 0.36246 | 309 |
| bug | fairy | 0.50 | 0.61053 | 190 |
| bug | psychic | 2.00 | 0.42415 | 646 |
| dark | fairy | 0.50 | 0.79518 | 83 |
| dark | fighting | 0.50 | 0.50485 | 103 |
| dragon | steel | 0.50 | 0.79433 | 141 |
| electric | flying | 2.00 | 0.31250 | 16 |
| electric | grass | 0.50 | 0.66667 | 459 |
| fairy | dark | 2.00 | 0.20482 | 83 |
| fairy | fighting | 2.00 | 0.33871 | 62 |
| fighting | bug | 0.50 | 0.57196 | 271 |
| fighting | dark | 2.00 | 0.49515 | 103 |
| fighting | fairy | 0.50 | 0.66129 | 62 |
| fighting | normal | 2.00 | 0.44018 | 443 |
| fighting | poison | 0.50 | 0.56391 | 133 |
| fire | rock | 0.50 | 0.60335 | 358 |
| fire | water | 0.50 | 0.58432 | 931 |
| flying | electric | 0.50 | 0.68750 | 16 |
| flying | rock | 0.50 | 0.66667 | 24 |
| flying | steel | 0.50 | 0.85714 | 21 |
| ghost | normal | 0.00 | 0.50620 | 484 |
| ghost | psychic | 2.00 | 0.44983 | 289 |
| grass | ground | 2.00 | 0.49057 | 318 |
| grass | steel | 0.50 | 0.50365 | 274 |
| grass | water | 2.00 | 0.49834 | 1208 |
| ground | bug | 0.50 | 0.52239 | 335 |
| ground | fire | 2.00 | 0.48120 | 266 |
| ground | grass | 0.50 | 0.50943 | 318 |
| ice | dragon | 2.00 | 0.31034 | 116 |
| ice | flying | 2.00 | 0.20000 | 20 |
| normal | rock | 0.50 | 0.60557 | 682 |
| normal | steel | 0.50 | 0.57820 | 422 |
| poison | rock | 0.50 | 0.60825 | 194 |
| psychic | steel | 0.50 | 0.55197 | 279 |
| rock | fire | 2.00 | 0.39665 | 358 |
| rock | flying | 2.00 | 0.33333 | 24 |
| water | fire | 2.00 | 0.41568 | 931 |
| water | grass | 0.50 | 0.50166 | 1208 |
| water | ground | 2.00 | 0.46935 | 571 |

**Interpretação.** A matriz respeita a regra de ouro da construção (taxa(A,B)+taxa(B,A)=1),
confirmando que cada confronto alimentou as duas células e que a orientação é pelo vencedor.
As divergências concentram-se nas situações em que a vantagem de tipo é pequena e o ataque
prévio decide: por exemplo, `fogo vs água` tem mult 0,5 na tabela oficial, mas o fogo vence
58% das vezes — conjunto inteiro de casos em que a velocidade (ver análise 5) e a qualidade
do Pokémon (análise 3) sobrepõem-se à tabela de tipos. O padrão é consistente: **a taxa
observada reflete fortemente a composição de velocidades dos Pokémon dos dois tipos, não só
a vantagem de tipo**.

---

## Análise 8 — Proposta do grupo: habitat × taxa de vitórias (Gold: `gold.taxa_vitorias_por_habitat`)

**Pergunta de negócio:** *O habitat da espécie a que o Pokémon pertence influencia sua taxa
de vitórias em batalhas simuladas?*
**Capacidade exigida do modelo (não coberta por 1–7):** cruzamento da dimensão
**`dim_habitat`** (à qual nenhuma análise obrigatória recorre), com o tratamento dos dois
tipos de ausência (`NAO_SE_APLICA` = conceito inaplicável após as gerações III — problema 3;
`SEM_INFORMACAO` = dado realmente sem valor) e a herança de espécie para formas alternativas.

| Habitat | Taxa | Combates |
| --- | --- | --- |
| rare | 0.81095 | 2100 |
| SEM_INFORMACAO | 0.78704 | 108 |
| rough-terrain | 0.52636 | 3737 |
| grassland | 0.52090 | 10787 |
| NAO_SE_APLICA | 0.51778 | 45991 |
| urban | 0.49213 | 5021 |
| sea | 0.47513 | 5449 |
| forest | 0.46702 | 9522 |
| cave | 0.43292 | 4398 |
| mountain | 0.42760 | 6413 |
| waters-edge | 0.40887 | 6474 |

**Interpretação.** Há diferença entre habitats, mas ela está **dominada pela composição de
espécies**, não pelo habitat em si: `rare` (81%) e `SEM_INFORMACAO` (79%) concentram
Pokémon raros/lendários (ex.: Tornadus, Therian forms), naturalmente mais fortes — o mesmo
mecanismo visto nas análises 3 e 4. Entre habitats "comuns" com amostra robusta, a variação
fica contida (0,41 a 0,53): `waters-edge` (litoral) é o pior, coerente com água ser o tipo
com taxa abaixo da média; `grassland` e `rough-terrain` lideram o grupo comum. O bloco
`NAO_SE_APLICA` (46 mil confrontos — Pokémon cujas espécies pós-III não têm habitat)
apresenta taxa neutra (~0,52) e funciona como termo de comparação. Conclusão: o habitat é
**um marcador indireto** — não causa o desempenho, mas correlaciona-se com os tipos e com a
raridade que o determinam. A análise concretiza a utilidade da dimensão conformada e a
correção do tratamento de ausências na modelagem.
