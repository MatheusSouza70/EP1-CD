/* ===================================================================================
   CONSULTAS ANALÍTICAS — EP01
   -> Etapa 1 e 2: Consultas sobre a camada Silver (Dados de Cadastro)
   -> Etapa 3 a 8: Leituras consolidadas da camada Gold 
      (Consultas diretas e sem funções de agregação complexas nas tabelas finais)
=================================================================================== */

/* -----------------------------------------------------------------------------------
   ANÁLISE 1 
   Matriz de distribuição de Pokémon por Tipo Primário e respectiva Geração.
   (Foco na verificação da consistência de dados conciliados)
----------------------------------------------------------------------------------- */
SELECT 
    dim_t.nome_tipo             AS tipo_primario,
    dim_g.id_geracao            AS geracao,
    COUNT(dim_p.sk_pokemon)     AS qtd_pokemon
FROM 
    silver.dim_pokemon AS dim_p
INNER JOIN 
    silver.dim_tipo AS dim_t 
    ON dim_t.sk_tipo = dim_p.sk_tipo_primario
INNER JOIN 
    silver.dim_geracao AS dim_g 
    ON dim_g.sk_geracao = dim_p.sk_geracao
GROUP BY 
    dim_t.nome_tipo, 
    dim_g.id_geracao
ORDER BY 
    tipo_primario ASC, 
    geracao ASC;

/* -----------------------------------------------------------------------------------
   ANÁLISE 2 
   Estatísticas médias de atributos de combate agrupados por Tipo Primário.
----------------------------------------------------------------------------------- */
SELECT 
    dim_t.nome_tipo                                     AS tipo_primario,
    ROUND(AVG(dim_p.hp_base)::numeric, 2)               AS hp_medio,
    ROUND(AVG(dim_p.ataque_base)::numeric, 2)           AS ataque_medio,
    ROUND(AVG(dim_p.defesa_base)::numeric, 2)           AS defesa_medio,
    ROUND(AVG(dim_p.ataque_especial_base)::numeric, 2)  AS sp_atk_medio,
    ROUND(AVG(dim_p.defesa_especial_base)::numeric, 2)  AS sp_def_medio,
    ROUND(AVG(dim_p.velocidade_base)::numeric, 2)       AS velocidade_medio,
    COUNT(dim_p.sk_pokemon)                             AS qtd_pokemon
FROM 
    silver.dim_pokemon AS dim_p
INNER JOIN 
    silver.dim_tipo AS dim_t 
    ON dim_t.sk_tipo = dim_p.sk_tipo_primario
GROUP BY 
    dim_t.nome_tipo
ORDER BY 
    velocidade_medio DESC;

-- Identificação do tipo com a maior velocidade média global
SELECT 
    dim_t.nome_tipo, 
    ROUND(AVG(dim_p.velocidade_base)::numeric, 2) AS velocidade_medio
FROM 
    silver.dim_pokemon AS dim_p
INNER JOIN 
    silver.dim_tipo AS dim_t 
    ON dim_t.sk_tipo = dim_p.sk_tipo_primario
GROUP BY 
    dim_t.nome_tipo
ORDER BY 
    velocidade_medio DESC
LIMIT 1;

-- Identificação do tipo com a maior resistência (defesa) média global
SELECT 
    dim_t.nome_tipo, 
    ROUND(AVG(dim_p.defesa_base)::numeric, 2) AS defesa_medio
FROM 
    silver.dim_pokemon AS dim_p
INNER JOIN 
    silver.dim_tipo AS dim_t 
    ON dim_t.sk_tipo = dim_p.sk_tipo_primario
GROUP BY 
    dim_t.nome_tipo
ORDER BY 
    defesa_medio DESC
LIMIT 1;

/* -----------------------------------------------------------------------------------
   ANÁLISE 3 
   Performance de Vitórias por Espécie (Top 10 Melhores e Top 10 Piores).
   Filtro aplicado: Amostragem mínima de 30 combates para evitar distorções 
   estatísticas de 100% de vitória/derrota com poucas lutas.
----------------------------------------------------------------------------------- */

-- Os 10 Melhores (Top 10)
SELECT 
    rank_pk.nome_pokemon, 
    rank_pk.numero_pokedex, 
    rank_pk.taxa_vitorias, 
    rank_pk.qtd_combates
FROM 
    gold.ranking_pokemon AS rank_pk
WHERE 
    rank_pk.qtd_combates >= 30
ORDER BY 
    rank_pk.taxa_vitorias DESC, 
    rank_pk.qtd_combates DESC
LIMIT 10;

-- Os 10 Piores (Bottom 10)
SELECT 
    rank_pk.nome_pokemon, 
    rank_pk.numero_pokedex, 
    rank_pk.taxa_vitorias, 
    rank_pk.qtd_combates
FROM 
    gold.ranking_pokemon AS rank_pk
WHERE 
    rank_pk.qtd_combates >= 30
ORDER BY 
    rank_pk.taxa_vitorias ASC, 
    rank_pk.qtd_combates DESC
LIMIT 10;

/* -----------------------------------------------------------------------------------
   ANÁLISE 4 
   Desempenho (Taxa de Vitórias) consolidado por Tipo Primário.
----------------------------------------------------------------------------------- */
SELECT 
    tb_tipo.nome_tipo, 
    tb_tipo.taxa_vitorias, 
    tb_tipo.qtd_combates
FROM 
    gold.taxa_vitorias_por_tipo AS tb_tipo
ORDER BY 
    tb_tipo.taxa_vitorias DESC;

/* -----------------------------------------------------------------------------------
   ANÁLISE 5 
   Impacto do desvio de velocidade no resultado das batalhas, dividido por faixas.
----------------------------------------------------------------------------------- */
SELECT 
    tb_faixa.faixa_velocidade, 
    tb_faixa.taxa_vitorias, 
    tb_faixa.qtd_confrontos
FROM 
    gold.taxa_vitorias_por_faixa_velocidade AS tb_faixa
ORDER BY 
    tb_faixa.ordem_faixa ASC;

/* -----------------------------------------------------------------------------------
   ANÁLISE 6 
   Influência do multiplicador de vantagem de tipo nas vitórias.
   (Avalia os defensores considerando ambos os tipos: 0, 0.25, 0.5, 1, 2, 4)
----------------------------------------------------------------------------------- */
SELECT 
    tb_mult.multiplicador, 
    tb_mult.taxa_vitorias_atacante, 
    tb_mult.qtd_confrontos
FROM 
    gold.taxa_vitorias_por_multiplicador AS tb_mult
ORDER BY 
    tb_mult.multiplicador ASC;

/* -----------------------------------------------------------------------------------
   ANÁLISE 7 
   Matriz cruzada de efetividade vs taxa de vitórias reais (18x18).
----------------------------------------------------------------------------------- */
SELECT 
    tb_matriz.nome_tipo_atacante        AS tipo_atacante,
    tb_matriz.nome_tipo_defensor        AS tipo_defensor,
    tb_matriz.taxa_vitorias_atacante,
    tb_matriz.multiplicador_efetividade,
    tb_matriz.qtd_confrontos
FROM 
    gold.matriz_confronto AS tb_matriz
ORDER BY 
    tipo_atacante ASC, 
    tipo_defensor ASC;

-- Análise de Anomalias: Cenários onde o resultado empírico contradiz a tabela de tipos
SELECT 
    tb_matriz.nome_tipo_atacante        AS tipo_atacante,
    tb_matriz.nome_tipo_defensor        AS tipo_defensor,
    tb_matriz.multiplicador_efetividade,
    tb_matriz.taxa_vitorias_atacante,
    tb_matriz.qtd_confrontos
FROM 
    gold.matriz_confronto AS tb_matriz
WHERE 
    (tb_matriz.multiplicador_efetividade > 1 AND tb_matriz.taxa_vitorias_atacante < 0.5)
    OR 
    (tb_matriz.multiplicador_efetividade < 1 AND tb_matriz.taxa_vitorias_atacante > 0.5)
ORDER BY 
    tipo_atacante ASC, 
    tipo_defensor ASC;

/* -----------------------------------------------------------------------------------
   ANÁLISE 8 
   Hipótese de Negócio: O habitat natural afeta a performance das espécies nas lutas?
   (Requer junção implícita na dim_habitat herdada pelas formas alternativas)
----------------------------------------------------------------------------------- */
SELECT 
    tb_hab.nome_habitat, 
    tb_hab.taxa_vitorias, 
    tb_hab.qtd_combates
FROM 
    gold.taxa_vitorias_por_habitat AS tb_hab
ORDER BY 
    tb_hab.taxa_vitorias DESC, 
    tb_hab.qtd_combates DESC;/* ===================================================================================
   CONSULTAS ANALÍTICAS — EP01
   -> Etapa 1 e 2: Consultas sobre a camada Silver (Dados de Cadastro)
   -> Etapa 3 a 8: Leituras consolidadas da camada Gold 
      (Consultas diretas e sem funções de agregação complexas nas tabelas finais)
=================================================================================== */

/* -----------------------------------------------------------------------------------
   ANÁLISE 1 
   Matriz de distribuição de Pokémon por Tipo Primário e respectiva Geração.
   (Foco na verificação da consistência de dados conciliados)
----------------------------------------------------------------------------------- */
SELECT 
    dim_t.nome_tipo             AS tipo_primario,
    dim_g.id_geracao            AS geracao,
    COUNT(dim_p.sk_pokemon)     AS qtd_pokemon
FROM 
    silver.dim_pokemon AS dim_p
INNER JOIN 
    silver.dim_tipo AS dim_t 
    ON dim_t.sk_tipo = dim_p.sk_tipo_primario
INNER JOIN 
    silver.dim_geracao AS dim_g 
    ON dim_g.sk_geracao = dim_p.sk_geracao
GROUP BY 
    dim_t.nome_tipo, 
    dim_g.id_geracao
ORDER BY 
    tipo_primario ASC, 
    geracao ASC;

/* -----------------------------------------------------------------------------------
   ANÁLISE 2 
   Estatísticas médias de atributos de combate agrupados por Tipo Primário.
----------------------------------------------------------------------------------- */
SELECT 
    dim_t.nome_tipo                                     AS tipo_primario,
    ROUND(AVG(dim_p.hp_base)::numeric, 2)               AS hp_medio,
    ROUND(AVG(dim_p.ataque_base)::numeric, 2)           AS ataque_medio,
    ROUND(AVG(dim_p.defesa_base)::numeric, 2)           AS defesa_medio,
    ROUND(AVG(dim_p.ataque_especial_base)::numeric, 2)  AS sp_atk_medio,
    ROUND(AVG(dim_p.defesa_especial_base)::numeric, 2)  AS sp_def_medio,
    ROUND(AVG(dim_p.velocidade_base)::numeric, 2)       AS velocidade_medio,
    COUNT(dim_p.sk_pokemon)                             AS qtd_pokemon
FROM 
    silver.dim_pokemon AS dim_p
INNER JOIN 
    silver.dim_tipo AS dim_t 
    ON dim_t.sk_tipo = dim_p.sk_tipo_primario
GROUP BY 
    dim_t.nome_tipo
ORDER BY 
    velocidade_medio DESC;

-- Identificação do tipo com a maior velocidade média global
SELECT 
    dim_t.nome_tipo, 
    ROUND(AVG(dim_p.velocidade_base)::numeric, 2) AS velocidade_medio
FROM 
    silver.dim_pokemon AS dim_p
INNER JOIN 
    silver.dim_tipo AS dim_t 
    ON dim_t.sk_tipo = dim_p.sk_tipo_primario
GROUP BY 
    dim_t.nome_tipo
ORDER BY 
    velocidade_medio DESC
LIMIT 1;

-- Identificação do tipo com a maior resistência (defesa) média global
SELECT 
    dim_t.nome_tipo, 
    ROUND(AVG(dim_p.defesa_base)::numeric, 2) AS defesa_medio
FROM 
    silver.dim_pokemon AS dim_p
INNER JOIN 
    silver.dim_tipo AS dim_t 
    ON dim_t.sk_tipo = dim_p.sk_tipo_primario
GROUP BY 
    dim_t.nome_tipo
ORDER BY 
    defesa_medio DESC
LIMIT 1;

/* -----------------------------------------------------------------------------------
   ANÁLISE 3 
   Performance de Vitórias por Espécie (Top 10 Melhores e Top 10 Piores).
   Filtro aplicado: Amostragem mínima de 30 combates para evitar distorções 
   estatísticas de 100% de vitória/derrota com poucas lutas.
----------------------------------------------------------------------------------- */

-- Os 10 Melhores (Top 10)
SELECT 
    rank_pk.nome_pokemon, 
    rank_pk.numero_pokedex, 
    rank_pk.taxa_vitorias, 
    rank_pk.qtd_combates
FROM 
    gold.ranking_pokemon AS rank_pk
WHERE 
    rank_pk.qtd_combates >= 30
ORDER BY 
    rank_pk.taxa_vitorias DESC, 
    rank_pk.qtd_combates DESC
LIMIT 10;

-- Os 10 Piores (Bottom 10)
SELECT 
    rank_pk.nome_pokemon, 
    rank_pk.numero_pokedex, 
    rank_pk.taxa_vitorias, 
    rank_pk.qtd_combates
FROM 
    gold.ranking_pokemon AS rank_pk
WHERE 
    rank_pk.qtd_combates >= 30
ORDER BY 
    rank_pk.taxa_vitorias ASC, 
    rank_pk.qtd_combates DESC
LIMIT 10;

/* -----------------------------------------------------------------------------------
   ANÁLISE 4 
   Desempenho (Taxa de Vitórias) consolidado por Tipo Primário.
----------------------------------------------------------------------------------- */
SELECT 
    tb_tipo.nome_tipo, 
    tb_tipo.taxa_vitorias, 
    tb_tipo.qtd_combates
FROM 
    gold.taxa_vitorias_por_tipo AS tb_tipo
ORDER BY 
    tb_tipo.taxa_vitorias DESC;

/* -----------------------------------------------------------------------------------
   ANÁLISE 5 
   Impacto do desvio de velocidade no resultado das batalhas, dividido por faixas.
----------------------------------------------------------------------------------- */
SELECT 
    tb_faixa.faixa_velocidade, 
    tb_faixa.taxa_vitorias, 
    tb_faixa.qtd_confrontos
FROM 
    gold.taxa_vitorias_por_faixa_velocidade AS tb_faixa
ORDER BY 
    tb_faixa.ordem_faixa ASC;

/* -----------------------------------------------------------------------------------
   ANÁLISE 6 
   Influência do multiplicador de vantagem de tipo nas vitórias.
   (Avalia os defensores considerando ambos os tipos: 0, 0.25, 0.5, 1, 2, 4)
----------------------------------------------------------------------------------- */
SELECT 
    tb_mult.multiplicador, 
    tb_mult.taxa_vitorias_atacante, 
    tb_mult.qtd_confrontos
FROM 
    gold.taxa_vitorias_por_multiplicador AS tb_mult
ORDER BY 
    tb_mult.multiplicador ASC;

/* -----------------------------------------------------------------------------------
   ANÁLISE 7 
   Matriz cruzada de efetividade vs taxa de vitórias reais (18x18).
----------------------------------------------------------------------------------- */
SELECT 
    tb_matriz.nome_tipo_atacante        AS tipo_atacante,
    tb_matriz.nome_tipo_defensor        AS tipo_defensor,
    tb_matriz.taxa_vitorias_atacante,
    tb_matriz.multiplicador_efetividade,
    tb_matriz.qtd_confrontos
FROM 
    gold.matriz_confronto AS tb_matriz
ORDER BY 
    tipo_atacante ASC, 
    tipo_defensor ASC;

-- Análise de Anomalias: Cenários onde o resultado empírico contradiz a tabela de tipos
SELECT 
    tb_matriz.nome_tipo_atacante        AS tipo_atacante,
    tb_matriz.nome_tipo_defensor        AS tipo_defensor,
    tb_matriz.multiplicador_efetividade,
    tb_matriz.taxa_vitorias_atacante,
    tb_matriz.qtd_confrontos
FROM 
    gold.matriz_confronto AS tb_matriz
WHERE 
    (tb_matriz.multiplicador_efetividade > 1 AND tb_matriz.taxa_vitorias_atacante < 0.5)
    OR 
    (tb_matriz.multiplicador_efetividade < 1 AND tb_matriz.taxa_vitorias_atacante > 0.5)
ORDER BY 
    tipo_atacante ASC, 
    tipo_defensor ASC;

/* -----------------------------------------------------------------------------------
   ANÁLISE 8 
   Hipótese de Negócio: O habitat natural afeta a performance das espécies nas lutas?
   (Requer junção implícita na dim_habitat herdada pelas formas alternativas)
----------------------------------------------------------------------------------- */
SELECT 
    tb_hab.nome_habitat, 
    tb_hab.taxa_vitorias, 
    tb_hab.qtd_combates
FROM 
    gold.taxa_vitorias_por_habitat AS tb_hab
ORDER BY 
    tb_hab.taxa_vitorias DESC, 
    tb_hab.qtd_combates DESC;