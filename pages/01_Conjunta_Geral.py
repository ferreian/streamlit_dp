from st_aggrid import GridOptionsBuilder
import streamlit as st
import pandas as pd
import io
from st_aggrid import AgGrid, GridOptionsBuilder
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import gaussian_kde

# =========================
# Header customizado do dashboard
# =========================
st.markdown(
    """
    <div style="
        background: linear-gradient(90deg, #0070C0 0%, #4a4e69 100%);
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.10);
        padding: 28px 24px 18px 24px;
        margin-bottom: 32px;
        display: flex;
        align-items: center;
    ">
        <div style="flex:1">
            <h1 style="margin-bottom: 0.2em; color: #fff; font-size: 2.2em; font-weight: 700;">
                Análise Conjunta da Produção e Componentes de Produção
            </h1>
            <h3 style="margin-top: 0; color: #e0e0e0; font-weight: 400; font-size: 1.2em;">
                Integra avaliação da produtividade total com variáveis agronômicas, permitindo identificar fatores que influenciam o desempenho dos híbridos em diferentes ambientes
            </h3>
        </div>
        <!-- Se quiser adicionar um logo, descomente a linha abaixo e coloque o caminho correto -->
        <!-- <img src=\"https://link-para-logo.png\" style=\"height:64px; margin-left:24px;\" /> -->
    </div>
    """,
    unsafe_allow_html=True
)

# Verifica se o DataFrame tratado está disponível no session_state
if "df_avTratamentoMilho" not in st.session_state:
    st.error("O DataFrame de tratamento de milho não foi carregado. Volte para a página inicial e carregue os dados.")
    st.stop()

# Usar o DataFrame tratado já pronto do session_state
df_avTratamentoMilho = st.session_state["df_avTratamentoMilho"]

filter_keys = [
    ("macroRegiaoMilho", "Macro Região", "macro"),
    ("conjuntaGeralMilhoSafrinha", "Conjunta Geral", "conjunta"),
    ("subConjuntaMilhoSafrinha", "Sub Conjunta", "subconjunta"),
    ("mrhMilho", "MRH", "mrh"),
    ("regional", "Regional", "regional"),
    ("siglaEstado", "Estado", "estado"),
    ("nomeCidade", "Cidade", "cidade"),
    ("nomeProdutor", "Produtor", "produtor"),
    ("nomeFazenda", "Fazenda", "fazenda"),
    ("nome", "Híbridos", "hibrido"),
    ("displayName", "DTC Responsável", "responsavel"),
]

# Inicializa seleções no session_state
for col, _, key in filter_keys:
    if f"sel_{key}" not in st.session_state:
        st.session_state[f"sel_{key}"] = []

# =========================
# Seleção de filtros
# =========================

with st.sidebar:
    df_filtrado = df_avTratamentoMilho.copy()
    for col, label, key in filter_keys:
        options = sorted(
            df_filtrado[col].dropna().unique(), key=lambda x: str(x))
        # Limpa seleções inválidas
        st.session_state[f"sel_{key}"] = [
            v for v in st.session_state[f"sel_{key}"] if v in options]
        selecionadas = []
        with st.expander(label, expanded=False):
            for opt in options:
                checked = opt in st.session_state[f"sel_{key}"]
                if st.checkbox(opt, value=checked, key=f"{key}_{opt}"):
                    selecionadas.append(opt)
        st.session_state[f"sel_{key}"] = selecionadas
        if selecionadas:
            df_filtrado = df_filtrado[df_filtrado[col].isin(selecionadas)]

# =========================
# Criação do DataFrame principal de análise
# =========================
# O DataFrame df_analise_conjunta será a base para todas as análises e visualizações

df_analise_conjunta = df_filtrado.copy()

# Desfragmenta o DataFrame para evitar PerformanceWarning
df_analise_conjunta = df_analise_conjunta.copy()

# Mapeamento de colunas para visualização customizada
colunas_renomeadas = [
    ("indexTratamento", "index"),
    ("nome", "Híbrido"),
    ("humidade", "Umd (%)"),
    ("prod_kg_ha_corr", "Prod@13.5% (kg/ha)"),
    ("prod_sc_ha_corr", "Prod@13.5% (sc/ha)"),
    ("numPlantas_ha", "Pop (plantas/ha)"),
    ("media_AIE_m", "AIE (m)"),
    ("media_ALT_m", "ALT (m)"),
    ("media_umd_PMG", "PMG Umd (%)"),
    ("corr_PMG", "PMG@13.5% (g)"),
    ("media_NumFileiras", "Num Fileiras"),
    ("media_NumGraosPorFileira", "Num Grãos/Fileira"),
    ("graosArdidos", "Ardidos (%)"),
    ("perc_Total", "Perda Total (%)"),
    ("ciclo_dias", "Ciclo (dias)"),
    ("macroRegiaoMilho", "Macro Região"),
    ("conjuntaGeralMilhoSafrinha", "Conjunta Geral"),
    ("subConjuntaMilhoSafrinha", "Sub Conjunta"),
    ("mrhMilho", "MRH"),
    ("regional", "Regional"),
    ("siglaEstado", "UF"),
    ("estado", "Estado"),
    ("nomeCidade", "Cidade"),
    ("nomeProdutor", "Produtor"),
    ("nomeFazenda", "Fazenda"),
    ("displayName", "DTC Responsável")
]

colunas = [c[0] for c in colunas_renomeadas]
novos_nomes = {c[0]: c[1] for c in colunas_renomeadas}

# Cria o DataFrame de visualização customizada a partir do df_analise_conjunta
colunas_existentes = [c for c in colunas if c in df_analise_conjunta.columns]
df_analise_conjunta_visualizacao = df_analise_conjunta[colunas_existentes].rename(
    columns=novos_nomes)

# Exibe o DataFrame filtrado original
titulo_expander = "Dados Originais - Análise Conjunta da Produção e Componentes de Produção"
with st.expander(titulo_expander, expanded=False):
    st.dataframe(df_filtrado, use_container_width=True)

    # Botão para exportar em Excel o DataFrame filtrado original
    buffer_filtro = io.BytesIO()
    df_filtrado.to_excel(buffer_filtro, index=False)  # type: ignore
    buffer_filtro.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel (dados originais - análise conjunta)",
        data=buffer_filtro,
        file_name="dados_originais_analise_conjunta.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =========================
# Configuração visual e funcional do AgGrid
# =========================

# Cria o construtor de opções do grid a partir do DataFrame customizado
# Permite configurar colunas, filtros, menus e estilos
gb = GridOptionsBuilder.from_dataframe(df_analise_conjunta_visualizacao)

# Configuração de casas decimais para colunas numéricas
colunas_formatar = {
    "Prod@13.5% (kg/ha)": 1,
    "Prod@13.5% (sc/ha)": 1,
    "Pop (plantas/ha)": 0,
    "AIE (m)": 2,
    "ALT (m)": 2,
    "PMG Umd (%)": 1,
    "PMG@13.5% (g)": 1,
    "Num Fileiras": 1,
    "Num Grãos/Fileira": 0,
    "Ardidos (%)": 1,
    "Perda Total (%)": 1,
    "Ciclo (dias)": 0
}

for col in df_analise_conjunta_visualizacao.columns:
    if col in colunas_formatar:
        casas = colunas_formatar[col]
        gb.configure_column(
            col,
            headerClass='ag-header-bold',
            menuTabs=['generalMenuTab', 'filterMenuTab', 'columnsMenuTab'],
            valueFormatter=f"value != null ? value.toFixed({casas}) : ''"
        )
    else:
        gb.configure_column(
            col,
            headerClass='ag-header-bold',
            menuTabs=['generalMenuTab', 'filterMenuTab', 'columnsMenuTab']
        )
# Configura opções padrão para todas as colunas
# (não editável, agrupável, filtrável, redimensionável, fonte 12px)
gb.configure_default_column(editable=False, groupable=True,
                            filter=True, resizable=True, cellStyle={'fontSize': '12px'})
# Ajusta a altura do cabeçalho
gb.configure_grid_options(headerHeight=30)
# Gera o dicionário final de opções do grid
grid_options = gb.build()

# =========================
# Estilização customizada do AgGrid
# =========================
custom_css = {
    # Estiliza o cabeçalho da tabela (header)
    ".ag-header-cell-label": {
        "font-weight": "bold",     # Deixa o texto do cabeçalho em negrito
        "font-size": "12px",       # Define o tamanho da fonte do cabeçalho
        "color": "black"           # Define a cor do texto do cabeçalho como preto
    },
    # Estiliza o conteúdo das células (dados)
    ".ag-cell": {
        "color": "black",          # Define a cor do texto das células como preto
        "font-size": "12px"        # Define o tamanho da fonte das células
    }
}

# =========================
# Exibição do DataFrame customizado com AgGrid (base: df_analise_conjunta)
# =========================
st.subheader("Produção e Componentes Produtivos")
st.markdown(
    """
    <div style="
        background-color: #e7f0fa;
        border-left: 6px solid #0070C0;
        padding: 12px 18px;
        margin-bottom: 12px;
        border-radius: 6px;
        font-size: 1.15em;
        color: #22223b;
        font-weight: 600;
    ">
        Resultados por Híbrido
    </div>
    """,
    unsafe_allow_html=True
)
AgGrid(
    df_analise_conjunta_visualizacao,   # DataFrame a ser exibido
    gridOptions=grid_options,           # Opções de configuração do grid
    enable_enterprise_modules=True,     # Libera recursos avançados do AgGrid
    fit_columns_on_grid_load=False,     # Não força ajuste automático das colunas
    theme="streamlit",                # Tema visual do grid
    height=500,                        # Altura da tabela em pixels
    reload_data=True,                  # Recarrega dados ao atualizar
    custom_css=custom_css              # Aplica o CSS customizado definido acima
)

# Botão para exportar em Excel o DataFrame customizado
buffer = io.BytesIO()
df_analise_conjunta_visualizacao.to_excel(buffer, index=False)  # type: ignore
buffer.seek(0)
st.download_button(
    label="⬇️ Baixar Excel (Produção e Componentes Produtivos)",
    data=buffer,
    file_name="producao_componentes.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# Agrupamento por fazendaRef e pares de indexTratamento
# =========================
# Cria coluna de agrupamento para pares (101,201), (102,202), ..., (121,221)


def agrupa_index(idx):
    pares = {
        201: 101, 202: 102, 203: 103, 204: 104, 205: 105, 206: 106, 207: 107,
        209: 109, 210: 110, 211: 111, 212: 112, 213: 113, 214: 114, 215: 115,
        216: 116, 217: 117, 218: 118, 220: 120, 221: 121, 219: 208
    }
    if idx in pares:
        return pares[idx]
    return idx


df_analise_conjunta['indexTratamentoAgrupado'] = df_analise_conjunta['indexTratamento'].apply(
    agrupa_index)

# Define as colunas de agrupamento e as colunas numéricas para média
group_cols = ['fazendaRef', 'indexTratamentoAgrupado']
colunas_numericas = df_analise_conjunta.select_dtypes(
    include='number').columns.tolist()
colunas_numericas = [c for c in colunas_numericas if c not in [
    'indexTratamento', 'indexTratamentoAgrupado']]

# Substitui zeros por NaN nas colunas numéricas antes do agrupamento
df_analise_conjunta[colunas_numericas] = df_analise_conjunta[colunas_numericas].replace(
    0, np.nan)

# Realiza o agrupamento e calcula a média das colunas numéricas
df_analise_conjunta_agrupado = (
    df_analise_conjunta
    .groupby(group_cols, as_index=False)[colunas_numericas]
    .mean()
)

# Recupera o nome do híbrido para cada (fazendaRef, indexTratamentoAgrupado)
df_nome = (
    df_analise_conjunta
    .groupby(['fazendaRef', 'indexTratamentoAgrupado'])['nome']
    .first()
    .reset_index()
)

# Junta o nome ao DataFrame agrupado
df_analise_conjunta_agrupado = pd.merge(
    df_analise_conjunta_agrupado,
    df_nome,
    on=['fazendaRef', 'indexTratamentoAgrupado'],
    how='left'
)

# =========================
# Seleção, reordenação e renomeação das colunas para visualização do agrupado
# =========================
colunas_agrupado_renomeadas = [
    ("indexTratamentoAgrupado", "index"),
    ("nome", "Híbrido"),
    ("humidade", "Umd (%)"),
    ("prod_kg_ha_corr", "Prod@13.5% (kg/ha)"),
    ("prod_sc_ha_corr", "Prod@13.5% (sc/ha)"),
    ("numPlantas_ha", "Pop (plantas/ha)"),
    ("media_AIE_m", "AIE (m)"),
    ("media_ALT_m", "ALT (m)"),
    ("media_umd_PMG", "PMG Umd (%)"),
    ("corr_PMG", "PMG@13.5% (g)"),
    ("media_NumFileiras", "Num Fileiras"),
    ("media_NumGraosPorFileira", "Num Grãos/Fileira"),
    ("graosArdidos", "Ardidos (%)"),
    ("perc_Total", "Perda Total (%)"),
    ("ciclo_dias", "Ciclo (dias)")
]
colunas_agrupado = [c[0] for c in colunas_agrupado_renomeadas]
novos_nomes_agrupado = {c[0]: c[1] for c in colunas_agrupado_renomeadas}
colunas_agrupado_existentes = [
    c for c in colunas_agrupado if c in df_analise_conjunta_agrupado.columns]
df_analise_conjunta_agrupado_visualizacao = df_analise_conjunta_agrupado[colunas_agrupado_existentes].rename(
    columns=novos_nomes_agrupado)  # type: ignore

# =========================
# Exibição do DataFrame agrupado customizado com AgGrid
# =========================
st.subheader("Dados Conjuntos por Híbrido - Produção e Componentes Produtivos")
st.markdown(
    """
    <div style="
        background-color: #e7f0fa;
        border-left: 6px solid #0070C0;
        padding: 12px 18px;
        margin-bottom: 12px;
        border-radius: 6px;
        font-size: 1.15em;
        color: #22223b;
        font-weight: 600;
    ">
        Resultados por Híbrido - Média das Parcelas
    </div>
    """,
    unsafe_allow_html=True
)
gb_agrupado = GridOptionsBuilder.from_dataframe(
    df_analise_conjunta_agrupado_visualizacao)

# Configuração de casas decimais para colunas numéricas do agrupado
colunas_formatar_agrupado = {
    "Prod@13.5% (kg/ha)": 1,
    "Prod@13.5% (sc/ha)": 1,
    "Pop (plantas/ha)": 0,
    "AIE (m)": 2,
    "ALT (m)": 2,
    "PMG Umd (%)": 1,
    "PMG@13.5% (g)": 1,
    "Num Fileiras": 1,
    "Num Grãos/Fileira": 0,
    "Ardidos (%)": 1,
    "Perda Total (%)": 1,
    "Ciclo (dias)": 0
}

for col in df_analise_conjunta_agrupado_visualizacao.columns:
    if col in colunas_formatar_agrupado:
        casas = colunas_formatar_agrupado[col]
        gb_agrupado.configure_column(
            col,
            headerClass='ag-header-bold',
            menuTabs=['generalMenuTab', 'filterMenuTab', 'columnsMenuTab'],
            valueFormatter=f"value != null ? value.toFixed({casas}) : ''"
        )
    else:
        gb_agrupado.configure_column(
            col,
            headerClass='ag-header-bold',
            menuTabs=['generalMenuTab', 'filterMenuTab', 'columnsMenuTab']
        )
# Configura opções padrão para todas as colunas
# (não editável, agrupável, filtrável, redimensionável, fonte 12px)
gb_agrupado.configure_default_column(editable=False, groupable=True,
                                     filter=True, resizable=True, cellStyle={'fontSize': '12px'})
# Ajusta a altura do cabeçalho
gb_agrupado.configure_grid_options(headerHeight=30)
grid_options_agrupado = gb_agrupado.build()

AgGrid(
    df_analise_conjunta_agrupado_visualizacao,
    gridOptions=grid_options_agrupado,
    enable_enterprise_modules=True,
    fit_columns_on_grid_load=False,
    theme="streamlit",
    height=500,
    reload_data=True,
    custom_css=custom_css
)

# Botão para exportar em Excel o DataFrame agrupado customizado
buffer_agrupado_vis = io.BytesIO()
df_analise_conjunta_agrupado_visualizacao.to_excel(
    buffer_agrupado_vis, index=False)  # type: ignore
buffer_agrupado_vis.seek(0)
st.download_button(
    label="⬇️ Baixar Excel (Resumo da Conjunta de Produção)",
    data=buffer_agrupado_vis,
    file_name="conjunta_producao.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# Resumo por Híbrido (nome) - após agrupado
# =========================
st.markdown(
    """
    <div style="background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 12px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;">
        Conjunta de Produção por Híbrido
    </div>
    """,
    unsafe_allow_html=True
)
# Seleciona colunas numéricas principais para o resumo
colunas_resumo = [
    'humidade', 'prod_kg_ha_corr', 'prod_sc_ha_corr', 'numPlantas_ha', 'media_AIE_m', 'media_ALT_m',
    'media_umd_PMG', 'corr_PMG', 'media_NumFileiras', 'media_NumGraosPorFileira',
    'graosArdidos', 'perc_Total', 'ciclo_dias'
]
colunas_resumo_existentes = [
    c for c in colunas_resumo if c in df_analise_conjunta.columns]
df_resumo_hibrido = df_analise_conjunta.groupby(
    'nome')[colunas_resumo_existentes].mean().reset_index()
# Renomeia colunas para visualização
renomear_resumo = {
    'nome': 'Híbrido',
    'humidade': 'Umd (%)',
    'prod_kg_ha_corr': 'Prod@13.5% (kg/ha)',
    'prod_sc_ha_corr': 'Prod@13.5% (sc/ha)',
    'numPlantas_ha': 'Pop (plantas/ha)',
    'media_AIE_m': 'AIE (m)',
    'media_ALT_m': 'ALT (m)',
    'media_umd_PMG': 'PMG Umd (%)',
    'corr_PMG': 'PMG@13.5% (g)',
    'media_NumFileiras': 'Num Fileiras',
    'media_NumGraosPorFileira': 'Num Grãos/Fileira',
    'graosArdidos': 'Ardidos (%)',
    'perc_Total': 'Perda Total (%)',
    'ciclo_dias': 'Ciclo (dias)'
}
df_resumo_hibrido = df_resumo_hibrido.rename(columns=renomear_resumo)
# Configura AgGrid
_gb_resumo_hibrido = GridOptionsBuilder.from_dataframe(df_resumo_hibrido)
colunas_formatar_resumo = {
    'Prod@13.5% (kg/ha)': 1,
    'Prod@13.5% (sc/ha)': 1,
    'Pop (plantas/ha)': 0,
    'Umd (%)': 1,
    'AIE (m)': 2,
    'ALT (m)': 2,
    'PMG Umd (%)': 1,
    'PMG@13.5% (g)': 1,
    'Num Fileiras': 1,
    'Num Grãos/Fileira': 0,
    'Ardidos (%)': 1,
    'Perda Total (%)': 1,
    'Ciclo (dias)': 0
}
for col in df_resumo_hibrido.columns:
    if col in colunas_formatar_resumo:
        casas = colunas_formatar_resumo[col]
        _gb_resumo_hibrido.configure_column(
            col, valueFormatter=f"value != null ? value.toFixed({casas}) : ''", headerClass='ag-header-bold')
_gb_resumo_hibrido.configure_default_column(
    editable=False, groupable=True, filter=True, resizable=True, cellStyle={'fontSize': '12px'})
_gb_resumo_hibrido.configure_grid_options(headerHeight=30)
_grid_options_resumo_hibrido = _gb_resumo_hibrido.build()
AgGrid(
    df_resumo_hibrido,
    gridOptions=_grid_options_resumo_hibrido,
    enable_enterprise_modules=True,
    fit_columns_on_grid_load=False,
    theme="streamlit",
    height=500,
    reload_data=True,
    custom_css=custom_css
)

# Botão para exportar em Excel o DataFrame de resumo por híbrido
buffer_resumo_hibrido = io.BytesIO()
df_resumo_hibrido.to_excel(buffer_resumo_hibrido,
                           index=False, engine='xlsxwriter')  # type: ignore
buffer_resumo_hibrido.seek(0)
st.download_button(
    label="⬇️ Baixar Excel (Resumo por Híbrido)",
    data=buffer_resumo_hibrido,
    file_name="resumo_por_hibrido.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# Estatísticas descritivas para variáveis selecionadas (FIM DA PÁGINA)
# =========================
variaveis = [
    'prod_kg_ha_corr',
    'prod_sc_ha_corr',
    'numPlantas_ha',
    'media_AIE_m',
    'media_ALT_m',
    'corr_PMG',
    'media_NumFileiras',
    'media_NumGraosPorFileira',
    'graosArdidos',
    'perc_Total'
]

estatisticas_dict = {}
for col_var in variaveis:
    serie = df_analise_conjunta_agrupado[col_var].dropna()
    estatisticas_dict[col_var] = {
        'Total de observações': serie.count(),
        'Média': serie.mean(),
        'Erro Padrão': serie.sem(),
        'Desvio Padrão': serie.std(),
        'Mínimo': serie.min(),
        '1º Quartil (25%)': serie.quantile(0.25),
        'Mediana': serie.median(),
        '3º Quartil (75%)': serie.quantile(0.75),
        'Máximo': serie.max(),
        'CV (%)': 100 * serie.std() / serie.mean() if serie.mean() != 0 else float('nan'),
        # LSD simplificado: 1.96 * erro padrão (aproximação para 95% de confiança)
        'LSD': 1.96 * serie.sem() if serie.count() > 1 else float('nan'),
        'Locais': df_analise_conjunta_agrupado['fazendaRef'].nunique()
    }

estatisticas_df = pd.DataFrame(estatisticas_dict)


# Exibição do DataFrame de estatísticas com AgGrid
st.subheader("Estatísticas Descritivas - Produção e Componentes Produtivos")
st.markdown(
    """
    <div style="
        background-color: #e7f0fa;
        border-left: 6px solid #0070C0;
        padding: 12px 18px;
        margin-bottom: 12px;
        border-radius: 6px;
        font-size: 1.15em;
        color: #22223b;
        font-weight: 600;
    ">
        Análise Conjunta da Produção e Componentes de Produção
    </div>
    """,
    unsafe_allow_html=True
)
estatisticas_aggrid = estatisticas_df.reset_index().rename(columns={
    'index': 'Medida'})

# Renomear as colunas conforme solicitado
colunas_renomeadas_aggrid = {
    'prod_kg_ha_corr': 'Prod@13.5% (kg/ha)',
    'prod_sc_ha_corr': 'Prod@13.5% (sc/ha)',
    'numPlantas_ha': 'Pop (plantas/ha)',
    'media_AIE_m': 'AIE (m)',
    'media_ALT_m': 'ALT (m)',
    'corr_PMG': 'PMG@13.5% (g)',
    'media_NumFileiras': 'Num Fileiras',
    'media_NumGraosPorFileira': 'Num Grãos/Fileira',
    'graosArdidos': 'Ardidos (%)',
    'perc_Total': 'Perda Total (%)'
}
estatisticas_aggrid = estatisticas_aggrid.rename(
    columns=colunas_renomeadas_aggrid)

gb_estatisticas = GridOptionsBuilder.from_dataframe(estatisticas_aggrid)

# Configuração de casas decimais para colunas numéricas das estatísticas
colunas_formatar_estatisticas = {
    'Prod@13.5% (kg/ha)': 1,
    'Prod@13.5% (sc/ha)': 1,
    'Pop (plantas/ha)': 0,
    'AIE (m)': 2,
    'ALT (m)': 2,
    'PMG@13.5% (g)': 1,
    'Num Fileiras': 1,
    'Num Grãos/Fileira': 0,
    'Ardidos (%)': 1,
    'Perda Total (%)': 1
}

for col in estatisticas_aggrid.columns:
    if col in colunas_formatar_estatisticas:
        casas = colunas_formatar_estatisticas[col]
        gb_estatisticas.configure_column(
            col,
            headerClass='ag-header-bold',
            menuTabs=['generalMenuTab', 'filterMenuTab', 'columnsMenuTab'],
            valueFormatter=f"value != null ? value.toFixed({casas}) : ''"
        )
    else:
        gb_estatisticas.configure_column(
            col,
            headerClass='ag-header-bold',
            menuTabs=['generalMenuTab', 'filterMenuTab', 'columnsMenuTab']
        )
# Configura opções padrão para todas as colunas
# (não editável, agrupável, filtrável, redimensionável, fonte 12px)
gb_estatisticas.configure_default_column(editable=False, groupable=True,
                                         filter=True, resizable=True, cellStyle={'fontSize': '12px'})
gb_estatisticas.configure_grid_options(headerHeight=30)
grid_options_estatisticas = gb_estatisticas.build()

AgGrid(
    estatisticas_aggrid,
    gridOptions=grid_options_estatisticas,
    enable_enterprise_modules=True,
    fit_columns_on_grid_load=False,
    theme="streamlit",
    height=405,
    reload_data=True,
    custom_css=custom_css
)

# Botão para exportar o DataFrame de estatísticas (AgGrid) para Excel
buffer_estatisticas_aggrid = io.BytesIO()
estatisticas_aggrid.to_excel(
    buffer_estatisticas_aggrid, index=False)  # type: ignore
buffer_estatisticas_aggrid.seek(0)
st.download_button(
    label="⬇️ Baixar Excel (Estatísticas - análise conjunta)",
    data=buffer_estatisticas_aggrid,
    file_name="estatisticas_descritivas_analise_conjunta.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# Sessão de Gráficos - Card estilizado
# =========================
st.markdown(
    """
    <div style="
        background-color: #f5f7fa;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.10);
        padding: 32px 24px 24px 24px;
        margin-bottom: 32px;
        ">
        <h2 style="margin-bottom: 0.2em; color: #22223b; font-size: 18px;">Histogramas e Box Plot - Produção e Componentes Produtivos</h2>
        <h4 style="margin-top: 0; color: #4a4e69; font-weight: 400; font-size: 16px;">
            Visualize a distribuição dos dados de produção e componentes produtivos, identifique padrões, tendências, valores atípicos e compare a variabilidade entre diferentes híbridos.
        </h4>
    </div>
    """,
    unsafe_allow_html=True
)

# Expander para Prod@13.5% (kg/ha)
with st.expander('Histograma - Prod@13.5% (kg/ha)', expanded=True):
    dados = df_filtrado['prod_kg_ha_corr'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=dados,
        name='Prod@13.5% (kg/ha)',
        marker_color='#0070C0',  # mudar cor da barra
        opacity=0.5,
        xbins=dict(size=500)
    ))
    fig.add_vline(
        x=media,
        line_dash='dot',
        line_color='red',
        annotation_text=f"Média: {media:.1f}",
        annotation_position="top right",
        annotation_font_color='red',
        annotation_font_size=20
    )
    fig.update_layout(
        title='Distribuição da Prod@13.5% (kg/ha)',
        xaxis_title='Prod@13.5% (kg/ha)',
        yaxis_title='Frequência',
        bargap=0.05,
        plot_bgcolor='#f5f7fa',
        barmode='overlay',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        legend=dict(font=dict(size=14))
    )
    st.plotly_chart(fig, use_container_width=True)

# Expander para Prod@13.5% (sc/ha)
with st.expander('Histograma - Prod@13.5% (sc/ha)', expanded=False):
    dados = df_filtrado['prod_sc_ha_corr'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=dados,
        name='Prod@13.5% (sc/ha)',
        marker_color='#0070C0',  # mudar cor da barra
        opacity=0.5,
        xbins=dict(size=10)
    ))
    fig.add_vline(
        x=media,
        line_dash='dot',
        line_color='red',
        annotation_text=f"Média: {media:.1f}",
        annotation_position="top right",
        annotation_font_color='red',
        annotation_font_size=20
    )
    fig.update_layout(
        title='Distribuição da Prod@13.5% (sc/ha)',
        xaxis_title='Prod@13.5% (sc/ha)',
        yaxis_title='Frequência',
        bargap=0.05,
        plot_bgcolor='#f5f7fa',
        barmode='overlay',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        legend=dict(font=dict(size=14))
    )
    st.plotly_chart(fig, use_container_width=True)

# Expander para Pop (plantas/ha)
with st.expander('Histograma - Pop (plantas/ha)', expanded=False):
    dados = df_filtrado['numPlantas_ha'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=dados,
        name='Pop (plantas/ha)',
        marker_color='#0070C0',  # mudar cor da barra
        opacity=0.5,
        xbins=dict(size=5000)
    ))
    fig.add_vline(
        x=media,
        line_dash='dot',
        line_color='red',
        annotation_text=f"Média: {media:.1f}",
        annotation_position="top right",
        annotation_font_color='red',
        annotation_font_size=20
    )
    fig.update_layout(
        title='Distribuição da Pop (plantas/ha)',
        xaxis_title='Pop (plantas/ha)',
        yaxis_title='Frequência',
        bargap=0.05,
        plot_bgcolor='#f5f7fa',
        barmode='overlay',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        legend=dict(font=dict(size=14))
    )
    st.plotly_chart(fig, use_container_width=True)

# Expander para AIE (m)
with st.expander('Histograma - AIE (m)', expanded=False):
    dados = df_filtrado['media_AIE_m'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=dados,
        name='AIE (m)',
        marker_color='#0070C0',  # mudar cor da barra
        opacity=0.5,
        xbins=dict(size=0.1)
    ))
    fig.add_vline(
        x=media,
        line_dash='dot',
        line_color='red',
        annotation_text=f"Média: {media:.2f}",
        annotation_position="top right",
        annotation_font_color='red',
        annotation_font_size=20
    )
    fig.update_layout(
        title='Distribuição da AIE (m)',
        xaxis_title='AIE (m)',
        yaxis_title='Frequência',
        bargap=0.05,
        plot_bgcolor='#f5f7fa',
        barmode='overlay',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        legend=dict(font=dict(size=14))
    )
    st.plotly_chart(fig, use_container_width=True)

# Expander para ALT (m)
with st.expander('Histograma - ALT (m)', expanded=False):
    dados = df_filtrado['media_ALT_m'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=dados,
        name='ALT (m)',
        marker_color='#0070C0',  # mudar cor da barra
        opacity=0.5,
        xbins=dict(size=0.5)
    ))
    fig.add_vline(
        x=media,
        line_dash='dot',
        line_color='red',
        annotation_text=f"Média: {media:.2f}",
        annotation_position="top right",
        annotation_font_color='red',
        annotation_font_size=20
    )
    fig.update_layout(
        title='Distribuição da ALT (m)',
        xaxis_title='ALT (m)',
        yaxis_title='Frequência',
        bargap=0.05,
        plot_bgcolor='#f5f7fa',
        barmode='overlay',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        legend=dict(font=dict(size=14))
    )
    st.plotly_chart(fig, use_container_width=True)

# Expander para PMG@13.5% (g)
with st.expander('Histograma - PMG@13.5% (g)', expanded=False):
    dados = df_filtrado['corr_PMG'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=dados,
        name='PMG@13.5% (g)',
        marker_color='#0070C0',  # mudar cor da barra
        opacity=0.5,
        xbins=dict(size=100)
    ))
    fig.add_vline(
        x=media,
        line_dash='dot',
        line_color='red',
        annotation_text=f"Média: {media:.2f}",
        annotation_position="top right",
        annotation_font_color='red',
        annotation_font_size=20
    )
    fig.update_layout(
        title='Distribuição da PMG@13.5% (g)',
        xaxis_title='PMG@13.5% (g)',
        yaxis_title='Frequência',
        bargap=0.05,
        plot_bgcolor='#f5f7fa',
        barmode='overlay',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        legend=dict(font=dict(size=14))
    )
    st.plotly_chart(fig, use_container_width=True)

# Expander para Num Fileiras
with st.expander('Histograma - Num Fileiras', expanded=False):
    dados = df_filtrado['media_NumFileiras'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=dados,
        name='Num Fileiras',
        marker_color='#0070C0',  # mudar cor da barra
        opacity=0.5,
        xbins=dict(size=2)
    ))
    fig.add_vline(
        x=media,
        line_dash='dot',
        line_color='red',
        annotation_text=f"Média: {media:.2f}",
        annotation_position="top right",
        annotation_font_color='red',
        annotation_font_size=20
    )
    fig.update_layout(
        title='Distribuição do Número de Fileiras',
        xaxis_title='Num Fileiras',
        yaxis_title='Frequência',
        bargap=0.05,
        plot_bgcolor='#f5f7fa',
        barmode='overlay',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        legend=dict(font=dict(size=14))
    )
    st.plotly_chart(fig, use_container_width=True)

# Expander para Num Grãos/Fileira
with st.expander('Histograma - Num Grãos/Fileira', expanded=False):
    dados = df_filtrado['media_NumGraosPorFileira'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=dados,
        name='Num Grãos/Fileira',
        marker_color='#0070C0',  # mudar cor da barra
        opacity=0.5,
        xbins=dict(size=10)
    ))
    fig.add_vline(
        x=media,
        line_dash='dot',
        line_color='red',
        annotation_text=f"Média: {media:.2f}",
        annotation_position="top right",
        annotation_font_color='red',
        annotation_font_size=20
    )
    fig.update_layout(
        title='Distribuição do Número de Grãos por Fileira',
        xaxis_title='Num Grãos/Fileira',
        yaxis_title='Frequência',
        bargap=0.05,
        plot_bgcolor='#f5f7fa',
        barmode='overlay',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        legend=dict(font=dict(size=14))
    )
    st.plotly_chart(fig, use_container_width=True)

# Expander para Ardidos (%)
with st.expander('Histograma - Ardidos (%)', expanded=False):
    dados = df_filtrado['graosArdidos'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=dados,
        name='Ardidos (%)',
        marker_color='#0070C0',  # mudar cor da barra
        opacity=0.5,
        xbins=dict(size=2)
    ))
    fig.add_vline(
        x=media,
        line_dash='dot',
        line_color='red',
        annotation_text=f"Média: {media:.2f}",
        annotation_position="top right",
        annotation_font_color='red',
        annotation_font_size=20
    )
    fig.update_layout(
        title='Distribuição de Ardidos (%)',
        xaxis_title='Ardidos (%)',
        yaxis_title='Frequência',
        bargap=0.05,
        plot_bgcolor='#f5f7fa',
        barmode='overlay',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        legend=dict(font=dict(size=14))
    )
    st.plotly_chart(fig, use_container_width=True)

# Expander para Perda Total (%)
with st.expander('Histograma - Perda Total (%)', expanded=False):
    dados = df_filtrado['perc_Total'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=dados,
        name='Perda Total (%)',
        marker_color='#0070C0',  # mudar cor da barra
        opacity=0.5,
        xbins=dict(size=10)
    ))
    fig.add_vline(
        x=media,
        line_dash='dot',
        line_color='red',
        annotation_text=f"Média: {media:.2f}",
        annotation_position="top right",
        annotation_font_color='red',
        annotation_font_size=20
    )
    fig.update_layout(
        title='Distribuição de Perda Total (%)',
        xaxis_title='Perda Total (%)',
        yaxis_title='Frequência',
        bargap=0.05,
        plot_bgcolor='#f5f7fa',
        barmode='overlay',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        legend=dict(font=dict(size=14))
    )
    st.plotly_chart(fig, use_container_width=True)

# Expander para Box Plot - Prod@13.5% (kg/ha)
with st.expander('Box Plot - Prod@13.5% (kg/ha)', expanded=False):
    dados = df_filtrado['prod_kg_ha_corr'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Box(
        x=dados,
        name='Prod@13.5% (kg/ha)',
        marker_color='#0070C0',
        boxmean=False,
        boxpoints='outliers',
        line=dict(color='#0070C0')
    ))
    # Adiciona a média como ponto vermelho
    fig.add_trace(go.Scatter(
        x=[media],
        y=['Prod@13.5% (kg/ha)'],
        mode='markers+text',
        marker=dict(color='red', size=14, symbol='diamond'),
        text=[f"Média: {media:.1f}"],
        textposition='top right',
        textfont=dict(color='red', size=16),
        showlegend=False
    ))
    fig.update_layout(
        title='Box Plot da Produção @13.5% (kg/ha)',
        xaxis_title='Prod@13.5% (kg/ha)',
        plot_bgcolor='#f5f7fa',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            tickfont=dict(size=16, color='black')
        ),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

# Expander para Box Plot - Prod@13.5% (sc/ha)
with st.expander('Box Plot - Prod@13.5% (sc/ha)', expanded=False):
    dados = df_filtrado['prod_sc_ha_corr'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Box(
        x=dados,
        name='Prod@13.5% (sc/ha)',
        marker_color='#0070C0',
        boxmean=False,
        boxpoints='outliers',
        line=dict(color='#0070C0')
    ))
    # Adiciona a média como ponto vermelho
    fig.add_trace(go.Scatter(
        x=[media],
        y=['Prod@13.5% (sc/ha)'],
        mode='markers+text',
        marker=dict(color='red', size=14, symbol='diamond'),
        text=[f"Média: {media:.1f}"],
        textposition='top right',
        textfont=dict(color='red', size=16),
        showlegend=False
    ))
    fig.update_layout(
        title='Box Plot da Produção @13.5% (sc/ha)',
        xaxis_title='Prod@13.5% (sc/ha)',
        plot_bgcolor='#f5f7fa',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            tickfont=dict(size=16, color='black')
        ),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

# Expander para Box Plot - Pop (plantas/ha)
with st.expander('Box Plot - Pop (plantas/ha)', expanded=False):
    dados = df_filtrado['numPlantas_ha'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Box(
        x=dados,
        name='Pop (plantas/ha)',
        marker_color='#0070C0',
        boxmean=False,
        boxpoints='outliers',
        line=dict(color='#0070C0')
    ))
    # Adiciona a média como ponto vermelho
    fig.add_trace(go.Scatter(
        x=[media],
        y=['Pop (plantas/ha)'],
        mode='markers+text',
        marker=dict(color='red', size=14, symbol='diamond'),
        text=[f"Média: {media:.1f}"],
        textposition='top right',
        textfont=dict(color='red', size=16),
        showlegend=False
    ))
    fig.update_layout(
        title='Box Plot da População de Plantas (plantas/ha)',
        xaxis_title='Pop (plantas/ha)',
        plot_bgcolor='#f5f7fa',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            tickfont=dict(size=16, color='black')
        ),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

# Expander para Box Plot - AIE (m)
with st.expander('Box Plot - AIE (m)', expanded=False):
    dados = df_filtrado['media_AIE_m'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Box(
        x=dados,
        name='AIE (m)',
        marker_color='#0070C0',
        boxmean=False,
        boxpoints='outliers',
        line=dict(color='#0070C0')
    ))
    # Adiciona a média como ponto vermelho
    fig.add_trace(go.Scatter(
        x=[media],
        y=['AIE (m)'],
        mode='markers+text',
        marker=dict(color='red', size=14, symbol='diamond'),
        text=[f"Média: {media:.2f}"],
        textposition='top right',
        textfont=dict(color='red', size=16),
        showlegend=False
    ))
    fig.update_layout(
        title='Box Plot do AIE (m)',
        xaxis_title='AIE (m)',
        plot_bgcolor='#f5f7fa',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            tickfont=dict(size=16, color='black')
        ),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

# Expander para Box Plot - ALT (m)
with st.expander('Box Plot - ALT (m)', expanded=False):
    dados = df_filtrado['media_ALT_m'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Box(
        x=dados,
        name='ALT (m)',
        marker_color='#0070C0',
        boxmean=False,
        boxpoints='outliers',
        line=dict(color='#0070C0')
    ))
    # Adiciona a média como ponto vermelho
    fig.add_trace(go.Scatter(
        x=[media],
        y=['ALT (m)'],
        mode='markers+text',
        marker=dict(color='red', size=14, symbol='diamond'),
        text=[f"Média: {media:.2f}"],
        textposition='top right',
        textfont=dict(color='red', size=16),
        showlegend=False
    ))
    fig.update_layout(
        title='Box Plot da ALT (m)',
        xaxis_title='ALT (m)',
        plot_bgcolor='#f5f7fa',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            tickfont=dict(size=16, color='black')
        ),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

# Expander para Box Plot - PMG@13.5% (g)
with st.expander('Box Plot - PMG@13.5% (g)', expanded=False):
    dados = df_filtrado['corr_PMG'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Box(
        x=dados,
        name='PMG@13.5% (g)',
        marker_color='#0070C0',
        boxmean=False,
        boxpoints='outliers',
        line=dict(color='#0070C0')
    ))
    # Adiciona a média como ponto vermelho
    fig.add_trace(go.Scatter(
        x=[media],
        y=['PMG@13.5% (g)'],
        mode='markers+text',
        marker=dict(color='red', size=14, symbol='diamond'),
        text=[f"Média: {media:.2f}"],
        textposition='top right',
        textfont=dict(color='red', size=16),
        showlegend=False
    ))
    fig.update_layout(
        title='Box Plot do PMG@13.5% (g)',
        xaxis_title='PMG@13.5% (g)',
        plot_bgcolor='#f5f7fa',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            tickfont=dict(size=16, color='black')
        ),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

# Expander para Box Plot - Num Fileiras
with st.expander('Box Plot - Num Fileiras', expanded=False):
    dados = df_filtrado['media_NumFileiras'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Box(
        x=dados,
        name='Num Fileiras',
        marker_color='#0070C0',
        boxmean=False,
        boxpoints='outliers',
        line=dict(color='#0070C0')
    ))
    # Adiciona a média como ponto vermelho
    fig.add_trace(go.Scatter(
        x=[media],
        y=['Num Fileiras'],
        mode='markers+text',
        marker=dict(color='red', size=14, symbol='diamond'),
        text=[f"Média: {media:.2f}"],
        textposition='top right',
        textfont=dict(color='red', size=16),
        showlegend=False
    ))
    fig.update_layout(
        title='Box Plot do Número de Fileiras',
        xaxis_title='Num Fileiras',
        plot_bgcolor='#f5f7fa',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            tickfont=dict(size=16, color='black')
        ),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

# Expander para Box Plot - Num Grãos/Fileira
with st.expander('Box Plot - Num Grãos/Fileira', expanded=False):
    dados = df_filtrado['media_NumGraosPorFileira'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Box(
        x=dados,
        name='Num Grãos/Fileira',
        marker_color='#0070C0',
        boxmean=False,
        boxpoints='outliers',
        line=dict(color='#0070C0')
    ))
    # Adiciona a média como ponto vermelho
    fig.add_trace(go.Scatter(
        x=[media],
        y=['Num Grãos/Fileira'],
        mode='markers+text',
        marker=dict(color='red', size=14, symbol='diamond'),
        text=[f"Média: {media:.2f}"],
        textposition='top right',
        textfont=dict(color='red', size=16),
        showlegend=False
    ))
    fig.update_layout(
        title='Box Plot do Número de Grãos por Fileira',
        xaxis_title='Num Grãos/Fileira',
        plot_bgcolor='#f5f7fa',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            tickfont=dict(size=16, color='black')
        ),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

# Expander para Box Plot - Perda Total (%)
with st.expander('Box Plot - Perda Total (%)', expanded=False):
    dados = df_filtrado['perc_Total'].dropna()
    media = dados.mean()
    fig = go.Figure()
    fig.add_trace(go.Box(
        x=dados,
        name='Perda Total (%)',
        marker_color='#0070C0',
        boxmean=False,
        boxpoints='outliers',
        line=dict(color='#0070C0')
    ))
    # Adiciona a média como ponto vermelho
    fig.add_trace(go.Scatter(
        x=[media],
        y=['Perda Total (%)'],
        mode='markers+text',
        marker=dict(color='red', size=14, symbol='diamond'),
        text=[f"Média: {media:.2f}"],
        textposition='top right',
        textfont=dict(color='red', size=16),
        showlegend=False
    ))
    fig.update_layout(
        title='Box Plot da Perda Total (%)',
        xaxis_title='Perda Total (%)',
        plot_bgcolor='#f5f7fa',
        xaxis=dict(
            title_font=dict(size=18, color='black'),
            tickfont=dict(size=16, color='black')
        ),
        yaxis=dict(
            tickfont=dict(size=16, color='black')
        ),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
