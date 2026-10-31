# Diversidade de gênero por subcampo de pesquisa

Dashboard interativo que mostra **quantas mulheres e quantos homens** pesquisam em cada **subcampo** do OpenAlex, a partir de uma base de pesquisadores credenciados em programas de pós-graduação em Ciência da Computação no Brasil.

O projeto cobre o caminho completo: **coleta** dos dados em APIs abertas → **inferência de gênero** → **visualização interativa**.

## Prévia

| Visão geral (todos os subcampos) | Um subcampo selecionado (exemplo: Artificial Intelligence) |
|---|---|
| ![Visão geral](docs/preview_geral.png) | ![Subcampo](docs/preview_subcampo.png) |

> As imagens são os gráficos gerados pelo próprio dashboard. No app, o menu lateral permite escolher o subcampo, e os cartões de totais se atualizam junto.

## O que o dashboard mostra

- **Visão geral:** rosca com todos os subcampos (nenhum é descartado). Ao passar o mouse sobre uma fatia aparecem o subcampo, o total de pesquisadores, o número de mulheres e o de homens.
- **Por subcampo:** proporção entre pesquisadoras e pesquisadores, com valor absoluto e percentual.
- **Cartões:** total de pesquisadores, de mulheres e de homens para a seleção atual.

### A base em números

| | |
|---|---|
| Pesquisadores com gênero identificado | 1460 |
| Mulheres | 300 (20,5%) |
| Homens | 1160 (79,5%) |
| Subcampos distintos | 95 (um deles é o marcador "Sem Sub-campo", 1 pesquisador sem classificação) |
| Campos distintos | 22 (inclui o marcador "Sem Campo") |

## Como os dados foram obtidos

```
planilha com IDs OpenAlex ──► scripts/coleta_openalex.py ──► scripts/genero_genderize.py ──► base final
        (author_id)             tópico, subcampo,              gênero provável a partir
                                campo e domínio                do primeiro nome
```

1. **Coleta (OpenAlex):** para cada pesquisador, `coleta_openalex.py` consulta a API do [OpenAlex](https://openalex.org) e guarda o **tópico principal** (o primeiro da lista, que vem ordenado pela pontuação) com o seu subcampo, campo e domínio.
2. **Gênero (Genderize):** `genero_genderize.py` usa a API [Genderize](https://genderize.io) para inferir o gênero provável a partir do **primeiro nome**, junto com uma probabilidade.
3. **Dashboard:** `app.py` agrupa os pesquisadores por subcampo e conta mulheres e homens.

## Como executar

Requer Python 3.9+.

```bash
git clone https://github.com/SEU_USUARIO/dashboard-genero-pesquisa.git
cd dashboard-genero-pesquisa

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python app.py
```

Abra **http://127.0.0.1:8050** no navegador.

### Refazer a coleta de dados (opcional)

Os dados já estão em `data/`, então isso só é preciso para gerar uma base nova.

```bash
export OPENALEX_EMAIL="voce@exemplo.com"      # opcional
export GENDERIZE_API_KEY="sua_chave"          # opcional (plano pago)

python scripts/coleta_openalex.py --entrada "author.xlsx" --coluna-id author_id
python scripts/genero_genderize.py
```

As chaves de API ficam em variáveis de ambiente e **nunca** no código. As planilhas geradas contêm nomes de pessoas e por isso estão no `.gitignore`.

## Estrutura do repositório

```
.
├── app.py                              # dashboard (Dash + Plotly)
├── data/
│   └── pesquisadores_anonimizado.csv   # Campo, Subcampo e Gênero (sem nomes nem IDs)
├── scripts/
│   ├── coleta_openalex.py              # etapa 1: tópicos no OpenAlex
│   └── genero_genderize.py             # etapa 2: gênero via Genderize
├── docs/                               # imagens do README
├── requirements.txt
└── README.md
```

## Publicar online (opcional)

O `app.py` já expõe `server = app.server`. Em serviços como o [Render](https://render.com), crie um *Web Service* a partir deste repositório com:

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn app:server`

Depois acrescente o link da demonstração no topo deste README.

## Limitações

- **O gênero é inferido, não declarado.** O Genderize usa só o primeiro nome e pode errar, principalmente em nomes unissex ou pouco comuns. Nomes que a API não reconhece (12 pesquisadores) ficam de fora das contagens.
- **O subcampo é do tópico principal.** Cada pessoa é classificada pelo primeiro tópico do OpenAlex, que é atribuído automaticamente a partir das publicações. Ele indica a área em que a pessoa mais publica, não o departamento onde trabalha.
- **Subcampos com poucos pesquisadores** geram percentuais instáveis (1 mulher em 2 pesquisadores já dá 50%). Por isso o dashboard mostra sempre o número absoluto junto com a proporção.
- **Duplicados:** três pesquisadores apareciam duas vezes na base original e foram contados uma só vez.
- Apenas gênero binário (feminino/masculino), porque é o que a API retorna.

## Tecnologias

Python · Dash · Plotly · Dash Bootstrap Components (tema Cyborg) · pandas · requests

## Fontes de dados

- [OpenAlex](https://openalex.org) — publicações, autores e classificação de tópicos
- [Genderize.io](https://genderize.io) — inferência de gênero a partir do primeiro nome
