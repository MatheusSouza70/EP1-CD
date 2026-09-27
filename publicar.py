#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 Script de Publicação: Camada Silver (PostgreSQL) -> Camada Gold (PostgreSQL)
===============================================================================
 - Aplica o arquivo DDL versionado (sql/gold.sql)
 - Materializa as tabelas de agregação consultando os dados consolidados 
   na camada Silver
 - Mantém controle e auditoria de cargas na tabela gold.log_publicacao
 - Execução 100% idempotente (processo de esvaziar e recarregar)
===============================================================================
"""

import os
from pathlib import Path
import psycopg


# =============================================================================
# CONSTANTES E PARÂMETROS DE CONEXÃO
# =============================================================================
DIRETORIO_ATUAL = Path(__file__).resolve().parent

HOST_BANCO = os.getenv("PG_HOST", "localhost")
PORTA_BANCO = int(os.getenv("PG_PORT", "5432"))
NOME_BANCO = os.getenv("PG_DB", "pokedex")
USUARIO_BANCO = os.getenv("PG_USER", "postgres")
SENHA_BANCO = os.getenv("PG_PASSWORD", "postgres")


def iniciar_conexao():
    return psycopg.connect(
        host=HOST_BANCO, 
        port=PORTA_BANCO, 
        dbname=NOME_BANCO, 
        user=USUARIO_BANCO, 
        password=SENHA_BANCO
    )


def rodar_script_sql(conexao, caminho_arquivo):
    conteudo_sql = caminho_arquivo.read_text(encoding="utf-8")
    with conexao.cursor() as cursor:
        cursor.execute(conteudo_sql)


# =============================================================================
# QUERIES DE MATERIALIZAÇÃO (DATAMART)
# =============================================================================
DICIONARIO_CARGAS = {
    
    # Análise 3 — Desempenho e vitórias no grão: Pokémon
    "gold.ranking_pokemon": """
        WITH participantes AS (
            SELECT 
                sk_pokemon, 
                SUM(venceu) AS vitorias, 
                COUNT(*)    AS combates
            FROM 
                silver.fato_confronto
            GROUP BY 
                sk_pokemon
        )
        SELECT 
            p.sk_pokemon, 
            d.nome_original, 
            d.numero_pokedex,
            ROUND(vitorias::numeric / combates, 5), 
            combates
        FROM 
            participantes p
        JOIN 
            silver.dim_pokemon d 
            ON d.sk_pokemon = p.sk_pokemon;
    """,

    # Análise 4 — Taxa de vitórias por Tipo Primário
    "gold.taxa_vitorias_por_tipo": """
        WITH participacoes AS (
            SELECT 
                f.venceu, 
                d.sk_tipo_primario
            FROM 
                silver.fato_confronto f
            JOIN 
                silver.dim_pokemon d 
                ON d.sk_pokemon = f.sk_pokemon
        )
        SELECT 
            t.sk_tipo, 
            t.nome_tipo,
            ROUND(AVG(p.venceu::numeric), 5) AS taxa,
            COUNT(*)                         AS combates
        FROM 
            participacoes p
        JOIN 
            silver.dim_tipo t 
            ON t.sk_tipo = p.sk_tipo_primario
        GROUP BY 
            t.sk_tipo, 
            t.nome_tipo;
    """,

    # Análise 5 — Efeito do desvio de velocidade agrupado por faixas
    "gold.taxa_vitorias_por_faixa_velocidade": """
        WITH bandas AS (
            SELECT
                CASE
                    WHEN f.diff_velocidade <= -81 THEN '<-80'
                    WHEN f.diff_velocidade <= -41 THEN '[-80,-41]'
                    WHEN f.diff_velocidade <= -1  THEN '[-40,-1]'
                    WHEN f.diff_velocidade = 0    THEN '=0'
                    WHEN f.diff_velocidade <= 40  THEN '[1,40]'
                    WHEN f.diff_velocidade <= 80  THEN '[41,80]'
                    ELSE                               '>80'
                END AS faixa,
                CASE
                    WHEN f.diff_velocidade <= -81 THEN 1
                    WHEN f.diff_velocidade <= -41 THEN 2
                    WHEN f.diff_velocidade <= -1  THEN 3
                    WHEN f.diff_velocidade = 0    THEN 4
                    WHEN f.diff_velocidade <= 40  THEN 5
                    WHEN f.diff_velocidade <= 80  THEN 6
                    ELSE                               7
                END AS ordem,
                CASE
                    WHEN f.diff_velocidade <= -81 THEN NULL
                    WHEN f.diff_velocidade <= -41 THEN -80
                    WHEN f.diff_velocidade <= -1  THEN -40
                    WHEN f.diff_velocidade = 0    THEN 0
                    WHEN f.diff_velocidade <= 40  THEN 1
                    WHEN f.diff_velocidade <= 80  THEN 41
                    ELSE                               81
                END AS li,
                CASE
                    WHEN f.diff_velocidade <= -81 THEN -81
                    WHEN f.diff_velocidade <= -41 THEN -41
                    WHEN f.diff_velocidade <= -1  THEN -1
                    WHEN f.diff_velocidade = 0    THEN 0
                    WHEN f.diff_velocidade <= 40  THEN 40
                    WHEN f.diff_velocidade <= 80  THEN 80
                    ELSE                               NULL
                END AS ls,
                f.venceu
            FROM 
                silver.fato_confronto f
            WHERE 
                f.diff_velocidade IS NOT NULL
        )
        SELECT 
            faixa, 
            ordem, 
            li, 
            ls,
            ROUND(AVG(venceu::numeric), 5), 
            COUNT(*)
        FROM 
            bandas
        GROUP BY 
            faixa, 
            ordem, 
            li, 
            ls
        ORDER BY 
            ordem;
    """,

    # Análise 6 — Desempenho ponderado pelo multiplicador de vantagem de tipo
    "gold.taxa_vitorias_por_multiplicador": """
        WITH mult AS (
            SELECT 
                f.venceu,
                ef1.multiplicador * COALESCE(ef2.multiplicador, 1) AS multiplicador
            FROM 
                silver.fato_confronto f
            JOIN 
                silver.dim_pokemon d1 
                ON d1.sk_pokemon = f.sk_pokemon
            JOIN 
                silver.dim_pokemon d2 
                ON d2.sk_pokemon = f.sk_oponente
            JOIN 
                silver.efetividade_tipo ef1
                ON ef1.sk_tipo_atacante = d1.sk_tipo_primario
                AND ef1.sk_tipo_defensor = d2.sk_tipo_primario
            LEFT JOIN 
                silver.efetividade_tipo ef2
                ON ef2.sk_tipo_atacante = d1.sk_tipo_primario
                AND ef2.sk_tipo_defensor = d2.sk_tipo_secundario
        )
        SELECT 
            multiplicador,
            ROUND(AVG(venceu::numeric), 5) AS taxa,
            COUNT(*)                       AS qtd
        FROM 
            mult
        GROUP BY 
            multiplicador
        ORDER BY 
            multiplicador;
    """,

    # Análise 7 — Cruzamento de tipos 18x18 (Eficácia x Resultado Real)
    "gold.matriz_confronto": """
        SELECT 
            d1.sk_tipo_primario, 
            d2.sk_tipo_primario,
            t1.nome_tipo, 
            t2.nome_tipo,
            ROUND(AVG(f.venceu::numeric), 5) AS taxa,
            ef.multiplicador,
            COUNT(*)                         AS qtd
        FROM 
            silver.fato_confronto f
        JOIN 
            silver.dim_pokemon d1 
            ON d1.sk_pokemon = f.sk_pokemon
        JOIN 
            silver.dim_pokemon d2 
            ON d2.sk_pokemon = f.sk_oponente
        JOIN 
            silver.dim_tipo t1 
            ON t1.sk_tipo = d1.sk_tipo_primario
        JOIN 
            silver.dim_tipo t2 
            ON t2.sk_tipo = d2.sk_tipo_primario
        JOIN 
            silver.efetividade_tipo ef
            ON ef.sk_tipo_atacante = d1.sk_tipo_primario
            AND ef.sk_tipo_defensor = d2.sk_tipo_primario
        GROUP BY 
            d1.sk_tipo_primario, 
            d2.sk_tipo_primario,
            t1.nome_tipo, 
            t2.nome_tipo, 
            ef.multiplicador
        ORDER BY 
            t1.nome_tipo, 
            t2.nome_tipo;
    """,

    # Análise 8 — Avaliação de impacto do habitat de origem da espécie
    "gold.taxa_vitorias_por_habitat": """
        WITH hab AS (
            SELECT 
                f.venceu, 
                d.sk_habitat
            FROM 
                silver.fato_confronto f
            JOIN 
                silver.dim_pokemon d 
                ON d.sk_pokemon = f.sk_pokemon
            WHERE 
                d.sk_habitat IS NOT NULL
        )
        SELECT 
            h.sk_habitat, 
            h.nome_habitat,
            ROUND(AVG(hab.venceu::numeric), 5) AS taxa,
            COUNT(*)                           AS qtd
        FROM 
            hab
        JOIN 
            silver.dim_habitat h 
            ON h.sk_habitat = hab.sk_habitat
        GROUP BY 
            h.sk_habitat, 
            h.nome_habitat
        ORDER BY 
            h.nome_habitat;
    """,
}


# =============================================================================
# FLUXO DE EXECUÇÃO
# =============================================================================
def main():
    conexao = iniciar_conexao()
    
    try:
        # Cria as estruturas no banco
        rodar_script_sql(conexao, DIRETORIO_ATUAL / "sql" / "gold.sql")

        # Ordem lógica de atualização
        ordem_das_tabelas = [
            "gold.taxa_vitorias_por_faixa_velocidade",
            "gold.taxa_vitorias_por_multiplicador",
            "gold.matriz_confronto",
            "gold.ranking_pokemon",
            "gold.taxa_vitorias_por_tipo",
            "gold.taxa_vitorias_por_habitat",
        ]
        
        # Esvazia as tabelas antes do reabastecimento
        with conexao.cursor() as cursor:
            tabelas_alvo = ", ".join(ordem_das_tabelas)
            cursor.execute(f"TRUNCATE TABLE {tabelas_alvo} RESTART IDENTITY;")
        conexao.commit()

        # Popular e registrar logs
        for nome_tabela in ordem_das_tabelas:
            query_materializacao = DICIONARIO_CARGAS[nome_tabela]
            
            with conexao.cursor() as cursor:
                # Remove logs antigos da mesma tabela
                cursor.execute("DELETE FROM gold.log_publicacao WHERE tabela = %s;", (nome_tabela,))
                
                # Executa inserção com o SELECT consolidado
                comando_insert = f"INSERT INTO {nome_tabela} {query_materializacao}"
                cursor.execute(comando_insert)
                
                # Conta as linhas carregadas
                cursor.execute(f"SELECT count(*) FROM {nome_tabela}")
                total_registros = cursor.fetchone()[0]
                
                # Grava auditoria
                cursor.execute(
                    "INSERT INTO gold.log_publicacao (tabela, qtd_linhas) VALUES (%s, %s);",
                    (nome_tabela, total_registros),
                )
                print(f"[publicar] Tabela {nome_tabela} -> {total_registros} registros inseridos")
            
            conexao.commit()

        # Leitura do resumo de auditoria
        print("\n--- Auditoria da Camada Gold ---")
        with conexao.cursor() as cursor:
            cursor.execute("SELECT tabela, qtd_linhas, carregado_em FROM gold.log_publicacao ORDER BY id_log;")
            for registro in cursor.fetchall():
                print(f"[log] Tabela: {registro[0]} | Linhas: {registro[1]} | Timestamp: {registro[2]}")
                
        print("\n[sistema] Publicação na Camada Gold finalizada com sucesso.")
        
    finally:
        conexao.close()


if __name__ == "__main__":
    main()