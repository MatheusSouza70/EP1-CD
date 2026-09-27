/* ==========================================================================
   CAMADA GOLD (DATAMART)
   Agregações materializadas no nível das perguntas de negócio (Análises 3-8)
========================================================================== */

CREATE SCHEMA IF NOT EXISTS gold;

/* --------------------------------------------------------------------------
   Tabela: gold.ranking_pokemon
   Grão: Nível de Espécie / Pokémon (Referência: Análise 3)
-------------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS gold.ranking_pokemon (
    sk_pokemon          INT             PRIMARY KEY,
    nome_pokemon        TEXT,
    numero_pokedex      INT,
    taxa_vitorias       NUMERIC(7,5),
    qtd_combates        INT
);

/* --------------------------------------------------------------------------
   Tabela: gold.taxa_vitorias_por_tipo
   Grão: Tipo Primário (Referência: Análise 4)
-------------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS gold.taxa_vitorias_por_tipo (
    sk_tipo             INT             PRIMARY KEY,
    nome_tipo           TEXT,
    taxa_vitorias       NUMERIC(7,5),
    qtd_combates        INT
);

/* --------------------------------------------------------------------------
   Tabela: gold.taxa_vitorias_por_faixa_velocidade
   Grão: Faixa de Desvio de Velocidade (Referência: Análise 5)
-------------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS gold.taxa_vitorias_por_faixa_velocidade (
    faixa_velocidade    TEXT            PRIMARY KEY,
    ordem_faixa         INT             NOT NULL,
    limite_inferior     INT,
    limite_superior     INT,
    taxa_vitorias       NUMERIC(7,5),
    qtd_confrontos      INT
);

/* --------------------------------------------------------------------------
   Tabela: gold.taxa_vitorias_por_multiplicador
   Grão: Multiplicador de Vantagem/Efetividade (Referência: Análise 6)
-------------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS gold.taxa_vitorias_por_multiplicador (
    multiplicador           NUMERIC(4,2)    PRIMARY KEY,
    taxa_vitorias_atacante  NUMERIC(7,5),
    qtd_confrontos          INT
);

/* --------------------------------------------------------------------------
   Tabela: gold.matriz_confronto
   Grão: Cruzamento (Atacante vs Defensor) - Matriz 18x18 (Referência: Análise 7)
-------------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS gold.matriz_confronto (
    sk_tipo_atacante            INT             NOT NULL,
    sk_tipo_defensor            INT             NOT NULL,
    nome_tipo_atacante          TEXT,
    nome_tipo_defensor          TEXT,
    taxa_vitorias_atacante      NUMERIC(7,5),
    multiplicador_efetividade   NUMERIC(4,2),
    qtd_confrontos              INT,
    
    PRIMARY KEY (sk_tipo_atacante, sk_tipo_defensor)
);

/* --------------------------------------------------------------------------
   Tabela: gold.taxa_vitorias_por_habitat
   Grão: Habitat de Origem da Espécie (Referência: Análise 8 - Proposta)
-------------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS gold.taxa_vitorias_por_habitat (
    sk_habitat          INT             PRIMARY KEY,
    nome_habitat        TEXT,
    taxa_vitorias       NUMERIC(7,5),
    qtd_combates        INT
);

/* --------------------------------------------------------------------------
   Tabela: gold.log_publicacao
   Propósito: Auditoria e registro de execuções das cargas na camada gold
-------------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS gold.log_publicacao (
    id_log              SERIAL          PRIMARY KEY,
    tabela              TEXT            NOT NULL,
    qtd_linhas          INT             NOT NULL,
    carregado_em        TIMESTAMPTZ     NOT NULL DEFAULT CURRENT_TIMESTAMP
);/* ==========================================================================
   CAMADA GOLD (DATAMART)
   Agregações materializadas no nível das perguntas de negócio (Análises 3-8)
========================================================================== */

CREATE SCHEMA IF NOT EXISTS gold;

/* --------------------------------------------------------------------------
   Tabela: gold.ranking_pokemon
   Grão: Nível de Espécie / Pokémon (Referência: Análise 3)
-------------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS gold.ranking_pokemon (
    sk_pokemon          INT             PRIMARY KEY,
    nome_pokemon        TEXT,
    numero_pokedex      INT,
    taxa_vitorias       NUMERIC(7,5),
    qtd_combates        INT
);

/* --------------------------------------------------------------------------
   Tabela: gold.taxa_vitorias_por_tipo
   Grão: Tipo Primário (Referência: Análise 4)
-------------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS gold.taxa_vitorias_por_tipo (
    sk_tipo             INT             PRIMARY KEY,
    nome_tipo           TEXT,
    taxa_vitorias       NUMERIC(7,5),
    qtd_combates        INT
);

/* --------------------------------------------------------------------------
   Tabela: gold.taxa_vitorias_por_faixa_velocidade
   Grão: Faixa de Desvio de Velocidade (Referência: Análise 5)
-------------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS gold.taxa_vitorias_por_faixa_velocidade (
    faixa_velocidade    TEXT            PRIMARY KEY,
    ordem_faixa         INT             NOT NULL,
    limite_inferior     INT,
    limite_superior     INT,
    taxa_vitorias       NUMERIC(7,5),
    qtd_confrontos      INT
);

/* --------------------------------------------------------------------------
   Tabela: gold.taxa_vitorias_por_multiplicador
   Grão: Multiplicador de Vantagem/Efetividade (Referência: Análise 6)
-------------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS gold.taxa_vitorias_por_multiplicador (
    multiplicador           NUMERIC(4,2)    PRIMARY KEY,
    taxa_vitorias_atacante  NUMERIC(7,5),
    qtd_confrontos          INT
);

/* --------------------------------------------------------------------------
   Tabela: gold.matriz_confronto
   Grão: Cruzamento (Atacante vs Defensor) - Matriz 18x18 (Referência: Análise 7)
-------------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS gold.matriz_confronto (
    sk_tipo_atacante            INT             NOT NULL,
    sk_tipo_defensor            INT             NOT NULL,
    nome_tipo_atacante          TEXT,
    nome_tipo_defensor          TEXT,
    taxa_vitorias_atacante      NUMERIC(7,5),
    multiplicador_efetividade   NUMERIC(4,2),
    qtd_confrontos              INT,
    
    PRIMARY KEY (sk_tipo_atacante, sk_tipo_defensor)
);

/* --------------------------------------------------------------------------
   Tabela: gold.taxa_vitorias_por_habitat
   Grão: Habitat de Origem da Espécie (Referência: Análise 8 - Proposta)
-------------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS gold.taxa_vitorias_por_habitat (
    sk_habitat          INT             PRIMARY KEY,
    nome_habitat        TEXT,
    taxa_vitorias       NUMERIC(7,5),
    qtd_combates        INT
);

/* --------------------------------------------------------------------------
   Tabela: gold.log_publicacao
   Propósito: Auditoria e registro de execuções das cargas na camada gold
-------------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS gold.log_publicacao (
    id_log              SERIAL          PRIMARY KEY,
    tabela              TEXT            NOT NULL,
    qtd_linhas          INT             NOT NULL,
    carregado_em        TIMESTAMPTZ     NOT NULL DEFAULT CURRENT_TIMESTAMP
);