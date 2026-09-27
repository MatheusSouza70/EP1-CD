/* ==========================================================================
   MODELO DIMENSIONAL — CAMADA SILVER
   Arquitetura: Esquema Estrela (Star Schema)
   Grão da Fato: Participação individual em combate (2 registros por luta)
========================================================================== */

CREATE SCHEMA IF NOT EXISTS silver;

/* --------------------------------------------------------------------------
   DIMENSÕES BASE
-------------------------------------------------------------------------- */

-- Dimensão: Geração
CREATE TABLE IF NOT EXISTS silver.dim_geracao (
    sk_geracao              SERIAL          PRIMARY KEY,
    id_geracao              INT             NOT NULL UNIQUE,
    descricao_geracao       TEXT,
    regiao                  TEXT
);

-- Dimensão: Habitat (Conceito obsoleto após gerações I-III)
CREATE TABLE IF NOT EXISTS silver.dim_habitat (
    sk_habitat              SERIAL          PRIMARY KEY,
    nome_habitat            TEXT            NOT NULL UNIQUE,
    observacao              TEXT
);

-- Dimensão: Cor
CREATE TABLE IF NOT EXISTS silver.dim_cor (
    sk_cor                  SERIAL          PRIMARY KEY,
    nome_cor                TEXT            NOT NULL UNIQUE
);

-- Dimensão: Forma Corporal
CREATE TABLE IF NOT EXISTS silver.dim_forma_corporal (
    sk_forma_corporal       SERIAL          PRIMARY KEY,
    nome_forma_corporal     TEXT            NOT NULL UNIQUE
);

-- Dimensão: Taxa de Crescimento
CREATE TABLE IF NOT EXISTS silver.dim_taxa_crescimento (
    sk_taxa_crescimento     SERIAL          PRIMARY KEY,
    nome_taxa_crescimento   TEXT            NOT NULL UNIQUE
);

-- Dimensão: Tipo
CREATE TABLE IF NOT EXISTS silver.dim_tipo (
    sk_tipo                 SERIAL          PRIMARY KEY,
    id_tipo_api             INT             UNIQUE,
    nome_tipo               TEXT            NOT NULL UNIQUE,
    eh_valido_jogo          BOOLEAN         NOT NULL DEFAULT TRUE,
    eh_membro_especial      BOOLEAN         NOT NULL DEFAULT FALSE
);

/* --------------------------------------------------------------------------
   DIMENSÃO PRINCIPAL: POKÉMON
-------------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS silver.dim_pokemon (
    sk_pokemon              SERIAL          PRIMARY KEY,
    numero_pokedex          INT,
    id_api                  INT,
    id_csv                  INT             UNIQUE,
    nome_original           TEXT,
    nome_api                TEXT,
    eh_forma_alternativa    BOOLEAN         DEFAULT FALSE,
    eh_padrao               BOOLEAN         DEFAULT TRUE,
    pokemon_pai_pokedex     INT,
    
    -- Atributos Físicos e Base
    altura                  NUMERIC(8,3),
    peso                    NUMERIC(8,3),
    experiencia_base        INT,
    hp_base                 INT,
    ataque_base             INT,
    defesa_base             INT,
    ataque_especial_base    INT,
    defesa_especial_base    INT,
    velocidade_base         INT,
    taxa_captura            INT,
    felicidade_base         INT,
    
    -- Classificações
    eh_lendario             BOOLEAN         DEFAULT FALSE,
    eh_mitico               BOOLEAN         DEFAULT FALSE,
    eh_bebe                 BOOLEAN         DEFAULT FALSE,
    categoria_raridade      TEXT,
    
    -- Chaves Estrangeiras (Relacionamentos)
    sk_geracao              INT             REFERENCES silver.dim_geracao(sk_geracao),
    sk_habitat              INT             REFERENCES silver.dim_habitat(sk_habitat),
    sk_cor                  INT             REFERENCES silver.dim_cor(sk_cor),
    sk_forma_corporal       INT             REFERENCES silver.dim_forma_corporal(sk_forma_corporal),
    sk_taxa_crescimento     INT             REFERENCES silver.dim_taxa_crescimento(sk_taxa_crescimento),
    sk_tipo_primario        INT             REFERENCES silver.dim_tipo(sk_tipo),
    sk_tipo_secundario      INT             REFERENCES silver.dim_tipo(sk_tipo),
    
    -- Metadados e Controle
    eh_membro_especial      BOOLEAN         DEFAULT FALSE,
    _fonte                  TEXT,
    _ingerido_em            TIMESTAMPTZ
);

/* --------------------------------------------------------------------------
   TABELAS DE RELACIONAMENTO E FATOS
-------------------------------------------------------------------------- */

-- Tabela de Domínio: Multiplicador de efetividade entre tipos
CREATE TABLE IF NOT EXISTS silver.efetividade_tipo (
    sk_efetividade          SERIAL          PRIMARY KEY,
    sk_tipo_atacante        INT             NOT NULL REFERENCES silver.dim_tipo(sk_tipo),
    sk_tipo_defensor        INT             NOT NULL REFERENCES silver.dim_tipo(sk_tipo),
    multiplicador           NUMERIC(4,2)    NOT NULL,
    
    UNIQUE (sk_tipo_atacante, sk_tipo_defensor)
);

-- Tabela Fato: Registro de confrontos
CREATE TABLE IF NOT EXISTS silver.fato_confronto (
    sk_fato_confronto       SERIAL          PRIMARY KEY,
    id_combate              INT             NOT NULL,
    lado                    SMALLINT        NOT NULL CHECK (lado IN (1,2)),
    sk_pokemon              INT             NOT NULL REFERENCES silver.dim_pokemon(sk_pokemon),
    sk_oponente             INT             NOT NULL REFERENCES silver.dim_pokemon(sk_pokemon),
    venceu                  SMALLINT        NOT NULL CHECK (venceu IN (0,1)),
    atacou_primeiro         SMALLINT        NOT NULL CHECK (atacou_primeiro IN (0,1)),
    velocidade_combatente   INT,
    velocidade_oponente     INT,
    diff_velocidade         INT,
    
    UNIQUE (id_combate, lado)
);

/* --------------------------------------------------------------------------
   TABELA DE AUDITORIA
-------------------------------------------------------------------------- */

-- Log de Conciliação
CREATE TABLE IF NOT EXISTS silver.log_conciliacao (
    id_log                  SERIAL          PRIMARY KEY,
    pokemon_id_csv          INT,
    numero_pokedex          INT,
    nome_csv                TEXT,
    nome_api                TEXT,
    formato                 TEXT,
    observacao              TEXT,
    conciliado              BOOLEAN         DEFAULT FALSE
);/* ==========================================================================
   MODELO DIMENSIONAL — CAMADA SILVER
   Arquitetura: Esquema Estrela (Star Schema)
   Grão da Fato: Participação individual em combate (2 registros por luta)
========================================================================== */

CREATE SCHEMA IF NOT EXISTS silver;

/* --------------------------------------------------------------------------
   DIMENSÕES BASE
-------------------------------------------------------------------------- */

-- Dimensão: Geração
CREATE TABLE IF NOT EXISTS silver.dim_geracao (
    sk_geracao              SERIAL          PRIMARY KEY,
    id_geracao              INT             NOT NULL UNIQUE,
    descricao_geracao       TEXT,
    regiao                  TEXT
);

-- Dimensão: Habitat (Conceito obsoleto após gerações I-III)
CREATE TABLE IF NOT EXISTS silver.dim_habitat (
    sk_habitat              SERIAL          PRIMARY KEY,
    nome_habitat            TEXT            NOT NULL UNIQUE,
    observacao              TEXT
);

-- Dimensão: Cor
CREATE TABLE IF NOT EXISTS silver.dim_cor (
    sk_cor                  SERIAL          PRIMARY KEY,
    nome_cor                TEXT            NOT NULL UNIQUE
);

-- Dimensão: Forma Corporal
CREATE TABLE IF NOT EXISTS silver.dim_forma_corporal (
    sk_forma_corporal       SERIAL          PRIMARY KEY,
    nome_forma_corporal     TEXT            NOT NULL UNIQUE
);

-- Dimensão: Taxa de Crescimento
CREATE TABLE IF NOT EXISTS silver.dim_taxa_crescimento (
    sk_taxa_crescimento     SERIAL          PRIMARY KEY,
    nome_taxa_crescimento   TEXT            NOT NULL UNIQUE
);

-- Dimensão: Tipo
CREATE TABLE IF NOT EXISTS silver.dim_tipo (
    sk_tipo                 SERIAL          PRIMARY KEY,
    id_tipo_api             INT             UNIQUE,
    nome_tipo               TEXT            NOT NULL UNIQUE,
    eh_valido_jogo          BOOLEAN         NOT NULL DEFAULT TRUE,
    eh_membro_especial      BOOLEAN         NOT NULL DEFAULT FALSE
);

/* --------------------------------------------------------------------------
   DIMENSÃO PRINCIPAL: POKÉMON
-------------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS silver.dim_pokemon (
    sk_pokemon              SERIAL          PRIMARY KEY,
    numero_pokedex          INT,
    id_api                  INT,
    id_csv                  INT             UNIQUE,
    nome_original           TEXT,
    nome_api                TEXT,
    eh_forma_alternativa    BOOLEAN         DEFAULT FALSE,
    eh_padrao               BOOLEAN         DEFAULT TRUE,
    pokemon_pai_pokedex     INT,
    
    -- Atributos Físicos e Base
    altura                  NUMERIC(8,3),
    peso                    NUMERIC(8,3),
    experiencia_base        INT,
    hp_base                 INT,
    ataque_base             INT,
    defesa_base             INT,
    ataque_especial_base    INT,
    defesa_especial_base    INT,
    velocidade_base         INT,
    taxa_captura            INT,
    felicidade_base         INT,
    
    -- Classificações
    eh_lendario             BOOLEAN         DEFAULT FALSE,
    eh_mitico               BOOLEAN         DEFAULT FALSE,
    eh_bebe                 BOOLEAN         DEFAULT FALSE,
    categoria_raridade      TEXT,
    
    -- Chaves Estrangeiras (Relacionamentos)
    sk_geracao              INT             REFERENCES silver.dim_geracao(sk_geracao),
    sk_habitat              INT             REFERENCES silver.dim_habitat(sk_habitat),
    sk_cor                  INT             REFERENCES silver.dim_cor(sk_cor),
    sk_forma_corporal       INT             REFERENCES silver.dim_forma_corporal(sk_forma_corporal),
    sk_taxa_crescimento     INT             REFERENCES silver.dim_taxa_crescimento(sk_taxa_crescimento),
    sk_tipo_primario        INT             REFERENCES silver.dim_tipo(sk_tipo),
    sk_tipo_secundario      INT             REFERENCES silver.dim_tipo(sk_tipo),
    
    -- Metadados e Controle
    eh_membro_especial      BOOLEAN         DEFAULT FALSE,
    _fonte                  TEXT,
    _ingerido_em            TIMESTAMPTZ
);

/* --------------------------------------------------------------------------
   TABELAS DE RELACIONAMENTO E FATOS
-------------------------------------------------------------------------- */

-- Tabela de Domínio: Multiplicador de efetividade entre tipos
CREATE TABLE IF NOT EXISTS silver.efetividade_tipo (
    sk_efetividade          SERIAL          PRIMARY KEY,
    sk_tipo_atacante        INT             NOT NULL REFERENCES silver.dim_tipo(sk_tipo),
    sk_tipo_defensor        INT             NOT NULL REFERENCES silver.dim_tipo(sk_tipo),
    multiplicador           NUMERIC(4,2)    NOT NULL,
    
    UNIQUE (sk_tipo_atacante, sk_tipo_defensor)
);

-- Tabela Fato: Registro de confrontos
CREATE TABLE IF NOT EXISTS silver.fato_confronto (
    sk_fato_confronto       SERIAL          PRIMARY KEY,
    id_combate              INT             NOT NULL,
    lado                    SMALLINT        NOT NULL CHECK (lado IN (1,2)),
    sk_pokemon              INT             NOT NULL REFERENCES silver.dim_pokemon(sk_pokemon),
    sk_oponente             INT             NOT NULL REFERENCES silver.dim_pokemon(sk_pokemon),
    venceu                  SMALLINT        NOT NULL CHECK (venceu IN (0,1)),
    atacou_primeiro         SMALLINT        NOT NULL CHECK (atacou_primeiro IN (0,1)),
    velocidade_combatente   INT,
    velocidade_oponente     INT,
    diff_velocidade         INT,
    
    UNIQUE (id_combate, lado)
);

/* --------------------------------------------------------------------------
   TABELA DE AUDITORIA
-------------------------------------------------------------------------- */

-- Log de Conciliação
CREATE TABLE IF NOT EXISTS silver.log_conciliacao (
    id_log                  SERIAL          PRIMARY KEY,
    pokemon_id_csv          INT,
    numero_pokedex          INT,
    nome_csv                TEXT,
    nome_api                TEXT,
    formato                 TEXT,
    observacao              TEXT,
    conciliado              BOOLEAN         DEFAULT FALSE
);