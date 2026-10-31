"""
Dashboard interativo — Diversidade de gênero por subcampo de pesquisa
Dados: pesquisadores de programas de pós-graduação em Ciência da Computação (OpenAlex + Genderize).
"""
from pathlib import Path

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

# =====================================================================
# CARREGAMENTO E TRATAMENTO DE DADOS
# =====================================================================
# Base anonimizada (sem nomes nem IDs): colunas Campo, Subcampo e Gênero.
CAMINHO_DADOS = Path(__file__).parent / "data" / "pesquisadores_anonimizado.csv"
df = pd.read_csv(CAMINHO_DADOS)

df = df.dropna(subset=['Subcampo', 'Gênero'])
df = df[df['Gênero'].isin(['male', 'female'])]
df['Gênero'] = df['Gênero'].map({'male': 'Masculino', 'female': 'Feminino'})

subcampos_unicos = df['Subcampo'].unique().tolist()
subcampos_unicos.sort()
opcoes_dropdown = [{'label': 'Geral (Todos os Subcampos)', 'value': 'Todos'}] + [{'label': s, 'value': s} for s in subcampos_unicos]

CORES_GENERO = {"Feminino": "#FF3399", "Masculino": "#3399FF"}

# =====================================================================
# INICIALIZAÇÃO DA APLICAÇÃO
# =====================================================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
server = app.server  # necessário para publicar com gunicorn (Render, Railway etc.)

app.layout = dbc.Container([
    dbc.Row([
        # MENU LATERAL (Sidebar)
        dbc.Col([
            html.Div([
                html.H4("Filtros", style={"color": "#FFFFFF", "margin-bottom": "20px"}),
                html.Label("Selecione o Subcampo:", style={"color": "#AAAAAA"}),
                dcc.Dropdown(
                    id='subcampo-dropdown',
                    options=opcoes_dropdown,
                    value='Todos',
                    clearable=False,
                    style={"color": "#000000", "margin-top": "10px"}
                )
            ], style={"background-color": "#1E1E1E", "padding": "20px", "border-radius": "8px", "height": "100%"})
        ], md=3, style={"padding-top": "20px", "padding-bottom": "20px"}),

        # CONTEÚDO PRINCIPAL
        dbc.Col([
            html.Div([
                html.H2("Análise de Diversidade de Gênero na Pesquisa", style={"color": "#FFFFFF", "textAlign": "center"}),
            ], style={"background-color": "#1E1E1E", "padding": "20px", "border-radius": "8px", "margin-bottom": "20px", "margin-top": "20px"}),

            # Cards
            dbc.Row([
                dbc.Col([dbc.Card([dbc.CardBody([
                    html.Span("Total de Pesquisadores", className="card-text"),
                    html.H2(id="total-pesquisadores", style={"color": "#FFFFFF", "margin-top": "10px"}),
                ])], color="dark", outline=True, style={"box-shadow": "0 4px 4px 0 rgba(0,0,0,0.15)"})], md=4),

                dbc.Col([dbc.Card([dbc.CardBody([
                    html.Span("Pesquisadoras (Feminino)", className="card-text"),
                    html.H2(id="total-mulheres", style={"color": CORES_GENERO["Feminino"], "margin-top": "10px"}),
                ])], color="dark", outline=True, style={"box-shadow": "0 4px 4px 0 rgba(0,0,0,0.15)"})], md=4),

                dbc.Col([dbc.Card([dbc.CardBody([
                    html.Span("Pesquisadores (Masculino)", className="card-text"),
                    html.H2(id="total-homens", style={"color": CORES_GENERO["Masculino"], "margin-top": "10px"}),
                ])], color="dark", outline=True, style={"box-shadow": "0 4px 4px 0 rgba(0,0,0,0.15)"})], md=4),
            ], style={"margin-bottom": "20px"}),

            # Gráfico de Rosca
            html.Div([
                dcc.Graph(id="donut-chart", style={"height": "550px"})
            ], style={"background-color": "#242424", "padding": "15px", "border-radius": "8px"})

        ], md=9)
    ])
], fluid=True, style={"background-color": "#121212", "min-height": "100vh"})

# =====================================================================
# REATIVIDADE (Callbacks)
# =====================================================================
@app.callback(
    [Output("total-pesquisadores", "children"),
     Output("total-mulheres", "children"),
     Output("total-homens", "children"),
     Output("donut-chart", "figure")],
    [Input("subcampo-dropdown", "value")]
)
def update_dashboard(selected_subcampo):
    if selected_subcampo == 'Todos':
        df_grouped = df.groupby('Subcampo').agg(
            Total=('Gênero', 'count'),
            Mulheres=('Gênero', lambda x: (x == 'Feminino').sum()),
            Homens=('Gênero', lambda x: (x == 'Masculino').sum())
        ).reset_index()

        df_grouped['texto_hover'] = (
            "<b>Subcampo: " + df_grouped['Subcampo'] + "</b><br>" +
            "Total de Pesquisadores: " + df_grouped['Total'].astype(str) + "<br>" +
            "<span style='color:#FFFFFF;'><b>Mulheres: " + df_grouped['Mulheres'].astype(str) + "</b></span><br>" +
            "<span style='color:#FFFFFF;'><b>Homens: " + df_grouped['Homens'].astype(str) + "</b></span>"
        )

        fig = px.pie(
            df_grouped,
            values='Total',
            names='Subcampo',
            hole=0.5
        )

        fig.update_traces(
            textinfo='none',
            customdata=df_grouped['texto_hover'],
            hovertemplate="%{customdata}<extra></extra>"
        )

        mostrar_legenda = False
        titulo_grafico = "Distribuição de Pesquisadores por Subcampo (Passe o mouse para ver detalhes)"

        total = df_grouped['Total'].sum()
        mulheres = df_grouped['Mulheres'].sum()
        homens = df_grouped['Homens'].sum()

    else:
        dff = df[df['Subcampo'] == selected_subcampo]
        df_grouped = dff.groupby('Gênero').size().reset_index(name='Contagem')

        fig = px.pie(
            df_grouped,
            values='Contagem',
            names='Gênero',
            hole=0.5,
            color='Gênero',
            color_discrete_map=CORES_GENERO
        )

        fig.update_traces(
            textposition='inside',
            textinfo='label+percent',
            hovertemplate="<b>%{label}</b><br>Total Absoluto: %{value}<br>Percentual no Subcampo: %{percent}<extra></extra>"
        )

        mostrar_legenda = True
        titulo_grafico = f"Proporção de Gênero - {selected_subcampo}"

        total = len(dff)
        mulheres = len(dff[dff['Gênero'] == 'Feminino'])
        homens = len(dff[dff['Gênero'] == 'Masculino'])

    fig.update_layout(
        title={"text": titulo_grafico, "x": 0.5, "xanchor": "center"},
        paper_bgcolor="#242424",
        plot_bgcolor="#242424",
        font_color="#FFFFFF",
        margin=dict(l=20, r=20, b=20, t=60),
        showlegend=mostrar_legenda,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )

    return total, mulheres, homens, fig


if __name__ == "__main__":
    app.run(debug=False)
