from plotly.colors import n_colors
import streamlit as st
import pandas as pd
import io
from st_aggrid import AgGrid, GridOptionsBuilder
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import gaussian_kde
from scipy.interpolate import make_interp_spline
import unicodedata

# Após os imports, defina as funções e o dicionário UMA VEZ SÓ:


def agrupa_index(idx):
    pares = {
        201: 101, 202: 102, 203: 103, 204: 104, 205: 105, 206: 106, 207: 107,
        209: 109, 210: 110, 211: 111, 212: 112, 213: 113, 214: 114, 215: 115,
        216: 116, 217: 117, 218: 118, 220: 120, 221: 121, 219: 208
    }
    if idx in pares:
        return pares[idx]
    return idx


dicionario_fazendas_linhas = {
    "FAZ. SANTA TEREZA": "BAL_1_MA",
    "CACHOEIRA DE MONTIVIDIU": "MTV_GO",
    "BRAVINHOS": "CPB_MG",
    "LOTE 17": "BAL_2_MA",
    "FAZENDA RONCADOR": "ARN_TO",
    "AGROMINA": "BAL_3_MA",
    "FAZENDA CIPÓ": "BDN_TO",
    "SANTA INÊS": "TPC_MG",
    "SÃO TOMAZ DOURADINHO_SHG": "SHG_GO",
    "FAZENDA VENEZA II - GRUPO UNIGGEL": "CAS_TO",
    "CERETTA E RIGON": "CJU_MT",
    "RANCHO 60": "QUE_1_MT",
    "SÍTIO DOIS IRMÃOS": "CVR_MT",
    "CAPÃO": "SGO_MS",
    "FAZENDA ARIRANHA": "JAT_GO",
    "FAZENDA 333": "RVD_GO",
    "FAZENDA TORRE": "JAC_MT",
    "FAZENDA RECANTO": "MRJ_MS",
    "CONQUISTA": "GMO_GO",
    "LONDRINA": "QUE_2_MT",
    "LUIZ PAULO PENNA": "SOR_MT",
    "FAZENDA MODELO": "ITA_MS",
    "SANTA RITA": "VIA_GO",
    "SANTO ANTÔNIO": "ARG_MG",
    "MARANEY": "CHC_GO",
    "ÁGUAS DE CHAPECÓ": "NMT_MT",
    "FAZENDA MAISA": "DOR_MS",
    "FAZENDA CANARINHO": "DIA_MT",
    "FAZENDA JACIARA": "LRV_MT",
    "LUIZ PAULO PENNA": "SCR_MT",
    "FAZENDA PAGANINI (TATI - MILHO)": "CSV_PR",
    "SÍTIO SÃO JOSÉ (MILHO - TATI)": "CMB_PR"
}


def padroniza_nome_linha(nome):
    nome = nome.strip().upper()
    nome = unicodedata.normalize('NFKD', nome).encode(
        'ASCII', 'ignore').decode('ASCII')
    return nome


dicionario_fazendas_linhas_padronizado = {padroniza_nome_linha(
    k): v for k, v in dicionario_fazendas_linhas.items()}


def substitui_nome_ou_codigo_linha(nome):
    nome_strip = nome.strip()
    if '_' in nome_strip and nome_strip[-3:] in ["_GO", "_MS", "_MT", "_MA", "_TO", "_MG"]:
        return nome_strip
    return dicionario_fazendas_linhas_padronizado.get(padroniza_nome_linha(nome_strip), nome_strip)


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
                Analise de Perdas Físicas em Híbridos de Milho
            </h1>
            <h3 style="margin-top: 0; color: #e0e0e0; font-weight: 400; font-size: 1.2em;">
                Analisa o impacto das plantas acamadas, quebradas, dominadas e com colmo podre sobre a produtividade, permitindo identificar híbridos mais tolerantes às adversidades de campo.
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

df_analise_perdas = df_filtrado.copy()

# Desfragmenta o DataFrame para evitar PerformanceWarning
df_analise_perdas = df_analise_perdas.copy()

# Mapeamento de colunas para visualização customizada
colunas_renomeadas = [
    ("indexTratamento", "index"),
    ("nome", "Híbrido"),
    ("humidade", "Umd (%)"),
    ("prod_kg_ha_corr", "Prod@13.5% (kg/ha)"),
    ("prod_sc_ha_corr", "Prod@13.5% (sc/ha)"),
    ("numPlantas_ha", "Pop (plantas/ha)"),
    ("perc_Acamadas", "AC (%)"),
    ("perc_Quebradas", "QBR (%)"),
    ("perc_Dominadas", "DMN (%)"),
    ("perc_ColmoPodre", "CP (%)"),
    ("perc_Total", "Total (%)"),
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
colunas_existentes = [c for c in colunas if c in df_analise_perdas.columns]
df_analise_perdas_visualizacao = df_analise_perdas[colunas_existentes].rename(
    columns=novos_nomes)

# Exibe o DataFrame filtrado original
titulo_expander = "Dados Originais - Análise Perdas Físicas"
with st.expander(titulo_expander, expanded=False):
    st.dataframe(df_filtrado, use_container_width=True)

    # Botão para exportar em Excel o DataFrame filtrado original
    buffer_filtro = io.BytesIO()
    df_filtrado.to_excel(buffer_filtro, index=False)  # type: ignore
    buffer_filtro.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel (dados originais - análise perdas físicas)",
        data=buffer_filtro,
        file_name="dados_originais_perdas_fisicas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =========================
# Configuração visual e funcional do AgGrid
# =========================

# Cria o construtor de opções do grid a partir do DataFrame customizado
# Permite configurar colunas, filtros, menus e estilos
gb = GridOptionsBuilder.from_dataframe(df_analise_perdas_visualizacao)

# Configuração de casas decimais para colunas numéricas
colunas_formatar = {
    "Prod@13.5% (kg/ha)": 1,
    "Prod@13.5% (sc/ha)": 1,
    "Pop (plantas/ha)": 0,
    "AC (%)": 0,
    "QBR (%)": 0,
    "DMN (%)": 0,
    "CP (%)": 0,
    "Total (%)": 0,
}

for col in df_analise_perdas_visualizacao.columns:
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
# Exibição do DataFrame customizado com AgGrid (base: df_analise_sanidade)
# =========================
st.subheader("Perdas Físicas de Híbridos de Milho")
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
    df_analise_perdas_visualizacao,   # DataFrame a ser exibido
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
df_analise_perdas_visualizacao.to_excel(buffer, index=False)  # type: ignore
buffer.seek(0)
st.download_button(
    label="⬇️ Baixar Excel (Perdas Físicas)",
    data=buffer,
    file_name="perdas_fisicas.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# Agrupamento por fazendaRef e pares de indexTratamento
# =========================
# Cria coluna de agrupamento para pares (101,201), (102,202), ..., (121,221)


df_analise_perdas['indexTratamentoAgrupado'] = df_analise_perdas['indexTratamento'].apply(
    agrupa_index)

# Define as colunas de agrupamento e as colunas numéricas para média
group_cols = ['fazendaRef', 'indexTratamentoAgrupado']
colunas_numericas = df_analise_perdas.select_dtypes(
    include='number').columns.tolist()
colunas_numericas = [c for c in colunas_numericas if c not in [
    'indexTratamento', 'indexTratamentoAgrupado']]

# Substitui zeros por NaN nas colunas numéricas antes do agrupamento
df_analise_perdas[colunas_numericas] = df_analise_perdas[colunas_numericas].replace(
    0, np.nan)

# Realiza o agrupamento e calcula a média das colunas numéricas
df_analise_perdas_agrupado = (
    df_analise_perdas
    .groupby(group_cols, as_index=False)[colunas_numericas]
    .mean()
)

# Recupera o nome do híbrido para cada (fazendaRef, indexTratamentoAgrupado)
df_nome = (
    df_analise_perdas
    .groupby(['fazendaRef', 'indexTratamentoAgrupado'])['nome']
    .first()
    .reset_index()
)

# Junta o nome ao DataFrame agrupado
df_analise_perdas_agrupado = pd.merge(
    df_analise_perdas_agrupado,
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
    ("perc_Acamadas", "AC (%)"),
    ("perc_Quebradas", "QBR (%)"),
    ("perc_Dominadas", "DMN (%)"),
    ("perc_ColmoPodre", "CP (%)"),
    ("perc_Total", "Total (%)")
]
colunas_agrupado = [c[0] for c in colunas_agrupado_renomeadas]
novos_nomes_agrupado = {c[0]: c[1] for c in colunas_agrupado_renomeadas}
colunas_agrupado_existentes = [
    c for c in colunas_agrupado if c in df_analise_perdas_agrupado.columns]
df_analise_perdas_agrupado_visualizacao = df_analise_perdas_agrupado[colunas_agrupado_existentes].rename(
    columns=novos_nomes_agrupado)  # type: ignore

# =========================
# Exibição do DataFrame agrupado customizado com AgGrid
# =========================

st.subheader("Dados Conjuntos por Híbrido - Perdas Físicas")
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
    df_analise_perdas_agrupado_visualizacao)

# Configuração de casas decimais para colunas numéricas do agrupado
colunas_formatar_agrupado = {
    "Prod@13.5% (kg/ha)": 1,
    "Prod@13.5% (sc/ha)": 1,
    "Pop (plantas/ha)": 0,
    "AC (%)": 0,
    "QBR (%)": 0,
    "DMN (%)": 0,
    "CP (%)": 0,
    "Total (%)": 0,
}
for col in df_analise_perdas_agrupado_visualizacao.columns:
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
    df_analise_perdas_agrupado_visualizacao,
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
df_analise_perdas_agrupado_visualizacao.to_excel(
    buffer_agrupado_vis, index=False)  # type: ignore
buffer_agrupado_vis.seek(0)
st.download_button(
    label="⬇️ Baixar Excel (Resumo da Perdas Físicas)",
    data=buffer_agrupado_vis,
    file_name="resumo_perdas_fisicas.xlsx",
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
        <h2 style="margin-bottom: 0.2em; color: #22223b; font-size: 18px;">Análise de Perdas Físicas</h2>
        <h4 style="margin-top: 0; color: #4a4e69; font-weight: 400; font-size: 16px;">
           Visualize, por local, as perdas físicas em gráficos de porcentagem de plantas acamadas, quebradas, dominadas e com colmo podre, identificando padrões, outliers e comparando a tolerância dos híbridos.
        </h4>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================
# Visualização completa do DataFrame de análise de perdas (após filtros e cálculos)
# =========================
# st.markdown(
# """
# <div style="background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 12px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;">
# Visualização Completa do DataFrame de Análise de Perdas (todas as colunas)
# </div>
# """,
# unsafe_allow_html=True
# )
# st.dataframe(df_analise_perdas, use_container_width=True)

# =========================
# Gráfico de linhas: perc_Acamadas por Fazenda e Híbrido (média dos pares de indexTratamento)
# =========================
# Dicionário de códigos das fazendas (ajuste conforme necessário)
# Aplica a substituição na coluna 'nomeFazenda' ANTES do agrupamento
if all(col in df_analise_perdas.columns for col in ["nomeFazenda", "nome", "indexTratamento", "perc_Acamadas"]):
    df_plot = df_analise_perdas.copy()
    # Aplica a substituição na coluna 'nomeFazenda' ANTES do agrupamento
    df_plot["nomeFazenda"] = df_plot["nomeFazenda"].apply(
        substitui_nome_ou_codigo_linha)
    df_plot["indexTratamentoAgrupado"] = df_plot["indexTratamento"].apply(
        agrupa_index)
    # Agrupa por fazenda, híbrido e par, calcula média de perc_Acamadas
    df_linhas = df_plot.groupby(["nomeFazenda", "nome", "indexTratamentoAgrupado"], as_index=False)[
        "perc_Acamadas"].mean()
    # Agrupa por fazenda e híbrido, tirando a média dos pares para evitar duplicatas
    df_linhas_unica = df_linhas.groupby(['nomeFazenda', 'nome'], as_index=False)[
        'perc_Acamadas'].mean()
    # Pivot para garantir todas as combinações fazenda × híbrido, preenchendo ausentes com zero
    df_pivot = df_linhas_unica.pivot(
        index="nomeFazenda", columns="nome", values="perc_Acamadas").fillna(0)
    df_linhas_completo = df_pivot.reset_index().melt(
        id_vars="nomeFazenda", var_name="nome", value_name="perc_Acamadas")
    fazendas_ordem = sorted(
        df_linhas_completo["nomeFazenda"].unique().tolist())
    st.markdown(
        """
            <div style="background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 12px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;">
                Perdas Física por Local - Plantas Acamadas (%)
            </div>
            """,
        unsafe_allow_html=True
    )
    fig_linhas = px.line(
        df_linhas_completo,
        x="nomeFazenda",
        y="perc_Acamadas",
        color="nome",
        markers=True,
        labels={
            "nomeFazenda": "Local",
            "perc_Acamadas": "Acamadas (%)",
            "nome": "Híbrido"
        },
        title="Perdas físicas - Acamadas (%)",
        line_shape="spline"
    )
    fig_linhas.update_layout(
        xaxis=dict(
            categoryorder="array",
            categoryarray=fazendas_ordem,
            tickangle=-45,
            title="Local",
            title_font=dict(size=22, color='black'),
            showgrid=False,  # sem grid vertical
            color='black',  # força fonte preta
            tickfont=dict(color='black'),  # cor dos valores do eixo x
        ),
        yaxis=dict(
            title="Acamadas (%)",
            title_font=dict(size=22, color='black'),
            showgrid=True,  # grid horizontal
            gridcolor='#cccccc',
            gridwidth=1,
            color='black',  # força fonte preta
            tickfont=dict(color='black'),  # cor dos valores do eixo y
        ),
        font=dict(size=15, color='black'),
        legend_title_font=dict(size=15, color='black'),
        legend=dict(font=dict(color='black')),
        height=600,
        margin=dict(t=60, b=80, l=40, r=40),
        plot_bgcolor="#f5f7fa"
    )
    # Destaca os marcadores para reforçar a ligação dos pontos
    fig_linhas.update_traces(mode="lines+markers")
    st.plotly_chart(fig_linhas, use_container_width=True)

# =========================
# Gráfico de linhas: perc_Quebradas por Fazenda e Híbrido (média dos pares de indexTratamento)
# =========================
st.markdown(
    """
        <div style="background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 12px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;">
            Perdas Física por Local - Plantas Quebradas (%)
        </div>
        """,
    unsafe_allow_html=True
)
# Agrupa por fazenda, híbrido e par, calcula média de perc_Quebradas
if all(col in df_analise_perdas.columns for col in ["nomeFazenda", "nome", "indexTratamento", "perc_Quebradas"]):
    df_plot_qbr = df_analise_perdas.copy()
    # Aplica a substituição na coluna 'nomeFazenda' ANTES do agrupamento
    df_plot_qbr["nomeFazenda"] = df_plot_qbr["nomeFazenda"].apply(
        substitui_nome_ou_codigo_linha)
    df_plot_qbr["indexTratamentoAgrupado"] = df_plot_qbr["indexTratamento"].apply(
        agrupa_index)
    # Agrupa por fazenda, híbrido e par, calcula média de perc_Quebradas
    df_linhas_qbr = df_plot_qbr.groupby(["nomeFazenda", "nome", "indexTratamentoAgrupado"], as_index=False)[
        "perc_Quebradas"].mean()
    # Agrupa por fazenda e híbrido, tirando a média dos pares para evitar duplicatas
    df_linhas_qbr_unica = df_linhas_qbr.groupby(['nomeFazenda', 'nome'], as_index=False)[
        'perc_Quebradas'].mean()
    # Pivot para garantir todas as combinações fazenda × híbrido, preenchendo ausentes com zero
    df_pivot_qbr = df_linhas_qbr_unica.pivot(
        index="nomeFazenda", columns="nome", values="perc_Quebradas").fillna(0)
    df_linhas_qbr_completo = df_pivot_qbr.reset_index().melt(
        id_vars="nomeFazenda", var_name="nome", value_name="perc_Quebradas")
    fazendas_ordem_qbr = sorted(
        df_linhas_qbr_completo["nomeFazenda"].unique().tolist())
    fig_linhas_qbr = px.line(
        df_linhas_qbr_completo,
        x="nomeFazenda",
        y="perc_Quebradas",
        color="nome",
        markers=True,
        labels={
            "nomeFazenda": "Local",
            "perc_Quebradas": "Quebradas (%)",
            "nome": "Híbrido"
        },
        title="Perdas físicas - Quebradas (%)",
        line_shape="spline"
    )
    fig_linhas_qbr.update_layout(
        xaxis=dict(
            categoryorder="array",
            categoryarray=fazendas_ordem_qbr,
            tickangle=-45,
            title="Local",
            title_font=dict(size=22, color='black'),
            showgrid=False,
            color='black',  # força fonte preta
            tickfont=dict(color='black'),  # cor dos valores do eixo x
        ),
        yaxis=dict(
            title="Quebradas (%)",
            title_font=dict(size=22, color='black'),
            showgrid=True,
            gridcolor='#cccccc',
            gridwidth=1,
            color='black',  # força fonte preta
            tickfont=dict(color='black'),  # cor dos valores do eixo y
        ),
        font=dict(size=15, color='black'),
        legend_title_font=dict(size=15, color='black'),
        legend=dict(font=dict(color='black')),
        height=600,
        margin=dict(t=60, b=80, l=40, r=40),
        plot_bgcolor="#f5f7fa"
    )
    fig_linhas_qbr.update_traces(mode="lines+markers")
    st.plotly_chart(fig_linhas_qbr, use_container_width=True)

    # =========================
    # Gráfico de linhas: perc_Dominadas por Fazenda e Híbrido (média dos pares de indexTratamento)
    # =========================
    st.markdown(
        """
            <div style="background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 12px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;">
                Perdas Física por Local - Plantas Dominadas (%)
            </div>
            """,
        unsafe_allow_html=True
    )
    # Agrupa por fazenda, híbrido e par, calcula média de perc_Dominadas
    if all(col in df_analise_perdas.columns for col in ["nomeFazenda", "nome", "indexTratamento", "perc_Dominadas"]):
        df_plot_dmn = df_analise_perdas.copy()
        # Aplica a substituição na coluna 'nomeFazenda' ANTES do agrupamento
        df_plot_dmn["nomeFazenda"] = df_plot_dmn["nomeFazenda"].apply(
            substitui_nome_ou_codigo_linha)
        df_plot_dmn["indexTratamentoAgrupado"] = df_plot_dmn["indexTratamento"].apply(
            agrupa_index)
        # Agrupa por fazenda, híbrido e par, calcula média de perc_Dominadas
        df_linhas_dmn = df_plot_dmn.groupby(["nomeFazenda", "nome", "indexTratamentoAgrupado"], as_index=False)[
            "perc_Dominadas"].mean()
        # Agrupa por fazenda e híbrido, tirando a média dos pares para evitar duplicatas
        df_linhas_dmn_unica = df_linhas_dmn.groupby(['nomeFazenda', 'nome'], as_index=False)[
            'perc_Dominadas'].mean()
        # Pivot para garantir todas as combinações fazenda × híbrido, preenchendo ausentes com zero
        df_pivot_dmn = df_linhas_dmn_unica.pivot(
            index="nomeFazenda", columns="nome", values="perc_Dominadas").fillna(0)
        df_linhas_dmn_completo = df_pivot_dmn.reset_index().melt(
            id_vars="nomeFazenda", var_name="nome", value_name="perc_Dominadas")
        fazendas_ordem_dmn = sorted(
            df_linhas_dmn_completo["nomeFazenda"].unique().tolist())
        fig_linhas_dmn = px.line(
            df_linhas_dmn_completo,
            x="nomeFazenda",
            y="perc_Dominadas",
            color="nome",
            markers=True,
            labels={
                "nomeFazenda": "Local",
                "perc_Dominadas": "Dominadas (%)",
                "nome": "Híbrido"
            },
            title="Perdas físicas - Dominadas (%)",
            line_shape="spline"
        )
        fig_linhas_dmn.update_layout(
            xaxis=dict(
                categoryorder="array",
                categoryarray=fazendas_ordem_dmn,
                tickangle=-45,
                title="Local",
                title_font=dict(size=22, color='black'),
                showgrid=False,
                color='black',
                tickfont=dict(color='black'),
            ),
            yaxis=dict(
                title="Dominadas (%)",
                title_font=dict(size=22, color='black'),
                showgrid=True,
                gridcolor='#cccccc',
                gridwidth=1,
                color='black',
                tickfont=dict(color='black'),
            ),
            font=dict(size=15, color='black'),
            legend_title_font=dict(size=15, color='black'),
            legend=dict(font=dict(color='black')),
            height=600,
            margin=dict(t=60, b=80, l=40, r=40),
            plot_bgcolor="#f5f7fa"
        )
        fig_linhas_dmn.update_traces(mode="lines+markers")
        st.plotly_chart(fig_linhas_dmn, use_container_width=True)

        # =========================
        # Gráfico de linhas: perc_ColmoPodre por Fazenda e Híbrido (média dos pares de indexTratamento)
        # =========================
        st.markdown(
            """
                <div style="background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 12px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;">
                    Perdas Física por Local - Plantas com Colmo Podre (%)
                </div>
                """,
            unsafe_allow_html=True
        )
        # Agrupa por fazenda, híbrido e par, calcula média de perc_ColmoPodre
        if all(col in df_analise_perdas.columns for col in ["nomeFazenda", "nome", "indexTratamento", "perc_ColmoPodre"]):
            df_plot_cp = df_analise_perdas.copy()
            # Aplica a substituição na coluna 'nomeFazenda' ANTES do agrupamento
            df_plot_cp["nomeFazenda"] = df_plot_cp["nomeFazenda"].apply(
                substitui_nome_ou_codigo_linha)
            df_plot_cp["indexTratamentoAgrupado"] = df_plot_cp["indexTratamento"].apply(
                agrupa_index)
            # Agrupa por fazenda, híbrido e par, calcula média de perc_ColmoPodre
            df_linhas_cp = df_plot_cp.groupby(["nomeFazenda", "nome", "indexTratamentoAgrupado"], as_index=False)[
                "perc_ColmoPodre"].mean()
            # Agrupa por fazenda e híbrido, tirando a média dos pares para evitar duplicatas
            df_linhas_cp_unica = df_linhas_cp.groupby(['nomeFazenda', 'nome'], as_index=False)[
                'perc_ColmoPodre'].mean()
            # Pivot para garantir todas as combinações fazenda × híbrido, preenchendo ausentes com zero
            df_pivot_cp = df_linhas_cp_unica.pivot(
                index="nomeFazenda", columns="nome", values="perc_ColmoPodre").fillna(0)
            df_linhas_cp_completo = df_pivot_cp.reset_index().melt(
                id_vars="nomeFazenda", var_name="nome", value_name="perc_ColmoPodre")
            fazendas_ordem_cp = sorted(
                df_linhas_cp_completo["nomeFazenda"].unique().tolist())
            fig_linhas_cp = px.line(
                df_linhas_cp_completo,
                x="nomeFazenda",
                y="perc_ColmoPodre",
                color="nome",
                markers=True,
                labels={
                    "nomeFazenda": "Local",
                    "perc_ColmoPodre": "Colmo Podre (%)",
                    "nome": "Híbrido"
                },
                title="Perdas físicas - Colmo Podre (%)",
                line_shape="spline"
            )
            fig_linhas_cp.update_layout(
                xaxis=dict(
                    categoryorder="array",
                    categoryarray=fazendas_ordem_cp,
                    tickangle=-45,
                    title="Local",
                    title_font=dict(size=22, color='black'),
                    showgrid=False,
                    color='black',
                    tickfont=dict(color='black'),
                ),
                yaxis=dict(
                    title="Colmo Podre (%)",
                    title_font=dict(size=22, color='black'),
                    showgrid=True,
                    gridcolor='#cccccc',
                    gridwidth=1,
                    color='black',
                    tickfont=dict(color='black'),
                ),
                font=dict(size=15, color='black'),
                legend_title_font=dict(size=15, color='black'),
                legend=dict(font=dict(color='black')),
                height=600,
                margin=dict(t=60, b=80, l=40, r=40),
                plot_bgcolor="#f5f7fa"
            )
            fig_linhas_cp.update_traces(mode="lines+markers")
            st.plotly_chart(fig_linhas_cp, use_container_width=True)

            # =========================
            # Gráfico de linhas: perc_Total por Fazenda e Híbrido (média dos pares de indexTratamento)
            # =========================
            st.markdown(
                """
                    <div style=\"background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 12px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;\">
                        Perdas Física por Local - Total (%)
                    </div>
                    """,
                unsafe_allow_html=True
            )
            # Agrupa por fazenda, híbrido e par, calcula média de perc_Total
            if all(col in df_analise_perdas.columns for col in ["nomeFazenda", "nome", "indexTratamento", "perc_Total"]):
                df_plot_total = df_analise_perdas.copy()
                # Aplica a substituição na coluna 'nomeFazenda' ANTES do agrupamento
                df_plot_total["nomeFazenda"] = df_plot_total["nomeFazenda"].apply(
                    substitui_nome_ou_codigo_linha)
                df_plot_total["indexTratamentoAgrupado"] = df_plot_total["indexTratamento"].apply(
                    agrupa_index)
                # Agrupa por fazenda, híbrido e par, calcula média de perc_Total
                df_linhas_total = df_plot_total.groupby(["nomeFazenda", "nome", "indexTratamentoAgrupado"], as_index=False)[
                    "perc_Total"].mean()
                # Agrupa por fazenda e híbrido, tirando a média dos pares para evitar duplicatas
                df_linhas_total_unica = df_linhas_total.groupby(['nomeFazenda', 'nome'], as_index=False)[
                    'perc_Total'].mean()
                # Pivot para garantir todas as combinações fazenda × híbrido, preenchendo ausentes com zero
                df_pivot_total = df_linhas_total_unica.pivot(
                    index="nomeFazenda", columns="nome", values="perc_Total").fillna(0)
                df_linhas_total_completo = df_pivot_total.reset_index().melt(
                    id_vars="nomeFazenda", var_name="nome", value_name="perc_Total")
                fazendas_ordem_total = sorted(
                    df_linhas_total_completo["nomeFazenda"].unique().tolist())
                fig_linhas_total = px.line(
                    df_linhas_total_completo,
                    x="nomeFazenda",
                    y="perc_Total",
                    color="nome",
                    markers=True,
                    labels={
                        "nomeFazenda": "Local",
                        "perc_Total": "Total (%)",
                        "nome": "Híbrido"
                    },
                    title="Perdas físicas - Total (%)",
                    line_shape="spline"
                )
                fig_linhas_total.update_layout(
                    xaxis=dict(
                        categoryorder="array",
                        categoryarray=fazendas_ordem_total,
                        tickangle=-45,
                        title="Local",
                        title_font=dict(size=22, color='black'),
                        showgrid=False,
                        color='black',
                        tickfont=dict(color='black'),
                    ),
                    yaxis=dict(
                        title="Total (%)",
                        title_font=dict(size=22, color='black'),
                        showgrid=True,
                        gridcolor='#cccccc',
                        gridwidth=1,
                        color='black',
                        tickfont=dict(color='black'),
                    ),
                    font=dict(size=15, color='black'),
                    legend_title_font=dict(size=15, color='black'),
                    legend=dict(font=dict(color='black')),
                    height=600,
                    margin=dict(t=60, b=80, l=40, r=40),
                    plot_bgcolor="#f5f7fa"
                )
                fig_linhas_total.update_traces(mode="lines+markers")
                st.plotly_chart(fig_linhas_total, use_container_width=True)

# =========================
# Tabela resumo agrupada por Híbrido (nome) - Perdas Físicas
# =========================
st.markdown(
    """
    <div style="background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 12px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;">
        Resumo de Perdas Físicas por Híbrido
    </div>
    """,
    unsafe_allow_html=True
)
# Agrupa por nome (Híbrido) e calcula as médias das colunas de interesse
df_resumo_perdas = (
    df_analise_perdas.groupby("nome", as_index=False)[
        ["perc_Acamadas", "perc_Quebradas", "perc_Dominadas", "perc_ColmoPodre"]
    ].mean()
)
# Calcula a coluna Total (%) como soma das quatro
colunas_perdas = ["perc_Acamadas", "perc_Quebradas",
                  "perc_Dominadas", "perc_ColmoPodre"]
df_resumo_perdas["Total (%)"] = df_resumo_perdas[colunas_perdas].sum(axis=1)
# Renomeia as colunas para visualização
renomear = {
    "nome": "Híbrido",
    "perc_Acamadas": "AC (%)",
    "perc_Quebradas": "QBR (%)",
    "perc_Dominadas": "DMN (%)",
    "perc_ColmoPodre": "CP (%)"
}
df_resumo_perdas = df_resumo_perdas.rename(columns=renomear)
# Reordena as colunas
colunas_final = ["Híbrido", "AC (%)", "QBR (%)",
                 "DMN (%)", "CP (%)", "Total (%)"]
df_resumo_perdas = df_resumo_perdas[colunas_final]
# Configura o AgGrid
_gb_resumo = GridOptionsBuilder.from_dataframe(df_resumo_perdas)
for col in ["AC (%)", "QBR (%)", "DMN (%)", "CP (%)", "Total (%)"]:
    _gb_resumo.configure_column(
        col, valueFormatter="value != null ? value.toFixed(1) : ''", headerClass='ag-header-bold')
_gb_resumo.configure_default_column(
    editable=False, groupable=True, filter=True, resizable=True, cellStyle={'fontSize': '12px'})
_gb_resumo.configure_grid_options(headerHeight=30)
_grid_options_resumo = _gb_resumo.build()
AgGrid(
    df_resumo_perdas,
    gridOptions=_grid_options_resumo,
    enable_enterprise_modules=True,
    fit_columns_on_grid_load=False,
    theme="streamlit",
    height=500,
    reload_data=True,
    custom_css=custom_css
)
# Botão para exportar a tabela resumo em Excel
_buffer_resumo = io.BytesIO()
df_resumo_perdas.to_excel(_buffer_resumo, index=False)
_buffer_resumo.seek(0)
st.download_button(
    label="⬇️ Baixar Excel (Resumo de Perdas Físicas por Híbrido)",
    data=_buffer_resumo,
    file_name="resumo_perdas_fisicas_hibrido.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# Curva de sobrevivência para perc_Acamadas por híbrido
# =========================
st.markdown(
    """
    <div style=\"background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 12px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;\">
        Curva de Sobrevivência - Percentual de Plantas Acamadas por Híbrido
    </div>
    """,
    unsafe_allow_html=True
)
# Seleciona apenas híbridos com dados suficientes
df_surv = df_analise_perdas[["nome", "perc_Acamadas"]].dropna()
hibridos = df_surv["nome"].unique()
fig_surv = go.Figure()
area_dict = {}
for h in hibridos:
    dados = df_surv[df_surv["nome"] == h]["perc_Acamadas"].sort_values().values
    if len(dados) < 2:
        continue
    valores = np.unique(dados)
    y_surv = [(dados >= v).sum() / len(dados) for v in valores]
    fig_surv.add_trace(go.Scatter(
        x=valores,
        y=y_surv,
        mode="lines+markers",
        name=h
    ))
    # Área sob a curva (quanto menor, melhor)
    area = np.trapz(y_surv, valores)
    area_dict[h] = area
# Linhas verticais de referência
ref = 10
label = "Referência Acamamento (10%)"
fig_surv.add_vline(x=ref, line_width=2, line_dash="solid", line_color="black")
fig_surv.add_annotation(x=ref, y=1.02, text=label, showarrow=False, yanchor="bottom",
                        xanchor="right", xshift=-5, textangle=-90, font=dict(color="black", size=12))
# Legenda de área sob a curva
area_df = pd.DataFrame(list(area_dict.items()),
                       columns=pd.Index(["Híbrido", "Área sob a curva"]))
area_df = area_df.sort_values("Área sob a curva", ascending=False)
n = len(area_df)
if n > 1:
    cores = n_colors('rgb(200,255,200)',
                     'rgb(255,200,200)', n, colortype='rgb')
else:
    cores = ['rgb(200,255,200)']
area_df["Cor"] = cores
# Adiciona tabela de área sob a curva como annotation
fig_surv.add_trace(go.Table(
    header=dict(values=["<b>Híbrido</b>", "<b>Área sob a curva</b>"],
                fill_color="#f5f7fa", font=dict(color="black", size=13)),
    cells=dict(values=[area_df["Híbrido"], [f"{v:.3f}" for v in area_df["Área sob a curva"]]], fill_color=[
               area_df["Cor"].tolist()], font=dict(color="black", size=13)),
    domain=dict(x=[0.7, 1], y=[0.6, 1])
))
fig_surv.update_layout(
    title="Curva de Sobrevivência - Plantas Acamadas (%)",
    xaxis_title="Percentual de Plantas Acamadas (%)",
    yaxis_title="Sobrevivência (%)",
    font=dict(size=15, color='black'),
    legend_title_text="Híbrido",
    legend_title_font=dict(size=15, color='black'),
    legend=dict(font=dict(color='black')),
    xaxis=dict(
        tickfont=dict(color='black'), title_font=dict(size=18, color='black'), color='black'),
    yaxis=dict(
        tickformat=".0%",
        tickfont=dict(color='black'), title_font=dict(size=18, color='black'), color='black'),
    height=650,
    margin=dict(t=60, b=80, l=40, r=40),
    plot_bgcolor="#f5f7fa"
)
st.plotly_chart(fig_surv, use_container_width=True)

# =========================
# Curva de sobrevivência para perc_Quebradas por híbrido
# =========================
st.markdown(
    """
    <div style=\"background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 12px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;\">
        Curva de Sobrevivência - Percentual de Plantas Quebradas por Híbrido
    </div>
    """,
    unsafe_allow_html=True
)
fig_surv_qbr = go.Figure()
area_dict_qbr = {}
df_surv_qbr = df_analise_perdas[["nome", "perc_Quebradas"]].dropna()
hibridos_qbr = df_surv_qbr["nome"].unique()
for h in hibridos_qbr:
    dados = df_surv_qbr[df_surv_qbr["nome"] ==
                        h]["perc_Quebradas"].sort_values().values
    if len(dados) < 2:
        continue
    valores = np.unique(dados)
    y_surv = [(dados >= v).sum() / len(dados) for v in valores]
    fig_surv_qbr.add_trace(go.Scatter(
        x=valores,
        y=y_surv,
        mode="lines+markers",
        name=h
    ))
    area = np.trapz(y_surv, valores)
    area_dict_qbr[h] = area
# Linha de referência 10%
ref = 10
label = "Referência Quebradas (10%)"
fig_surv_qbr.add_vline(x=ref, line_width=2,
                       line_dash="solid", line_color="black")
fig_surv_qbr.add_annotation(x=ref, y=1.02, text=label, showarrow=False, yanchor="bottom",
                            xanchor="right", xshift=-5, textangle=-90, font=dict(color="black", size=12))
# Legenda de área sob a curva
area_df_qbr = pd.DataFrame(list(area_dict_qbr.items()),
                           columns=pd.Index(["Híbrido", "Área sob a curva"]))
area_df_qbr = area_df_qbr.sort_values("Área sob a curva", ascending=False)
n_qbr = len(area_df_qbr)
if n_qbr > 1:
    cores_qbr = n_colors('rgb(200,255,200)',
                         'rgb(255,200,200)', n_qbr, colortype='rgb')
else:
    cores_qbr = ['rgb(200,255,200)']
area_df_qbr["Cor"] = cores_qbr
fig_surv_qbr.add_trace(go.Table(
    header=dict(values=["<b>Híbrido</b>", "<b>Área sob a curva</b>"],
                fill_color="#f5f7fa", font=dict(color="black", size=13)),
    cells=dict(values=[area_df_qbr["Híbrido"], [f"{v:.3f}" for v in area_df_qbr["Área sob a curva"]]], fill_color=[
               area_df_qbr["Cor"].tolist()], font=dict(color="black", size=13)),
    domain=dict(x=[0.7, 1], y=[0.6, 1])
))
fig_surv_qbr.update_layout(
    title="Curva de Sobrevivência - Plantas Quebradas (%)",
    xaxis_title="Percentual de Plantas Quebradas (%)",
    yaxis_title="Sobrevivência (%)",
    font=dict(size=15, color='black'),
    legend_title_text="Híbrido",
    legend_title_font=dict(size=15, color='black'),
    legend=dict(font=dict(color='black')),
    xaxis=dict(
        tickfont=dict(color='black'), title_font=dict(size=18, color='black'), color='black'),
    yaxis=dict(
        tickformat=".0%",
        tickfont=dict(color='black'), title_font=dict(size=18, color='black'), color='black'),
    height=650,
    margin=dict(t=60, b=80, l=40, r=40),
    plot_bgcolor="#f5f7fa"
)
st.plotly_chart(fig_surv_qbr, use_container_width=True)

# =========================
# Curva de sobrevivência para perc_Dominadas por híbrido
# =========================
st.markdown(
    """
    <div style=\"background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 12px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;\">
        Curva de Sobrevivência - Percentual de Plantas Dominadas por Híbrido
    </div>
    """,
    unsafe_allow_html=True
)
fig_surv_dmn = go.Figure()
area_dict_dmn = {}
df_surv_dmn = df_analise_perdas[["nome", "perc_Dominadas"]].dropna()
hibridos_dmn = df_surv_dmn["nome"].unique()
for h in hibridos_dmn:
    dados = df_surv_dmn[df_surv_dmn["nome"] ==
                        h]["perc_Dominadas"].sort_values().values
    if len(dados) < 2:
        continue
    valores = np.unique(dados)
    y_surv = [(dados >= v).sum() / len(dados) for v in valores]
    fig_surv_dmn.add_trace(go.Scatter(
        x=valores,
        y=y_surv,
        mode="lines+markers",
        name=h
    ))
    area = np.trapz(y_surv, valores)
    area_dict_dmn[h] = area
# Linha de referência 10%
ref = 10
label = "Referência Dominadas (10%)"
fig_surv_dmn.add_vline(x=ref, line_width=2,
                       line_dash="solid", line_color="black")
fig_surv_dmn.add_annotation(x=ref, y=1.02, text=label, showarrow=False, yanchor="bottom",
                            xanchor="right", xshift=-5, textangle=-90, font=dict(color="black", size=12))
# Legenda de área sob a curva
area_df_dmn = pd.DataFrame(list(area_dict_dmn.items()),
                           columns=pd.Index(["Híbrido", "Área sob a curva"]))
area_df_dmn = area_df_dmn.sort_values("Área sob a curva", ascending=False)
n_dmn = len(area_df_dmn)
if n_dmn > 1:
    cores_dmn = n_colors('rgb(200,255,200)',
                         'rgb(255,200,200)', n_dmn, colortype='rgb')
else:
    cores_dmn = ['rgb(200,255,200)']
area_df_dmn["Cor"] = cores_dmn
fig_surv_dmn.add_trace(go.Table(
    header=dict(values=["<b>Híbrido</b>", "<b>Área sob a curva</b>"],
                fill_color="#f5f7fa", font=dict(color="black", size=13)),
    cells=dict(values=[area_df_dmn["Híbrido"], [f"{v:.3f}" for v in area_df_dmn["Área sob a curva"]]], fill_color=[
               area_df_dmn["Cor"].tolist()], font=dict(color="black", size=13)),
    domain=dict(x=[0.7, 1], y=[0.6, 1])
))
fig_surv_dmn.update_layout(
    title="Curva de Sobrevivência - Plantas Dominadas (%)",
    xaxis_title="Percentual de Plantas Dominadas (%)",
    yaxis_title="Sobrevivência (%)",
    font=dict(size=15, color='black'),
    legend_title_text="Híbrido",
    legend_title_font=dict(size=15, color='black'),
    legend=dict(font=dict(color='black')),
    xaxis=dict(
        tickfont=dict(color='black'), title_font=dict(size=18, color='black'), color='black'),
    yaxis=dict(
        tickformat=".0%",
        tickfont=dict(color='black'), title_font=dict(size=18, color='black'), color='black'),
    height=650,
    margin=dict(t=60, b=80, l=40, r=40),
    plot_bgcolor="#f5f7fa"
)
st.plotly_chart(fig_surv_dmn, use_container_width=True)

# =========================
# Curva de sobrevivência para perc_ColmoPodre por híbrido
# =========================
st.markdown(
    """
    <div style=\"background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 12px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;\">
        Curva de Sobrevivência - Percentual de Plantas com Colmo Podre por Híbrido
    </div>
    """,
    unsafe_allow_html=True
)
fig_surv_cp = go.Figure()
area_dict_cp = {}
df_surv_cp = df_analise_perdas[["nome", "perc_ColmoPodre"]].dropna()
hibridos_cp = df_surv_cp["nome"].unique()
for h in hibridos_cp:
    dados = df_surv_cp[df_surv_cp["nome"] ==
                       h]["perc_ColmoPodre"].sort_values().values
    if len(dados) < 2:
        continue
    valores = np.unique(dados)
    y_surv = [(dados >= v).sum() / len(dados) for v in valores]
    fig_surv_cp.add_trace(go.Scatter(
        x=valores,
        y=y_surv,
        mode="lines+markers",
        name=h
    ))
    area = np.trapz(y_surv, valores)
    area_dict_cp[h] = area
# Linha de referência 10%
ref = 10
label = "Referência Colmo Podre (10%)"
fig_surv_cp.add_vline(x=ref, line_width=2,
                      line_dash="solid", line_color="black")
fig_surv_cp.add_annotation(x=ref, y=1.02, text=label, showarrow=False, yanchor="bottom",
                           xanchor="right", xshift=-5, textangle=-90, font=dict(color="black", size=12))
# Legenda de área sob a curva
area_df_cp = pd.DataFrame(list(area_dict_cp.items()),
                          columns=pd.Index(["Híbrido", "Área sob a curva"]))
area_df_cp = area_df_cp.sort_values("Área sob a curva", ascending=False)
n_cp = len(area_df_cp)
if n_cp > 1:
    cores_cp = n_colors('rgb(200,255,200)',
                        'rgb(255,200,200)', n_cp, colortype='rgb')
else:
    cores_cp = ['rgb(200,255,200)']
area_df_cp["Cor"] = cores_cp
fig_surv_cp.add_trace(go.Table(
    header=dict(values=["<b>Híbrido</b>", "<b>Área sob a curva</b>"],
                fill_color="#f5f7fa", font=dict(color="black", size=13)),
    cells=dict(values=[area_df_cp["Híbrido"], [f"{v:.3f}" for v in area_df_cp["Área sob a curva"]]], fill_color=[
               area_df_cp["Cor"].tolist()], font=dict(color="black", size=13)),
    domain=dict(x=[0.7, 1], y=[0.6, 1])
))
fig_surv_cp.update_layout(
    title="Curva de Sobrevivência - Plantas com Colmo Podre (%)",
    xaxis_title="Percentual de Plantas com Colmo Podre (%)",
    yaxis_title="Sobrevivência (%)",
    font=dict(size=15, color='black'),
    legend_title_text="Híbrido",
    legend_title_font=dict(size=15, color='black'),
    legend=dict(font=dict(color='black')),
    xaxis=dict(
        tickfont=dict(color='black'), title_font=dict(size=18, color='black'), color='black'),
    yaxis=dict(
        tickformat=".0%",
        tickfont=dict(color='black'), title_font=dict(size=18, color='black'), color='black'),
    height=650,
    margin=dict(t=60, b=80, l=40, r=40),
    plot_bgcolor="#f5f7fa"
)
st.plotly_chart(fig_surv_cp, use_container_width=True)

# =========================
# Curva de sobrevivência para perc_Total por híbrido
# =========================
st.markdown(
    """
    <div style=\"background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 12px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;\">
        Curva de Sobrevivência - Percentual Total de Perdas por Híbrido
    </div>
    """,
    unsafe_allow_html=True
)
fig_surv_total = go.Figure()
area_dict_total = {}
df_surv_total = df_analise_perdas[["nome", "perc_Total"]].dropna()
hibridos_total = df_surv_total["nome"].unique()
for h in hibridos_total:
    dados = df_surv_total[df_surv_total["nome"]
                          == h]["perc_Total"].sort_values().values
    if len(dados) < 2:
        continue
    valores = np.unique(dados)
    y_surv = [(dados >= v).sum() / len(dados) for v in valores]
    fig_surv_total.add_trace(go.Scatter(
        x=valores,
        y=y_surv,
        mode="lines+markers",
        name=h
    ))
    area = np.trapz(y_surv, valores)
    area_dict_total[h] = area
# Linha de referência 10%
ref = 10
label = "Referência Total (10%)"
fig_surv_total.add_vline(
    x=ref, line_width=2, line_dash="solid", line_color="black")
fig_surv_total.add_annotation(x=ref, y=1.02, text=label, showarrow=False, yanchor="bottom",
                              xanchor="right", xshift=-5, textangle=-90, font=dict(color="black", size=12))
# Legenda de área sob a curva
area_df_total = pd.DataFrame(list(area_dict_total.items()), columns=pd.Index([
                             "Híbrido", "Área sob a curva"]))
area_df_total = area_df_total.sort_values("Área sob a curva", ascending=False)
n_total = len(area_df_total)
if n_total > 1:
    cores_total = n_colors(
        'rgb(200,255,200)', 'rgb(255,200,200)', n_total, colortype='rgb')
else:
    cores_total = ['rgb(200,255,200)']
area_df_total["Cor"] = cores_total
fig_surv_total.add_trace(go.Table(
    header=dict(values=["<b>Híbrido</b>", "<b>Área sob a curva</b>"],
                fill_color="#f5f7fa", font=dict(color="black", size=13)),
    cells=dict(values=[area_df_total["Híbrido"], [f"{v:.3f}" for v in area_df_total["Área sob a curva"]]], fill_color=[
               area_df_total["Cor"].tolist()], font=dict(color="black", size=13)),
    domain=dict(x=[0.7, 1], y=[0.6, 1])
))
fig_surv_total.update_layout(
    title="Curva de Sobrevivência - Perdas Físicas Totais (%)",
    xaxis_title="Percentual Total de Perdas (%)",
    yaxis_title="Sobrevivência (%)",
    font=dict(size=15, color='black'),
    legend_title_text="Híbrido",
    legend_title_font=dict(size=15, color='black'),
    legend=dict(font=dict(color='black')),
    xaxis=dict(
        tickfont=dict(color='black'), title_font=dict(size=18, color='black'), color='black'),
    yaxis=dict(
        tickformat=".0%",
        tickfont=dict(color='black'), title_font=dict(size=18, color='black'), color='black'),
    height=650,
    margin=dict(t=60, b=80, l=40, r=40),
    plot_bgcolor="#f5f7fa"
)
st.plotly_chart(fig_surv_total, use_container_width=True)
