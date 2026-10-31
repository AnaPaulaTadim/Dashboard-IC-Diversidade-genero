"""
Etapa 2 — Gênero com a API Genderize
====================================
Lê a planilha gerada pela etapa 1 (coleta_openalex.py) e acrescenta as colunas
`Gênero` e `Probabilidade`, inferidas a partir do primeiro nome de cada pesquisador.
"""
import argparse
import os
import time
from pathlib import Path
from unicodedata import normalize

import pandas as pd
import requests
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

GENDERIZE_URL = "https://api.genderize.io/"
GENDERIZE_API_KEY = os.environ.get("GENDERIZE_API_KEY")  
PAUSA = 0.05     
TIMEOUT = 30


def ajustar_largura_colunas(caminho_xlsx):
    """Ajusta a largura das colunas do Excel ao conteúdo."""
    wb = load_workbook(caminho_xlsx)
    ws = wb.active
    for coluna in ws.columns:
        maior = max((len(str(c.value)) for c in coluna if c.value is not None), default=0)
        ws.column_dimensions[get_column_letter(coluna[0].column)].width = maior + 2
    wb.save(caminho_xlsx)


def primeiro_nome(nome_completo):
    """Primeiro nome sem acentos e em minúsculas (é o que o Genderize recebe)."""
    if pd.isna(nome_completo) or not str(nome_completo).strip():
        return ""
    ascii_nome = normalize("NFKD", str(nome_completo)).encode("ASCII", "ignore").decode("utf-8")
    partes = ascii_nome.split()
    return partes[0].lower() if partes else ""


def consultar_genero(nome, tentativas=3):
    """Consulta o Genderize. Retorna (gênero, probabilidade).

    O gênero vem None quando o Genderize não conhece o nome; em caso de erro de
    rede ou de resposta inesperada retorna ("Desconhecido", 0).
    """
    params = {"name": nome}
    if GENDERIZE_API_KEY:
        params["apikey"] = GENDERIZE_API_KEY
    for tentativa in range(1, tentativas + 1):
        try:
            resp = requests.get(GENDERIZE_URL, params=params, timeout=TIMEOUT)
            if resp.status_code == 200:
                dados = resp.json()
                return dados.get("gender"), dados.get("probability", 0)
            if resp.status_code == 429:  # excesso de requisições: espera e tenta de novo
                time.sleep(2 * tentativa)
                continue
            print(f"Genderize respondeu {resp.status_code} para '{nome}'")
            break
        except requests.exceptions.RequestException as e:
            print(f"Erro com '{nome}' (tentativa {tentativa}): {e}")
            time.sleep(tentativa)
    return "Desconhecido", 0


def adicionar_genero(entrada, saida):
    df = pd.read_excel(entrada)
    df["_primeiro"] = df["Nome"].apply(primeiro_nome)

    unicos = sorted(n for n in df["_primeiro"].unique() if n)
    print(f"{len(df)} pesquisadores | {len(unicos)} primeiros nomes distintos a consultar")

    cache = {}
    for i, nome in enumerate(unicos, start=1):
        cache[nome] = consultar_genero(nome)
        if i % 100 == 0:
            print(f"  {i}/{len(unicos)} nomes consultados")
        time.sleep(PAUSA)

    padrao = ("Desconhecido", 0)
    df["Gênero"] = df["_primeiro"].map(lambda n: cache.get(n, padrao)[0])
    df["Probabilidade"] = df["_primeiro"].map(lambda n: cache.get(n, padrao)[1])
    df = df.drop(columns="_primeiro")

    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(saida, index=False)
    ajustar_largura_colunas(saida)

    print("\n--- Relatório ---")
    print(f"Requisições feitas: {len(unicos)}")
    print(df["Gênero"].value_counts(dropna=False).to_string())
    print("Arquivo salvo com sucesso!")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Adiciona gênero (Genderize) à planilha de tópicos.")
    ap.add_argument("--entrada", default="data/Topicos_Pesquisa_Autores.xlsx", help="planilha gerada pela etapa 1")
    ap.add_argument("--saida", default="data/Tópicos_de_Pesquisa_com_Genero.xlsx", help="planilha final com gênero")
    args = ap.parse_args()
    adicionar_genero(args.entrada, args.saida)
