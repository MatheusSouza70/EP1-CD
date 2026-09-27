#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
 Pipeline de Carga: Camada Bronze (MongoDB) -> Camada Silver (PostgreSQL)
===============================================================================
 - Aplica o DDL versionado do arquivo sql/silver.sql
 - Executa a conciliação de chaves entre o CSV e a Pokédex via nome 
   (tratando formatos Mega, Primal, Forme, Size, Cloak, Mode, Therian, etc.)
 - Popula o modelo dimensional (star schema) garantindo idempotência
 - Gera auditoria (conciliacao.csv) e registra no banco (silver.log_conciliacao)
===============================================================================
"""

import csv
import io
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from pymongo import MongoClient


# =============================================================================
# CONFIGURAÇÕES E CONSTANTES GERAIS
# =============================================================================
DIRETORIO_BASE = Path(__file__).resolve().parent

URI_MONGODB = os.getenv("MONGO_URI", "mongodb://localhost:27017")
BANCO_MONGODB = "pokedex_bronze"

HOST_PG = os.getenv("PG_HOST", "localhost")
PORTA_PG = int(os.getenv("PG_PORT", "5432"))
BANCO_PG = os.getenv("PG_DB", "pokedex")
USUARIO_PG = os.getenv("PG_USER", "postgres")
SENHA_PG = os.getenv("PG_PASSWORD", "postgres")

MAPA_GERACOES = {
    1: ("Geração I", "Kanto"),
    2: ("Geração II", "Johto"),
    3: ("Geração III", "Hoenn"),
    4: ("Geração IV", "Sinnoh"),
    5: ("Geração V", "Unova"),
    6: ("Geração VI", "Kalos"),
}

# Palavras descartáveis que o CSV utiliza, mas a PokéAPI ignora
TERMOS_RUIDO = {"forme", "form", "mode", "cloak", "size", "style", "standard", "ordinary"}

# Exceções hardcoded onde a normalização padrão falha devido a inconsistências no CSV
REGRAS_EXCECAO = {
    "DeoxysAttack Forme": "deoxys-attack",
    "Kyurem Black Kyurem": "kyurem-black",
    "Kyurem White Kyurem": "kyurem-white",
    "Zygarde Half Forme": "zygarde-50",
    "Hoopa Confined": "hoopa",
}


# =============================================================================
# FUNÇÕES DE TRATAMENTO DE TEXTO E CONCILIAÇÃO
# =============================================================================
def criar_slug(texto_entrada):
    texto_formatado = unicodedata.normalize("NFKD", texto_entrada).encode("ascii", "ignore").decode("ascii")
    texto_formatado = texto_formatado.lower()
    texto_limpo = re.sub(r"[^a-z0-9]+", "-", texto_formatado).strip("-")
    return texto_limpo


def normalizar_nome(nome_cru):
    """
    Transforma um nome em uma chave canônica composta por tokens ordenados.
    Exemplo: 'Mega Charizard X' e 'charizard-mega-x' resultarão na mesma chave.
    """
    if not nome_cru:
        return ""
        
    texto = nome_cru.replace("♀", " f").replace("♂", " m")
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    texto = texto.lower()
    texto = texto.replace("'", "").replace(".", "")
    
    lista_tokens = [tok for tok in re.split(r"[^a-z0-9]+", texto) if tok and tok not in TERMOS_RUIDO]
    return "|".join(sorted(lista_tokens))


def gerar_indice_formas(formas_api, especies_por_forma):
    """
    Cria um dicionário mapeando a chave normalizada para os dados da forma correspondente.
    """
    dicionario_indice = {}
    
    for _, dados_forma in formas_api.items():
        chave_forma = normalizar_nome(dados_forma["name"])
        if chave_forma:
            dicionario_indice.setdefault(chave_forma, []).append(dados_forma)
            
        if dados_forma.get("is_default"):
            dados_especie = especies_por_forma.get(dados_forma["name"])
            if dados_especie and dados_especie.get("name"):
                chave_esp = normalizar_nome(dados_especie["name"])
                if chave_esp:
                    dicionario_indice.setdefault(chave_esp, []).append(dados_forma)
                    
    return dicionario_indice


def avaliar_correspondencia(nome_csv, dicionario_indice, slugs_api):
    """
    Retorna uma tupla (slug, formato, observacao) após cruzar o CSV com a API.
    """
    nome_limpo = (nome_csv or "").strip()
    
    if not nome_limpo:
        return None, "NAO_CONCILIADO_NOME_AUSENTE", "Nome ausente no CSV (linha 63) - membro especial"
        
    if nome_limpo in REGRAS_EXCECAO:
        slug_encontrado = REGRAS_EXCECAO[nome_limpo]
        if slug_encontrado in slugs_api:
            return slug_encontrado, "FORMA_ALTERNATIVA", "Exceção explícita: nome do CSV não normaliza genericamente para a PokéAPI."
        return None, "NAO_CONCILIADO", f"Exceção configurada ('{nome_limpo}') sem forma correspondente na PokéAPI."
        
    forma_identificada = dicionario_indice.get(normalizar_nome(nome_limpo))
    if forma_identificada:
        slug_encontrado = forma_identificada[0]["name"]
        tipo_formato = "EXATO" if slug_encontrado == criar_slug(nome_limpo) else "FORMA_ALTERNATIVA"
        return slug_encontrado, tipo_formato, ""
        
    return None, "NAO_CONCILIADO", "Forma sem correspondência na PokéAPI; atributos de espécie herdados por associação."


# =============================================================================
# COMUNICAÇÃO COM BANCOS DE DADOS
# =============================================================================
def extrair_dados_bronze():
    cliente = MongoClient(URI_MONGODB)
    banco = cliente[BANCO_MONGODB]
    colecoes = {
        "especies": list(banco["especies"].find()),
        "pokemon": list(banco["pokemon"].find()),
        "tipos": list(banco["tipos"].find()),
        "pokemon_csv": list(banco["pokemon_csv"].find()),
        "combates": list(banco["combates"].find()),
    }
    cliente.close()
    return colecoes


def ordenar_arquivos_csv(lista_documentos):
    def extrair_numero(doc):
        return int(doc["_id"].split("/")[-1])
    return sorted(lista_documentos, key=extrair_numero)


def iniciar_conexao_pg():
    return psycopg.connect(
        host=HOST_PG,
        port=PORTA_PG,
        dbname=BANCO_PG,
        user=USUARIO_PG,
        password=SENHA_PG,
    )


def rodar_script_sql(conexao, caminho_arquivo):
    conteudo_sql = caminho_arquivo.read_text(encoding="utf-8")
    try:
        with conexao.cursor() as cursor:
            cursor.execute(conteudo_sql)
    except psycopg.errors.ProgrammingError:
        with conexao.cursor() as cursor:
            comandos = [cmd.strip() for cmd in conteudo_sql.split(";") if cmd.strip()]
            for cmd in comandos:
                cursor.execute(cmd)


# =============================================================================
# FLUXO PRINCIPAL
# =============================================================================
def main():
    dados_bronze = extrair_dados_bronze()

    lista_especies = dados_bronze["especies"]
    lista_pokemon_api = dados_bronze["pokemon"]
    dicionario_tipos_api = {t["id"]: t for t in dados_bronze["tipos"]}
    lista_pokemon_csv = ordenar_arquivos_csv(dados_bronze["pokemon_csv"])
    lista_combates = ordenar_arquivos_csv(dados_bronze["combates"])

    # Estruturação de mapas baseados na PokéAPI
    mapa_formas_api = {p["name"]: p for p in lista_pokemon_api}
    
    mapa_especies_por_forma = {}
    for dados_especie in lista_especies:
        for variedade in dados_especie.get("varieties", []):
            nome_pokemon = (variedade.get("pokemon") or {}).get("name")
            if nome_pokemon:
                mapa_especies_por_forma[nome_pokemon] = dados_especie

    # Helpers locais (Sem dependências externas)
    def converter_geracao(str_geracao):
        correspondencia = re.match(r"^generation-([a-z]+)$", str_geracao or "")
        if not correspondencia:
            return None
        numeros_romanos = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6}
        return numeros_romanos.get(correspondencia.group(1))

    def sanitizar_inteiro(valor, padrao=None):
        try:
            return int(valor)
        except (TypeError, ValueError):
            return padrao

    def extrair_stats(dados_forma):
        dicionario_stats = {}
        for stat in dados_forma.get("stats", []) or []:
            dicionario_stats[stat["stat"]["name"]] = stat["base_stat"]
        return dicionario_stats

    def extrair_nomes_tipos(dados_forma):
        return [t["type"]["name"] for t in dados_forma.get("types", []) or []]

    def mapear_propriedades_especie(dados_especie):
        nome_habitat = (dados_especie.get("habitat") or {}).get("name")
        return {
            "geracao": converter_geracao((dados_especie.get("generation") or {}).get("name")),
            "habitat": nome_habitat, 
            "cor": (dados_especie.get("color") or {}).get("name") or "SEM_INFORMACAO",
            "forma_corporal": (dados_especie.get("shape") or {}).get("name") or "SEM_INFORMACAO",
            "taxa_crescimento": (dados_especie.get("growth_rate") or {}).get("name") or "SEM_INFORMACAO",
            "taxa_captura": dados_especie.get("capture_rate"),
            "felicidade_base": dados_especie.get("base_happiness"),
            "lendario": bool(dados_especie.get("is_legendary")),
            "mitico": bool(dados_especie.get("is_mythical")),
            "bebe": bool(dados_especie.get("is_baby")),
            "id_species": dados_especie.get("id"),
        }

    conexao = iniciar_conexao_pg()
    
    try:
        rodar_script_sql(conexao, DIRETORIO_BASE / "sql" / "silver.sql")
        
        # Limpa as tabelas respeitando a ordem reversa das Foreign Keys
        tabelas_para_truncar = [
            "silver.fato_confronto",
            "silver.efetividade_tipo",
            "silver.dim_pokemon",
            "silver.dim_tipo",
            "silver.dim_geracao",
            "silver.dim_habitat",
            "silver.dim_cor",
            "silver.dim_forma_corporal",
            "silver.dim_taxa_crescimento",
            "silver.log_conciliacao",
        ]
        
        with conexao.cursor() as cursor:
            for nome_tabela in tabelas_para_truncar:
                cursor.execute(f"TRUNCATE TABLE {nome_tabela} RESTART IDENTITY CASCADE;")
        conexao.commit()

        # Inserção nas Dimensões Base
        chaves_geracao = {}
        for num_geracao, (desc_geracao, regiao_geracao) in MAPA_GERACOES.items():
            with conexao.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO silver.dim_geracao (id_geracao, descricao_geracao, regiao) "
                    "VALUES (%s, %s, %s) RETURNING sk_geracao;",
                    (num_geracao, desc_geracao, regiao_geracao),
                )
                chaves_geracao[num_geracao] = cursor.fetchone()[0]
        conexao.commit()

        chaves_tipo = {}
        for id_tipo in range(1, 19):
            nome_do_tipo = dicionario_tipos_api[id_tipo]["name"]
            with conexao.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO silver.dim_tipo (id_tipo_api, nome_tipo, eh_valido_jogo) "
                    "VALUES (%s, %s, TRUE) RETURNING sk_tipo;",
                    (id_tipo, nome_do_tipo),
                )
                chaves_tipo[nome_do_tipo] = cursor.fetchone()[0]
                
        with conexao.cursor() as cursor:
            cursor.execute(
                "INSERT INTO silver.dim_tipo (id_tipo_api, nome_tipo, eh_valido_jogo, eh_membro_especial) "
                "VALUES (NULL, 'SEM_TIPO', FALSE, TRUE) RETURNING sk_tipo;"
            )
            chaves_tipo["SEM_TIPO"] = cursor.fetchone()[0]
        conexao.commit()

        # Popular dimensões auxiliares com valores padrão
        valores_habitat_padrao = [
            ("NAO_SE_APLICA", "conceito não se aplica ao jogo de origem"), 
            ("SEM_INFORMACAO", "sem informação na fonte")
        ]
        for habitat_nome, habitat_obs in valores_habitat_padrao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO silver.dim_habitat (nome_habitat, observacao) VALUES (%s, %s);",
                    (habitat_nome, habitat_obs),
                )
                
        tabelas_simples = [
            ("dim_cor", "nome_cor"),
            ("dim_forma_corporal", "nome_forma_corporal"),
            ("dim_taxa_crescimento", "nome_taxa_crescimento")
        ]
        for tabela, coluna in tabelas_simples:
            with conexao.cursor() as cursor:
                cursor.execute(f"INSERT INTO silver.{tabela} ({coluna}) VALUES (%s);", ("SEM_INFORMACAO",))
        conexao.commit()

        def injetar_dimensao_lazy(conn, nome_tabela, nome_coluna, nome_pk, valor_insercao):
            sufixo_tabela = nome_tabela.split(".")[-1]
            mapa_cache = _cache_dimensoes.get(sufixo_tabela)
            
            if mapa_cache is None:
                mapa_cache = {}
                with conn.cursor() as cur:
                    cur.execute(f"SELECT {nome_coluna}, {nome_pk} FROM {nome_tabela}")
                    mapa_cache.update(cur.fetchall())
                _cache_dimensoes[sufixo_tabela] = mapa_cache
                
            if valor_insercao not in mapa_cache:
                with conn.cursor() as cur:
                    cur.execute(f"INSERT INTO {nome_tabela} ({nome_coluna}) VALUES (%s) RETURNING {nome_pk};", (valor_insercao,))
                    mapa_cache[valor_insercao] = cur.fetchone()[0]
                conn.commit()
                
            return mapa_cache[valor_insercao]

        global _cache_dimensoes
        _cache_dimensoes = {}

        sk_hab_inaplicavel = injetar_dimensao_lazy(conexao, "silver.dim_habitat", "nome_habitat", "sk_habitat", "NAO_SE_APLICA")
        sk_hab_desconhecido = injetar_dimensao_lazy(conexao, "silver.dim_habitat", "nome_habitat", "sk_habitat", "SEM_INFORMACAO")

        # Processo de Conciliação
        conjunto_slugs_api = set(mapa_formas_api.keys())
        indice_geral = gerar_indice_formas(mapa_formas_api, mapa_especies_por_forma)

        registros_csv_limpos = []
        for documento in lista_pokemon_csv:
            id_do_csv = int(documento["_id"].split("/")[-1])
            registros_csv_limpos.append({
                "id_csv": id_do_csv,
                "name": (documento.get("Name") or "").strip(),
                "type1": (documento.get("Type 1") or "").strip(),
                "type2": (documento.get("Type 2") or "").strip(),
                "hp": sanitizar_inteiro(documento.get("HP")),
                "atk": sanitizar_inteiro(documento.get("Attack")),
                "def": sanitizar_inteiro(documento.get("Defense")),
                "spa": sanitizar_inteiro(documento.get("Sp_ Atk") or documento.get("Sp. Atk")),
                "spd": sanitizar_inteiro(documento.get("Sp_ Def") or documento.get("Sp. Def")),
                "spe": sanitizar_inteiro(documento.get("Speed")),
                "geracao": sanitizar_inteiro(documento.get("Generation")),
                "legend": (documento.get("Legendary") or "").strip().lower() == "true",
            })

        lista_conciliada = [] 
        mapa_csv_sk = {}
        linhas_para_dimensao = []
        slugs_ja_utilizados = set()

        for registro_csv in registros_csv_limpos:
            nome_bruto_csv = registro_csv["name"]
            
            if not nome_bruto_csv:
                slug_identificado = None
                obs_conciliacao = "Nome ausente no CSV (linha 63) - membro especial"
                tipo_formato = "NAO_CONCILIADO_NOME_AUSENTE"
            else:
                slug_identificado, tipo_formato, obs_conciliacao = avaliar_correspondencia(nome_bruto_csv, indice_geral, conjunto_slugs_api)

            if slug_identificado:
                dados_da_forma = mapa_formas_api[slug_identificado]
                slugs_ja_utilizados.add(slug_identificado)
                
                dados_da_especie = mapa_especies_por_forma.get(slug_identificado)
                numero_pokedex = dados_da_especie.get("id") if dados_da_especie else None
                atributos_especie = mapear_propriedades_especie(dados_da_especie) if dados_da_especie else {}
                
                eh_padrao = bool(dados_da_forma.get("is_default"))
                
                linha_montada = {
                    "id_csv": registro_csv["id_csv"],
                    "id_api": dados_da_forma["id"],
                    "numero": numero_pokedex,
                    "nome_original": nome_bruto_csv or dados_da_forma["name"],
                    "nome_api": dados_da_forma["name"],
                    "eh_forma_alternativa": not eh_padrao,
                    "eh_padrao": eh_padrao,
                    "altura": dados_da_forma.get("height"),
                    "peso": dados_da_forma.get("weight"),
                    "exp": dados_da_forma.get("base_experience"),
                    "stats": extrair_stats(dados_da_forma),
                    "type1": registro_csv["type1"],
                    "type2": registro_csv["type2"],
                    "geracao": registro_csv["geracao"],
                    "legend": registro_csv["legend"],
                    "attrs": atributos_especie,
                    "status_csv": True,
                }
            else:
                slug_base = None
                if nome_bruto_csv.startswith("Primal "):
                    slug_base = criar_slug(nome_bruto_csv[7:])
                elif nome_bruto_csv and nome_bruto_csv.startswith("Mega "):
                    fragmentos = nome_bruto_csv[5:].strip().split()
                    if fragmentos and fragmentos[-1] in ("X", "Y"):
                        slug_base = criar_slug(" ".join(fragmentos[:-1]))
                    else:
                        slug_base = criar_slug(nome_bruto_csv[5:])
                else:
                    slug_base = criar_slug(nome_bruto_csv)
                    
                forma_base = mapa_formas_api.get(slug_base) if slug_base else None
                dados_da_especie = mapa_especies_por_forma.get(slug_base) if forma_base else None
                atributos_especie = mapear_propriedades_especie(dados_da_especie) if dados_da_especie else {}
                
                nome_calculado = (slug_base if dados_da_especie else None) or (nome_bruto_csv if nome_bruto_csv.startswith(("Primal ", "Mega ")) else None)
                
                linha_montada = {
                    "id_csv": registro_csv["id_csv"],
                    "id_api": None,
                    "numero": dados_da_especie.get("id") if dados_da_especie else None,
                    "nome_original": nome_bruto_csv or "DESCONHECIDO",
                    "nome_api": nome_calculado,
                    "eh_forma_alternativa": True,
                    "eh_padrao": False,
                    "altura": forma_base.get("height") if forma_base else None,
                    "peso": forma_base.get("weight") if forma_base else None,
                    "exp": forma_base.get("base_experience") if forma_base else None,
                    "stats": extrair_stats(forma_base) if forma_base else {},
                    "type1": registro_csv["type1"],
                    "type2": registro_csv["type2"],
                    "geracao": registro_csv["geracao"],
                    "legend": registro_csv["legend"],
                    "attrs": atributos_especie,
                    "status_csv": True,
                }

            # Prioriza os stats advindos do CSV
            if registro_csv["hp"] is not None:
                linha_montada["stats"].update({
                    "hp": registro_csv["hp"], 
                    "attack": registro_csv["atk"], 
                    "defense": registro_csv["def"],
                    "special-attack": registro_csv["spa"], 
                    "special-defense": registro_csv["spd"], 
                    "speed": registro_csv["spe"],
                })
                
            num_final = linha_montada["numero"] if linha_montada["numero"] else registro_csv["geracao"]
            lista_conciliada.append((
                registro_csv["id_csv"], num_final, nome_bruto_csv, 
                linha_montada["nome_api"], tipo_formato, obs_conciliacao, bool(slug_identificado)
            ))
            linhas_para_dimensao.append(linha_montada)

        # Incorpora formas exclusivas da API
        for slug_restante, dados_da_forma in mapa_formas_api.items():
            if slug_restante in slugs_ja_utilizados:
                continue
                
            dados_da_especie = mapa_especies_por_forma.get(slug_restante)
            if not dados_da_especie:
                continue
                
            lista_tipos = extrair_nomes_tipos(dados_da_forma)
            
            linhas_para_dimensao.append({
                "id_csv": None,
                "id_api": dados_da_forma["id"],
                "numero": dados_da_especie["id"],
                "nome_original": dados_da_forma["name"],
                "nome_api": dados_da_forma["name"],
                "eh_forma_alternativa": not bool(dados_da_forma.get("is_default")),
                "eh_padrao": bool(dados_da_forma.get("is_default")),
                "altura": dados_da_forma.get("height"),
                "peso": dados_da_forma.get("weight"),
                "exp": dados_da_forma.get("base_experience"),
                "stats": extrair_stats(dados_da_forma),
                "type1": lista_tipos[0] if lista_tipos else "SEM_TIPO",
                "type2": lista_tipos[1] if len(lista_tipos) > 1 else "SEM_TIPO",
                "geracao": converter_geracao((dados_da_especie.get("generation") or {}).get("name")),
                "legend": None,
                "attrs": mapear_propriedades_especie(dados_da_especie),
                "status_csv": False,
            })

        # Inserção na Tabela dim_pokemon
        lote_insercao_dimensao = []
        for lin in linhas_para_dimensao:
            tipo_pri = lin["type1"].strip().lower() if lin["type1"] else "SEM_TIPO"
            tipo_sec = lin["type2"].strip().lower() if lin["type2"] else "SEM_TIPO"
            gen_base = lin["geracao"]
            
            sk_gen = chaves_geracao.get(gen_base) if gen_base in MAPA_GERACOES else None
            
            hab_base = lin["attrs"].get("habitat")
            if hab_base is None:
                sk_hab = sk_hab_desconhecido if (lin["status_csv"] and not lin["attrs"]) else sk_hab_inaplicavel
            else:
                sk_hab = injetar_dimensao_lazy(conexao, "silver.dim_habitat", "nome_habitat", "sk_habitat", hab_base)
                
            sk_cor = injetar_dimensao_lazy(conexao, "silver.dim_cor", "nome_cor", "sk_cor", lin["attrs"].get("cor", "SEM_INFORMACAO"))
            sk_forma = injetar_dimensao_lazy(conexao, "silver.dim_forma_corporal", "nome_forma_corporal", "sk_forma_corporal", lin["attrs"].get("forma_corporal", "SEM_INFORMACAO"))
            sk_taxa = injetar_dimensao_lazy(conexao, "silver.dim_taxa_crescimento", "nome_taxa_crescimento", "sk_taxa_crescimento", lin["attrs"].get("taxa_crescimento", "SEM_INFORMACAO"))
            
            flag_lendario, flag_mitico, flag_bebe = lin["attrs"].get("lendario"), lin["attrs"].get("mitico"), lin["attrs"].get("bebe")
            
            if flag_bebe:
                categoria_final = "BEBE"
            elif flag_mitico:
                categoria_final = "MITICO"
            elif flag_lendario:
                categoria_final = "LENDARIO"
            else:
                categoria_final = "COMUM"

            lote_insercao_dimensao.append((
                lin["numero"], lin["id_api"], lin["id_csv"], lin["nome_original"], lin["nome_api"],
                lin["eh_forma_alternativa"], lin["eh_padrao"], lin["numero"],
                lin["altura"], lin["peso"], lin["exp"],
                lin["stats"].get("hp"), lin["stats"].get("attack"), lin["stats"].get("defense"),
                lin["stats"].get("special-attack"), lin["stats"].get("special-defense"), lin["stats"].get("speed"),
                lin["attrs"].get("taxa_captura"), lin["attrs"].get("felicidade_base"),
                flag_lendario, flag_mitico, flag_bebe, categoria_final,
                sk_gen, sk_hab, sk_cor, sk_forma, sk_taxa, 
                chaves_tipo.get(tipo_pri, chaves_tipo["SEM_TIPO"]), 
                chaves_tipo.get(tipo_sec, chaves_tipo["SEM_TIPO"]),
            ))

        sql_dim_pokemon = """
            INSERT INTO silver.dim_pokemon (
                numero_pokedex, id_api, id_csv, nome_original, nome_api,
                eh_forma_alternativa, eh_padrao, pokemon_pai_pokedex,
                altura, peso, experiencia_base,
                hp_base, ataque_base, defesa_base, ataque_especial_base,
                defesa_especial_base, velocidade_base,
                taxa_captura, felicidade_base,
                eh_lendario, eh_mitico, eh_bebe, categoria_raridade,
                sk_geracao, sk_habitat, sk_cor, sk_forma_corporal,
                sk_taxa_crescimento, sk_tipo_primario, sk_tipo_secundario
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
        """
        
        with conexao.cursor() as cursor:
            cursor.executemany(sql_dim_pokemon, lote_insercao_dimensao)
        conexao.commit()

        # Cache temporário para resolução da tabela Fato
        with conexao.cursor() as cursor:
            cursor.execute("SELECT id_csv, sk_pokemon FROM silver.dim_pokemon WHERE id_csv IS NOT NULL")
            mapa_csv_sk.update(cursor.fetchall())
            
            cursor.execute("SELECT id_csv, velocidade_base FROM silver.dim_pokemon WHERE id_csv IS NOT NULL")
            mapa_velocidade_csv = dict(cursor.fetchall())

        # Inserção na Tabela efetividade_tipo
        lote_efetividade = []
        lista_tipos_validos = [dicionario_tipos_api[i]["name"] for i in range(1, 19)]
        
        for nome_atacante in lista_tipos_validos:
            idx_tipo = [i for i in range(1, 19) if dicionario_tipos_api[i]["name"] == nome_atacante][0]
            relacoes = dicionario_tipos_api[idx_tipo].get("damage_relations", {})
            
            conjunto_2x = {x["name"] for x in relacoes.get("double_damage_to", [])}
            conjunto_05x = {x["name"] for x in relacoes.get("half_damage_to", [])}
            conjunto_0x = {x["name"] for x in relacoes.get("no_damage_to", [])}
            
            for nome_defensor in lista_tipos_validos:
                multiplicador_calculado = 1.0
                if nome_defensor in conjunto_2x:
                    multiplicador_calculado = 2.0
                elif nome_defensor in conjunto_05x:
                    multiplicador_calculado = 0.5
                elif nome_defensor in conjunto_0x:
                    multiplicador_calculado = 0.0
                    
                lote_efetividade.append((chaves_tipo[nome_atacante], chaves_tipo[nome_defensor], multiplicador_calculado))
                
        with conexao.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO silver.efetividade_tipo (sk_tipo_atacante, sk_tipo_defensor, multiplicador) VALUES (%s,%s,%s);",
                lote_efetividade,
            )
        conexao.commit()

        # Inserção na Tabela Fato
        lote_fato = []
        for registro_combate in lista_combates:
            id_do_combate = int(registro_combate["_id"].split("/")[-1])
            pkmn_1 = int(registro_combate["First_pokemon"])
            pkmn_2 = int(registro_combate["Second_pokemon"])
            id_vencedor = int(registro_combate["Winner"])
            
            sk_pkmn_1 = mapa_csv_sk[pkmn_1]
            sk_pkmn_2 = mapa_csv_sk[pkmn_2]
            vel_1 = mapa_velocidade_csv.get(pkmn_1)
            vel_2 = mapa_velocidade_csv.get(pkmn_2)
            
            vit_1 = 1 if id_vencedor == pkmn_1 else 0
            vit_2 = 1 if id_vencedor == pkmn_2 else 0
            
            dif_1 = (vel_1 - vel_2) if (vel_1 and vel_2) else None
            dif_2 = (vel_2 - vel_1) if (vel_1 and vel_2) else None

            lote_fato.append((id_do_combate, 1, sk_pkmn_1, sk_pkmn_2, vit_1, 1, vel_1, vel_2, dif_1))
            lote_fato.append((id_do_combate, 2, sk_pkmn_2, sk_pkmn_1, vit_2, 0, vel_2, vel_1, dif_2))
            
        sql_fato_confronto = """
            INSERT INTO silver.fato_confronto
            (id_combate, lado, sk_pokemon, sk_oponente, venceu, atacou_primeiro, velocidade_combatente, velocidade_oponente, diff_velocidade)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);
        """
        
        for indice_bloco in range(0, len(lote_fato), 5000):
            with conexao.cursor() as cursor:
                cursor.executemany(sql_fato_confronto, lote_fato[indice_bloco : indice_bloco + 5000])
            conexao.commit()

        # Auditoria e Arquivo CSV
        titulos_csv = ["pokemon_id_csv", "numero_pokedex", "nome_csv", "nome_api", "formato", "observacao"]
        with open(DIRETORIO_BASE / "conciliacao.csv", "w", encoding="utf-8", newline="") as arquivo_saida:
            escritor_csv = csv.writer(arquivo_saida)
            escritor_csv.writerow(titulos_csv)
            escritor_csv.writerows([(item[0], item[1], item[2], item[3], item[4], item[5]) for item in lista_conciliada])
            
        sql_auditoria = """
            INSERT INTO silver.log_conciliacao 
            (pokemon_id_csv, numero_pokedex, nome_csv, nome_api, formato, observacao, conciliado) 
            VALUES (%s,%s,%s,%s,%s,%s,%s);
        """
        with conexao.cursor() as cursor:
            cursor.executemany(sql_auditoria, [(item[0], item[1], item[2], item[3], item[4], item[5], item[6]) for item in lista_conciliada])
        conexao.commit()

        # Resumo no Console
        with conexao.cursor() as cursor:
            for tb in ["dim_geracao", "dim_tipo", "dim_pokemon", "efetividade_tipo", "fato_confronto", "log_conciliacao"]:
                cursor.execute(f"SELECT count(*) FROM silver.{tb}")
                print(f"[Carga Realizada] silver.{tb}: {cursor.fetchone()[0]}")

        total_conciliado = sum(1 for item in lista_conciliada if item[6])
        print(f"[Status] Conciliação: {total_conciliado}/{len(lista_conciliada)} processados com sucesso")
        
        registros_falhos = [(item[2], item[4]) for item in lista_conciliada if not item[6]]
        if registros_falhos:
            print("[Atenção] Registros não conciliados:", registros_falhos)

        conexao.commit()
    finally:
        conexao.close()


if __name__ == "__main__":
    main()