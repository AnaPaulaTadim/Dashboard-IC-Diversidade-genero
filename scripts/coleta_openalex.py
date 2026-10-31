"""
Etapa 1 — Coleta no OpenAlex
============================
Lê uma planilha com os IDs OpenAlex dos pesquisadores e busca, para cada um, o
tópico principal (primeiro da lista, que vem ordenado pela pontuação), com o
subcampo, o campo e o domínio correspondentes
"""
import argparse
import os
import time
from pathlib import Path

import pandas as pd
import requests
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

OPENALEX_URL = "https://api.openalex.org/authors/{id}"
OPENALEX_EMAIL = os.environ.get("OPENALEX_EMAIL")  
PAUSA = 0.5      # segundos entre requisições, para não sobrecarregar a API
TIMEOUT = 30

COLUNAS = ["Nome", "ID (OpenAlex)", "Tópico Principal", "Dominio", "Campo", "Subcampo"]


def ajustar_largura_colunas(caminho_xlsx):
    """Ajusta a largura das colunas do Excel ao conteúdo."""
    wb = load_workbook(caminho_xlsx)
    ws = wb.active
    for coluna in ws.columns:
        maior = max((len(str(c.value)) for c in coluna if c.value is not None), default=0)
        ws.column_dimensions[get_column_letter(coluna[0].column)].width = maior + 2
    wb.save(caminho_xlsx)


def coletar_topicos(entrada, coluna_id, saida):
    # author_id = o pesquisador; (phd_supervisor_id seria o orientador, não usado aqui)
    df = pd.read_excel(entrada)
    ids = df[coluna_id]

    params = {"mailto": OPENALEX_EMAIL} if OPENALEX_EMAIL else {}
    registros = []
    nao_encontrados = sem_topico = 0

    print("Iniciando busca na OpenAlex. Isso pode levar alguns minutos...")
    for i, id_autor in enumerate(ids, start=1):
        try:
            resp = requests.get(OPENALEX_URL.format(id=id_autor), params=params, timeout=TIMEOUT)
            if resp.status_code != 200:
                nao_encontrados += 1
                print(f"ID {id_autor} não encontrado. Status: {resp.status_code}")
                continue

            dados = resp.json()
            topicos = dados.get("topics", [])
            if topicos:
                t = topicos[0]  # tópico de maior pontuação
                topico = t.get("display_name", "Sem Tópico")
                dominio = t.get("domain", {}).get("display_name", "Sem Domínio")
                campo = t.get("field", {}).get("display_name", "Sem Campo")
                subcampo = t.get("subfield", {}).get("display_name", "Sem Sub-campo")
            else:
                sem_topico += 1
                topico, dominio, campo, subcampo = "Sem Tópico", "Sem Domínio", "Sem Campo", "Sem Sub-campo"

            registros.append({
                "Nome": dados.get("display_name", "Nome Desconhecido"),
                "ID (OpenAlex)": id_autor,
                "Tópico Principal": topico,
                "Dominio": dominio,
                "Campo": campo,
                "Subcampo": subcampo,
            })
        except requests.exceptions.RequestException as e:
            nao_encontrados += 1
            print(f"Erro de requisição para o ID {id_autor}: {e}")
            continue

        if i % 50 == 0:
            print(f"  {i}/{len(ids)} processados")
        time.sleep(PAUSA)

    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(registros, columns=COLUNAS).to_excel(saida, index=False)
    ajustar_largura_colunas(saida)

    print("\n--- Relatório Final ---")
    print(" Arquivo Excel criado com sucesso!")
    print(f"Total de Pesquisadores Analisados: {len(ids)}")
    print(f"Pesquisadores não encontrados na OpenAlex: {nao_encontrados}")
    print(f"Pesquisadores encontrados sem tópicos: {sem_topico}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Coleta tópico/subcampo/campo/domínio no OpenAlex.")
    ap.add_argument("--entrada", required=True, help="planilha .xlsx com os IDs OpenAlex dos pesquisadores")
    ap.add_argument("--coluna-id", default="author_id", help="coluna com o ID do pesquisador (padrão: author_id)")
    ap.add_argument("--saida", default="data/Topicos_Pesquisa_Autores.xlsx", help="planilha de saída")
    args = ap.parse_args()
    coletar_topicos(args.entrada, args.coluna_id, args.saida)
