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
                Sanidade de Híbridos de Milho
            </h1>
            <h3 style="margin-top: 0; color: #e0e0e0; font-weight: 400; font-size: 1.2em;">
                Avaliação comparativa da incidência e severidade das principais doenças, auxiliando na seleção de híbridos mais tolerantes e adaptados às condições regionais.
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

df_analise_sanidade = df_filtrado.copy()

# Desfragmenta o DataFrame para evitar PerformanceWarning
df_analise_sanidade = df_analise_sanidade.copy()

# Mapeamento de colunas para visualização customizada
colunas_renomeadas = [
    ("indexTratamento", "index"),
    ("nome", "Híbrido"),
    ("humidade", "Umd (%)"),
    ("prod_kg_ha_corr", "Prod@13.5% (kg/ha)"),
    ("prod_sc_ha_corr", "Prod@13.5% (sc/ha)"),
    ("numPlantas_ha", "Pop (plantas/ha)"),
    ("manchaTurcicum", "TUR"),
    ("manchaCercospora", "CER"),
    ("manchaBranca", "MB"),
    ("manchaBipolaris", "MPB"),
    ("ferrugemTropical", "FT"),
    ("enfezamento", "ENF"),
    ("graosArdidos", "Ardidos (%)"),
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
colunas_existentes = [c for c in colunas if c in df_analise_sanidade.columns]
df_analise_sanidade_visualizacao = df_analise_sanidade[colunas_existentes].rename(
    columns=novos_nomes)

# Exibe o DataFrame filtrado original
titulo_expander = "Dados Originais - Análise Sanidade"
with st.expander(titulo_expander, expanded=False):
    st.dataframe(df_filtrado, use_container_width=True)

    # Botão para exportar em Excel o DataFrame filtrado original
    buffer_filtro = io.BytesIO()
    df_filtrado.to_excel(buffer_filtro, index=False)  # type: ignore
    buffer_filtro.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel (dados originais - análise conjunta)",
        data=buffer_filtro,
        file_name="dados_originais_analise_sanidade.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =========================
# Configuração visual e funcional do AgGrid
# =========================

# Cria o construtor de opções do grid a partir do DataFrame customizado
# Permite configurar colunas, filtros, menus e estilos
gb = GridOptionsBuilder.from_dataframe(df_analise_sanidade_visualizacao)

# Configuração de casas decimais para colunas numéricas
colunas_formatar = {
    "Prod@13.5% (kg/ha)": 1,
    "Prod@13.5% (sc/ha)": 1,
    "Pop (plantas/ha)": 0,
    "Ardidos (%)": 1
}

for col in df_analise_sanidade_visualizacao.columns:
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
st.subheader("Sanidade de Híbridos de Milho")
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
    df_analise_sanidade_visualizacao,   # DataFrame a ser exibido
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
df_analise_sanidade_visualizacao.to_excel(buffer, index=False)  # type: ignore
buffer.seek(0)
st.download_button(
    label="⬇️ Baixar Excel (Sanidade)",
    data=buffer,
    file_name="sanidade.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# Agrupamento por fazendaRef e pares de indexTratamento
# =========================
# Cria coluna de agrupamento para pares (101,201), (102,202), ..., (121,221)


def agrupa_index(idx):
    if 201 <= idx <= 221:
        return idx - 100
    return idx


df_analise_sanidade['indexTratamentoAgrupado'] = df_analise_sanidade['indexTratamento'].apply(
    agrupa_index)

# Define as colunas de agrupamento e as colunas numéricas para média
group_cols = ['fazendaRef', 'indexTratamentoAgrupado']
colunas_numericas = df_analise_sanidade.select_dtypes(
    include='number').columns.tolist()
colunas_numericas = [c for c in colunas_numericas if c not in [
    'indexTratamento', 'indexTratamentoAgrupado']]

# Substitui zeros por NaN nas colunas numéricas antes do agrupamento
df_analise_sanidade[colunas_numericas] = df_analise_sanidade[colunas_numericas].replace(
    0, np.nan)

# Realiza o agrupamento e calcula a média das colunas numéricas
df_analise_sanidade_agrupado = (
    df_analise_sanidade
    .groupby(group_cols, as_index=False)[colunas_numericas]
    .mean()
)

# Recupera o nome do híbrido para cada (fazendaRef, indexTratamentoAgrupado)
df_nome = (
    df_analise_sanidade
    .groupby(['fazendaRef', 'indexTratamentoAgrupado'])['nome']
    .first()
    .reset_index()
)

# Junta o nome ao DataFrame agrupado
df_analise_sanidade_agrupado = pd.merge(
    df_analise_sanidade_agrupado,
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
    ("manchaTurcicum", "TUR"),
    ("manchaCercospora", "CER"),
    ("manchaBranca", "MB"),
    ("manchaBipolaris", "MPB"),
    ("ferrugemTropical", "FT"),
    ("enfezamento", "ENF"),
    ("tombamentoVerde", "GS"),
    ("graosArdidos", "Ardidos (%)")
]
colunas_agrupado = [c[0] for c in colunas_agrupado_renomeadas]
novos_nomes_agrupado = {c[0]: c[1] for c in colunas_agrupado_renomeadas}
colunas_agrupado_existentes = [
    c for c in colunas_agrupado if c in df_analise_sanidade_agrupado.columns]
df_analise_sanidade_agrupado_visualizacao = df_analise_sanidade_agrupado[colunas_agrupado_existentes].rename(
    columns=novos_nomes_agrupado)  # type: ignore

# =========================
# Exibição do DataFrame agrupado customizado com AgGrid
# =========================
st.subheader("Dados Conjuntos por Híbrido - Sanidade")
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
    df_analise_sanidade_agrupado_visualizacao)

# Configuração de casas decimais para colunas numéricas do agrupado
colunas_formatar_agrupado = {
    "Prod@13.5% (kg/ha)": 1,
    "Prod@13.5% (sc/ha)": 1,
    "Pop (plantas/ha)": 0,
    "TUR": 0,
    "CER": 0,
    "MB": 0,
    "MPB": 0,
    "FT": 0,
    "ENF": 0,
    "GS": 0,
    "Ardidos (%)": 1
}

for col in df_analise_sanidade_agrupado_visualizacao.columns:
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
    df_analise_sanidade_agrupado_visualizacao,
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
df_analise_sanidade_agrupado_visualizacao.to_excel(
    buffer_agrupado_vis, index=False)  # type: ignore
buffer_agrupado_vis.seek(0)
st.download_button(
    label="⬇️ Baixar Excel (Resumo da Sanidade)",
    data=buffer_agrupado_vis,
    file_name="resumo_sanidade.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# st.markdown(
# "### Visualização do DataFrame Agrupado (df_analise_sanidade_agrupado)")
# if 'nome' in df_analise_sanidade_agrupado.columns:
#     st.dataframe(df_analise_sanidade_agrupado[[
#                  'nome'] + [col for col in df_analise_sanidade_agrupado.columns if col != 'nome']], use_container_width=True)
# else:
#     st.dataframe(df_analise_sanidade_agrupado, use_container_width=True)

# Dicionário para nomes amigáveis das doenças
_doencas_labels = {
    "TUR": "TUR",
    "CER": "CER",
    "MB": "MB",
    "MPB": "MPB",
    "FT": "FT",
    "ENF": "ENF",
    "GS": "GS"
}

# Dicionário para mapear prefixos das colunas
_opcoes_doencas = {
    "TUR": "manchaTurcicum",
    "CER": "manchaCercospora",
    "MB": "manchaBranca",
    "MPB": "manchaBipolaris",
    "FT": "ferrugemTropical",
    "ENF": "enfezamento",
    "GS": "tombamentoVerde"
}

# Sidebar: filtro para resumo estatístico das doenças
with st.sidebar:
    with st.expander("Selecionar Doença para Conjunta", expanded=False):
        doencas_selecionadas = []
        for key, val in _opcoes_doencas.items():
            if st.checkbox(key, key=f"check_{key}"):
                doencas_selecionadas.append(key)

# ===== Resumo Estatístico das Doenças por Híbrido =====
colunas_presentes = list(_opcoes_doencas.values())
df_doencas = df_analise_sanidade.copy()

# 📊 Estatísticas principais
resumo = df_doencas.groupby("nome").agg(
    **{f"{col}_mean": (col, "mean") for col in colunas_presentes},
    **{f"{col}_min": (col, "min") for col in colunas_presentes},
    **{f"{col}_max": (col, "max") for col in colunas_presentes},
).round(1).reset_index()

df_resumo_doencas = resumo.copy()

# ➕ Incidência %
for col in colunas_presentes:
    total = df_doencas.groupby("nome")[col].count()
    abaixo_6 = df_doencas[df_doencas[col] < 6].groupby("nome")[col].count()
    incidencia = ((abaixo_6 / total) *
                  100).round(1).reindex(total.index).fillna(0)
    df_resumo_doencas[f"{col}_inc_per"] = df_resumo_doencas["nome"].map(
        incidencia)

# Exibe apenas as colunas das doenças selecionadas, renomeando conforme padrão
colunas_exibir = ["nome"]
rename_dict = {"nome": "Híbrido"}
for doenca in doencas_selecionadas:
    label = _doencas_labels[doenca]
    col_prefix = _opcoes_doencas[doenca]
    colunas_exibir += [
        f"{col_prefix}_mean",
        f"{col_prefix}_min",
        f"{col_prefix}_max",
        f"{col_prefix}_inc_per"
    ]
    rename_dict[f"{col_prefix}_mean"] = f"{label} média"
    rename_dict[f"{col_prefix}_min"] = f"{label} min"
    rename_dict[f"{col_prefix}_max"] = f"{label} max"
    rename_dict[f"{col_prefix}_inc_per"] = f"{label} inc (%)"
colunas_exibir = [
    col for col in colunas_exibir if col in df_resumo_doencas.columns]
df_resumo_aggrid = df_resumo_doencas[colunas_exibir].rename(
    columns=rename_dict)

if doencas_selecionadas:
    from st_aggrid import AgGrid, GridOptionsBuilder
    gb = GridOptionsBuilder.from_dataframe(df_resumo_aggrid)
    gb.configure_default_column(cellStyle={'fontSize': '14px'})
    gb.configure_grid_options(headerHeight=30)
    custom_css = {
        ".ag-header-cell-label": {"font-weight": "bold", "font-size": "15px", "color": "black"}}
    st.markdown(f"""
        <div style="background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 12px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;">
            Conjunta de Doenças — {', '.join(doencas_selecionadas)}
        </div>
    """, unsafe_allow_html=True)
    AgGrid(df_resumo_aggrid, gridOptions=gb.build(), height=400,
           custom_css=custom_css, use_container_width=True)
    # Legenda das siglas (acima do botão de exportar)
    st.markdown(
        """
        <div style='margin-top: 12px; font-size: 1em; color: #444;'>
            <b>Legenda:</b> <b>TUR</b>: Turcicum, <b>CER</b>: Cercospora, <b>MB</b>: Mancha Branca, <b>MPB</b>: Mancha Bipolaris, <b>FT</b>: Ferrugem Tropical, <b>ENF</b>: Enfezamento, <b>GS</b>: Green Snap
        </div>
        """,
        unsafe_allow_html=True
    )
    # Botão para exportar em Excel
    buffer_resumo = io.BytesIO()
    with pd.ExcelWriter(buffer_resumo, engine="xlsxwriter") as writer:  # type: ignore
        df_resumo_aggrid.to_excel(writer, index=False)
    buffer_resumo.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel (Conjunta de Doenças)",
        data=buffer_resumo.getvalue(),
        file_name="conjunta_doencas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Selecione ao menos uma doença para visualizar a conjunta.")

# Gráfico de Grãos Ardidos (%) por Híbrido

df_graos_ardidos = df_analise_sanidade.groupby("nome", as_index=False)[
    "graosArdidos"].mean()
df_graos_ardidos = df_graos_ardidos.sort_values(
    by="graosArdidos", ascending=False)

fig = px.bar(
    df_graos_ardidos,
    x="nome",
    y="graosArdidos",
    color="nome",  # individualiza as cores das barras por híbrido
    labels={"nome": "Híbrido", "graosArdidos": "Grãos Ardidos (%)"},
    title="Média de Grãos Ardidos (%) por Híbrido"
)
# Ajusta os rótulos para uma casa decimal


def set_text(trace, df):
    nome_hibrido = getattr(trace, 'name', None)
    if nome_hibrido is not None:
        valor = df[df["nome"] == nome_hibrido]["graosArdidos"].values
        if len(valor) > 0:
            trace.text = [f"{valor[0]:.1f}"]


fig.for_each_trace(lambda trace: set_text(trace, df_graos_ardidos))
fig.update_traces(
    textposition="outside",
    textfont=dict(size=16, color='black')
)

fig.update_layout(
    xaxis_tickangle=-45,
    height=650,  # aumenta a altura total do gráfico
    font=dict(size=18, color='black'),
    xaxis=dict(title_font=dict(size=20, color='black'),
               tickfont=dict(size=16, color='black')),
    yaxis=dict(title_font=dict(size=20, color='black'),
               tickfont=dict(size=16, color='black')),
    title_font=dict(size=22, color='black'),
    margin=dict(t=60, b=40, l=40, r=40)  # margem superior intermediária
)

st.markdown(
    """
    <div style="background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 12px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;">
        Gráfico de Grãos Ardidos (%) por Híbrido
    </div>
    """,
    unsafe_allow_html=True
)
st.plotly_chart(fig, use_container_width=True)
