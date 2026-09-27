#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 Script de Extração: Fontes Externas -> Camada Bronze (MongoDB)
=============================================================================
 - Coleta dados da PokéAPI (REST/JSON)
 - Coleta arquivos pokemon.csv / combats.csv
 - Mantém cache local no diretório dados_brutos/ para evitar reconsultas
   (idempotência na execução).
=============================================================================
"""

import csv
import io
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from pymongo import MongoClient, UpdateOne


# =============================================================================
# CONSTANTES E CONFIGURAÇÕES DE AMBIENTE
# =============================================================================
DIRETORIO_RAIZ = Path(__file__).resolve().parent
PASTA_CACHE = DIRETORIO_RAIZ / "dados_brutos"

API_BASE_URL = "https://pokeapi.co/api/v2"
LINK_CSV_POKEMON = "https://raw.githubusercontent.com/cdiener/pokemon_app/master/pokemon.csv"
LINK_CSV_COMBATES = "https://raw.githubusercontent.com/cdiener/pokemon_app/master/combats.csv"

URI_CONEXAO_MONGO = os.getenv("MONGO_URI", "mongodb://localhost:27017")
NOME_BANCO_MONGO = "pokedex_bronze"

# Definição do escopo de dados:
IDS_DAS_ESPECIES = list(range(1, 722))
IDS_DOS_TIPOS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 10001, 10002]

PAUSA_ENTRE_REQUISICOES = 0.1


# =============================================================================
# FUNÇÕES UTILITÁRIAS GERAIS
# =============================================================================
def gerar_timestamp_iso():
    agora_utc = datetime.now(timezone.utc)
    return agora_utc.isoformat().replace("+00:00", "Z")


def criar_estrutura_pastas():
    lista_subpastas = ("pokemon", "especies", "tipos", "csv")
    for nome_pasta in lista_subpastas:
        (PASTA_CACHE / nome_pasta).mkdir(parents=True, exist_ok=True)


def buscar_conteudo_json(url_alvo, sessao_http):
    resposta = sessao_http.get(url_alvo, timeout=120)
    resposta.raise_for_status()
    return resposta.json()


def escrever_arquivo_json(caminho_arquivo, conteudo_dicionario):
    with open(caminho_arquivo, "w", encoding="utf-8") as arq_saida:
        json.dump(conteudo_dicionario, arq_saida, ensure_ascii=False)


def carregar_arquivo_json(caminho_arquivo):
    with open(caminho_arquivo, "r", encoding="utf-8") as arq_entrada:
        return json.load(arq_entrada)


def enviar_lote_para_mongo(colecao_alvo, lista_documentos):
    if not lista_documentos:
        return
        
    operacoes_bulk = []
    for doc in lista_documentos:
        comando = UpdateOne(
            {"_id": doc["_id"]}, 
            {"$set": doc}, 
            upsert=True
        )
        operacoes_bulk.append(comando)
        
    colecao_alvo.bulk_write(operacoes_bulk)


# =============================================================================
# MÓDULO DE EXTRAÇÃO: DADOS DA POKEAPI
# =============================================================================
def extrair_dados_api():
    cliente_bd = MongoClient(URI_CONEXAO_MONGO)
    banco_dados = cliente_bd[NOME_BANCO_MONGO]
    
    col_pokemon = banco_dados["pokemon"]
    col_especies = banco_dados["especies"]
    col_tipos = banco_dados["tipos"]

    sessao_requests = requests.Session()

    # --- 1. Carga de Espécies ---
    lote_docs = []
    for id_esp in IDS_DAS_ESPECIES:
        caminho_local = PASTA_CACHE / "especies" / f"{id_esp}.json"
        
        if caminho_local.exists():
            payload_json = carregar_arquivo_json(caminho_local)
        else:
            payload_json = buscar_conteudo_json(f"{API_BASE_URL}/pokemon-species/{id_esp}", sessao_requests)
            escrever_arquivo_json(caminho_local, payload_json)
            time.sleep(PAUSA_ENTRE_REQUISICOES)
            
        documento_final = dict(payload_json)
        documento_final["_id"] = f"especie/{id_esp}"
        documento_final["_fonte"] = "pokeapi"
        documento_final["_url"] = f"{API_BASE_URL}/pokemon-species/{id_esp}"
        documento_final["_ingerido_em"] = gerar_timestamp_iso()
        
        lote_docs.append(documento_final)
        
    enviar_lote_para_mongo(col_especies, lote_docs)
    lote_docs.clear()
    print(f"[extracao_api] total de especies coletadas: {len(IDS_DAS_ESPECIES)}")

    # --- 2. Carga de Pokémon (Base e Variedades) ---
    conjunto_ids_pkm = set()
    
    for id_esp in IDS_DAS_ESPECIES:
        dados_especie = carregar_arquivo_json(PASTA_CACHE / "especies" / f"{id_esp}.json")
        variedades = dados_especie.get("varieties", [])
        
        for var in variedades:
            link_pokemon = (var.get("pokemon") or {}).get("url", "")
            if link_pokemon:
                try:
                    id_recuperado = int(link_pokemon.rstrip("/").split("/")[-1])
                    conjunto_ids_pkm.add(id_recuperado)
                except (ValueError, IndexError):
                    continue
                    
    lista_ids_ordenada = sorted(conjunto_ids_pkm)

    for id_pkm in lista_ids_ordenada:
        caminho_local = PASTA_CACHE / "pokemon" / f"{id_pkm}.json"
        
        if caminho_local.exists():
            payload_json = carregar_arquivo_json(caminho_local)
        else:
            payload_json = buscar_conteudo_json(f"{API_BASE_URL}/pokemon/{id_pkm}", sessao_requests)
            escrever_arquivo_json(caminho_local, payload_json)
            time.sleep(PAUSA_ENTRE_REQUISICOES)
            
        documento_final = dict(payload_json)
        documento_final["_id"] = f"pokemon/{id_pkm}"
        documento_final["_fonte"] = "pokeapi"
        documento_final["_url"] = f"{API_BASE_URL}/pokemon/{id_pkm}"
        documento_final["_ingerido_em"] = gerar_timestamp_iso()
        
        lote_docs.append(documento_final)
        
    enviar_lote_para_mongo(col_pokemon, lote_docs)
    lote_docs.clear()
    print(f"[extracao_api] total de pokemon coletados: {len(lista_ids_ordenada)}")

    # --- 3. Carga de Tipos ---
    for id_tipo in IDS_DOS_TIPOS:
        caminho_local = PASTA_CACHE / "tipos" / f"{id_tipo}.json"
        
        if caminho_local.exists():
            payload_json = carregar_arquivo_json(caminho_local)
        else:
            payload_json = buscar_conteudo_json(f"{API_BASE_URL}/type/{id_tipo}", sessao_requests)
            escrever_arquivo_json(caminho_local, payload_json)
            time.sleep(PAUSA_ENTRE_REQUISICOES)
            
        documento_final = dict(payload_json)
        documento_final["_id"] = f"tipo/{id_tipo}"
        documento_final["_fonte"] = "pokeapi"
        documento_final["_url"] = f"{API_BASE_URL}/type/{id_tipo}"
        documento_final["_ingerido_em"] = gerar_timestamp_iso()
        
        lote_docs.append(documento_final)
        
    enviar_lote_para_mongo(col_tipos, lote_docs)
    print(f"[extracao_api] total de tipos coletados: {len(IDS_DOS_TIPOS)}")

    cliente_bd.close()


# =============================================================================
# MÓDULO DE EXTRAÇÃO: DADOS CSV
# =============================================================================
def efetuar_download_csv(url_origem, nome_arq):
    resposta_http = requests.get(url_origem, timeout=300)
    resposta_http.raise_for_status()
    local_destino = PASTA_CACHE / "csv" / nome_arq
    local_destino.write_text(resposta_http.text, encoding="utf-8")
    return resposta_http.text


def decodificar_texto_csv(string_csv):
    buffer_memoria = io.StringIO(string_csv)
    return list(csv.DictReader(buffer_memoria))


def extrair_dados_csvs():
    cliente_bd = MongoClient(URI_CONEXAO_MONGO)
    banco_dados = cliente_bd[NOME_BANCO_MONGO]

    # --- pokemon.csv ---
    arquivo_pokemon = "pokemon.csv"
    caminho_pkm = PASTA_CACHE / "csv" / arquivo_pokemon
    
    if caminho_pkm.exists():
        texto_conteudo = caminho_pkm.read_text(encoding="utf-8")
    else:
        texto_conteudo = efetuar_download_csv(LINK_CSV_POKEMON, arquivo_pokemon)
        
    linhas_planilha = decodificar_texto_csv(texto_conteudo)

    colecao_pkm_csv = banco_dados["pokemon_csv"]
    cabecalho_base = list(linhas_planilha[0].keys()) if linhas_planilha else []
    lote_docs = []
    
    for indice_linha, registro in enumerate(linhas_planilha, start=1):
        doc_formatado = {chave.replace(".", "_"): valor for chave, valor in registro.items()}
        doc_formatado["_cabecalho_original"] = cabecalho_base
        doc_formatado["_id"] = f"pokemon_csv/{indice_linha}"
        doc_formatado["_fonte"] = "csv"
        doc_formatado["_url"] = LINK_CSV_POKEMON
        doc_formatado["_ingerido_em"] = gerar_timestamp_iso()
        
        lote_docs.append(doc_formatado)
        
    enviar_lote_para_mongo(colecao_pkm_csv, lote_docs)
    print(f"[extracao_csv] registros inseridos na pokemon_csv: {len(linhas_planilha)}")

    # --- combats.csv ---
    arquivo_combates = "combats.csv"
    caminho_cmb = PASTA_CACHE / "csv" / arquivo_combates
    
    if caminho_cmb.exists():
        texto_conteudo = caminho_cmb.read_text(encoding="utf-8")
    else:
        texto_conteudo = efetuar_download_csv(LINK_CSV_COMBATES, arquivo_combates)
        
    linhas_planilha = decodificar_texto_csv(texto_conteudo)

    colecao_cmb_csv = banco_dados["combates"]
    lote_docs = []
    
    for indice_linha, registro in enumerate(linhas_planilha, start=1):
        doc_formatado = dict(registro)
        doc_formatado["_id"] = f"combate/{indice_linha}"
        doc_formatado["_fonte"] = "csv"
        doc_formatado["_url"] = LINK_CSV_COMBATES
        doc_formatado["_ingerido_em"] = gerar_timestamp_iso()
        
        lote_docs.append(doc_formatado)
        
    enviar_lote_para_mongo(colecao_cmb_csv, lote_docs)
    print(f"[extracao_csv] registros inseridos na combates: {len(linhas_planilha)}")

    cliente_bd.close()


# =============================================================================
# FLUXO DE EXECUÇÃO
# =============================================================================
def main():
    criar_estrutura_pastas()
    extrair_dados_api()
    extrair_dados_csvs()
    print("[sistema] Pipeline de extração concluída com sucesso.")


if __name__ == "__main__":
    main()#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 Script de Extração: Fontes Externas -> Camada Bronze (MongoDB)
=============================================================================
 - Coleta dados da PokéAPI (REST/JSON)
 - Coleta arquivos pokemon.csv / combats.csv
 - Mantém cache local no diretório dados_brutos/ para evitar reconsultas
   (idempotência na execução).
=============================================================================
"""

import csv
import io
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from pymongo import MongoClient, UpdateOne


# =============================================================================
# CONSTANTES E CONFIGURAÇÕES DE AMBIENTE
# =============================================================================
DIRETORIO_RAIZ = Path(__file__).resolve().parent
PASTA_CACHE = DIRETORIO_RAIZ / "dados_brutos"

API_BASE_URL = "https://pokeapi.co/api/v2"
LINK_CSV_POKEMON = "https://raw.githubusercontent.com/cdiener/pokemon_app/master/pokemon.csv"
LINK_CSV_COMBATES = "https://raw.githubusercontent.com/cdiener/pokemon_app/master/combats.csv"

URI_CONEXAO_MONGO = os.getenv("MONGO_URI", "mongodb://localhost:27017")
NOME_BANCO_MONGO = "pokedex_bronze"

# Definição do escopo de dados:
IDS_DAS_ESPECIES = list(range(1, 722))
IDS_DOS_TIPOS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 10001, 10002]

PAUSA_ENTRE_REQUISICOES = 0.1


# =============================================================================
# FUNÇÕES UTILITÁRIAS GERAIS
# =============================================================================
def gerar_timestamp_iso():
    agora_utc = datetime.now(timezone.utc)
    return agora_utc.isoformat().replace("+00:00", "Z")


def criar_estrutura_pastas():
    lista_subpastas = ("pokemon", "especies", "tipos", "csv")
    for nome_pasta in lista_subpastas:
        (PASTA_CACHE / nome_pasta).mkdir(parents=True, exist_ok=True)


def buscar_conteudo_json(url_alvo, sessao_http):
    resposta = sessao_http.get(url_alvo, timeout=120)
    resposta.raise_for_status()
    return resposta.json()


def escrever_arquivo_json(caminho_arquivo, conteudo_dicionario):
    with open(caminho_arquivo, "w", encoding="utf-8") as arq_saida:
        json.dump(conteudo_dicionario, arq_saida, ensure_ascii=False)


def carregar_arquivo_json(caminho_arquivo):
    with open(caminho_arquivo, "r", encoding="utf-8") as arq_entrada:
        return json.load(arq_entrada)


def enviar_lote_para_mongo(colecao_alvo, lista_documentos):
    if not lista_documentos:
        return
        
    operacoes_bulk = []
    for doc in lista_documentos:
        comando = UpdateOne(
            {"_id": doc["_id"]}, 
            {"$set": doc}, 
            upsert=True
        )
        operacoes_bulk.append(comando)
        
    colecao_alvo.bulk_write(operacoes_bulk)


# =============================================================================
# MÓDULO DE EXTRAÇÃO: DADOS DA POKEAPI
# =============================================================================
def extrair_dados_api():
    cliente_bd = MongoClient(URI_CONEXAO_MONGO)
    banco_dados = cliente_bd[NOME_BANCO_MONGO]
    
    col_pokemon = banco_dados["pokemon"]
    col_especies = banco_dados["especies"]
    col_tipos = banco_dados["tipos"]

    sessao_requests = requests.Session()

    # --- 1. Carga de Espécies ---
    lote_docs = []
    for id_esp in IDS_DAS_ESPECIES:
        caminho_local = PASTA_CACHE / "especies" / f"{id_esp}.json"
        
        if caminho_local.exists():
            payload_json = carregar_arquivo_json(caminho_local)
        else:
            payload_json = buscar_conteudo_json(f"{API_BASE_URL}/pokemon-species/{id_esp}", sessao_requests)
            escrever_arquivo_json(caminho_local, payload_json)
            time.sleep(PAUSA_ENTRE_REQUISICOES)
            
        documento_final = dict(payload_json)
        documento_final["_id"] = f"especie/{id_esp}"
        documento_final["_fonte"] = "pokeapi"
        documento_final["_url"] = f"{API_BASE_URL}/pokemon-species/{id_esp}"
        documento_final["_ingerido_em"] = gerar_timestamp_iso()
        
        lote_docs.append(documento_final)
        
    enviar_lote_para_mongo(col_especies, lote_docs)
    lote_docs.clear()
    print(f"[extracao_api] total de especies coletadas: {len(IDS_DAS_ESPECIES)}")

    # --- 2. Carga de Pokémon (Base e Variedades) ---
    conjunto_ids_pkm = set()
    
    for id_esp in IDS_DAS_ESPECIES:
        dados_especie = carregar_arquivo_json(PASTA_CACHE / "especies" / f"{id_esp}.json")
        variedades = dados_especie.get("varieties", [])
        
        for var in variedades:
            link_pokemon = (var.get("pokemon") or {}).get("url", "")
            if link_pokemon:
                try:
                    id_recuperado = int(link_pokemon.rstrip("/").split("/")[-1])
                    conjunto_ids_pkm.add(id_recuperado)
                except (ValueError, IndexError):
                    continue
                    
    lista_ids_ordenada = sorted(conjunto_ids_pkm)

    for id_pkm in lista_ids_ordenada:
        caminho_local = PASTA_CACHE / "pokemon" / f"{id_pkm}.json"
        
        if caminho_local.exists():
            payload_json = carregar_arquivo_json(caminho_local)
        else:
            payload_json = buscar_conteudo_json(f"{API_BASE_URL}/pokemon/{id_pkm}", sessao_requests)
            escrever_arquivo_json(caminho_local, payload_json)
            time.sleep(PAUSA_ENTRE_REQUISICOES)
            
        documento_final = dict(payload_json)
        documento_final["_id"] = f"pokemon/{id_pkm}"
        documento_final["_fonte"] = "pokeapi"
        documento_final["_url"] = f"{API_BASE_URL}/pokemon/{id_pkm}"
        documento_final["_ingerido_em"] = gerar_timestamp_iso()
        
        lote_docs.append(documento_final)
        
    enviar_lote_para_mongo(col_pokemon, lote_docs)
    lote_docs.clear()
    print(f"[extracao_api] total de pokemon coletados: {len(lista_ids_ordenada)}")

    # --- 3. Carga de Tipos ---
    for id_tipo in IDS_DOS_TIPOS:
        caminho_local = PASTA_CACHE / "tipos" / f"{id_tipo}.json"
        
        if caminho_local.exists():
            payload_json = carregar_arquivo_json(caminho_local)
        else:
            payload_json = buscar_conteudo_json(f"{API_BASE_URL}/type/{id_tipo}", sessao_requests)
            escrever_arquivo_json(caminho_local, payload_json)
            time.sleep(PAUSA_ENTRE_REQUISICOES)
            
        documento_final = dict(payload_json)
        documento_final["_id"] = f"tipo/{id_tipo}"
        documento_final["_fonte"] = "pokeapi"
        documento_final["_url"] = f"{API_BASE_URL}/type/{id_tipo}"
        documento_final["_ingerido_em"] = gerar_timestamp_iso()
        
        lote_docs.append(documento_final)
        
    enviar_lote_para_mongo(col_tipos, lote_docs)
    print(f"[extracao_api] total de tipos coletados: {len(IDS_DOS_TIPOS)}")

    cliente_bd.close()


# =============================================================================
# MÓDULO DE EXTRAÇÃO: DADOS CSV
# =============================================================================
def efetuar_download_csv(url_origem, nome_arq):
    resposta_http = requests.get(url_origem, timeout=300)
    resposta_http.raise_for_status()
    local_destino = PASTA_CACHE / "csv" / nome_arq
    local_destino.write_text(resposta_http.text, encoding="utf-8")
    return resposta_http.text


def decodificar_texto_csv(string_csv):
    buffer_memoria = io.StringIO(string_csv)
    return list(csv.DictReader(buffer_memoria))


def extrair_dados_csvs():
    cliente_bd = MongoClient(URI_CONEXAO_MONGO)
    banco_dados = cliente_bd[NOME_BANCO_MONGO]

    # --- pokemon.csv ---
    arquivo_pokemon = "pokemon.csv"
    caminho_pkm = PASTA_CACHE / "csv" / arquivo_pokemon
    
    if caminho_pkm.exists():
        texto_conteudo = caminho_pkm.read_text(encoding="utf-8")
    else:
        texto_conteudo = efetuar_download_csv(LINK_CSV_POKEMON, arquivo_pokemon)
        
    linhas_planilha = decodificar_texto_csv(texto_conteudo)

    colecao_pkm_csv = banco_dados["pokemon_csv"]
    cabecalho_base = list(linhas_planilha[0].keys()) if linhas_planilha else []
    lote_docs = []
    
    for indice_linha, registro in enumerate(linhas_planilha, start=1):
        doc_formatado = {chave.replace(".", "_"): valor for chave, valor in registro.items()}
        doc_formatado["_cabecalho_original"] = cabecalho_base
        doc_formatado["_id"] = f"pokemon_csv/{indice_linha}"
        doc_formatado["_fonte"] = "csv"
        doc_formatado["_url"] = LINK_CSV_POKEMON
        doc_formatado["_ingerido_em"] = gerar_timestamp_iso()
        
        lote_docs.append(doc_formatado)
        
    enviar_lote_para_mongo(colecao_pkm_csv, lote_docs)
    print(f"[extracao_csv] registros inseridos na pokemon_csv: {len(linhas_planilha)}")

    # --- combats.csv ---
    arquivo_combates = "combats.csv"
    caminho_cmb = PASTA_CACHE / "csv" / arquivo_combates
    
    if caminho_cmb.exists():
        texto_conteudo = caminho_cmb.read_text(encoding="utf-8")
    else:
        texto_conteudo = efetuar_download_csv(LINK_CSV_COMBATES, arquivo_combates)
        
    linhas_planilha = decodificar_texto_csv(texto_conteudo)

    colecao_cmb_csv = banco_dados["combates"]
    lote_docs = []
    
    for indice_linha, registro in enumerate(linhas_planilha, start=1):
        doc_formatado = dict(registro)
        doc_formatado["_id"] = f"combate/{indice_linha}"
        doc_formatado["_fonte"] = "csv"
        doc_formatado["_url"] = LINK_CSV_COMBATES
        doc_formatado["_ingerido_em"] = gerar_timestamp_iso()
        
        lote_docs.append(doc_formatado)
        
    enviar_lote_para_mongo(colecao_cmb_csv, lote_docs)
    print(f"[extracao_csv] registros inseridos na combates: {len(linhas_planilha)}")

    cliente_bd.close()


# =============================================================================
# FLUXO DE EXECUÇÃO
# =============================================================================
def main():
    criar_estrutura_pastas()
    extrair_dados_api()
    extrair_dados_csvs()
    print("[sistema] Pipeline de extração concluída com sucesso.")


if __name__ == "__main__":
    main()