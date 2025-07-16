import streamlit as st
import pandas as pd
import io
from st_aggrid import AgGrid, GridOptionsBuilder
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import gaussian_kde
from plotly.graph_objs import Scatter

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
                Índice Ambiental: Desempenho de Híbridos de Milho em Diferentes Ambientes
            </h1>
            <h3 style="margin-top: 0; color: #e0e0e0; font-weight: 400; font-size: 1.2em;">
                Avalia a adaptabilidade e estabilidade dos híbridos, relacionando seu desempenho produtivo às variações ambientais dos locais de cultivo.
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
with st.expander("Ver tabela de Produção e Componentes Produtivos", expanded=False):
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
    df_analise_conjunta_visualizacao.to_excel(
        buffer, index=False)  # type: ignore
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
    if 201 <= idx <= 221:
        return idx - 100
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
with st.expander("Ver tabela de Dados Conjuntos por Híbrido", expanded=False):
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

    if 'Média do Local (sc/ha)' in df_analise_conjunta_agrupado_visualizacao.columns:
        df_analise_conjunta_agrupado_visualizacao = df_analise_conjunta_agrupado_visualizacao.sort_values(
            'Média do Local (sc/ha)', ascending=True)

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
# Gráfico de Índice Ambiental - TODAS AS PARCELAS (NÃO AGRUPADO)
# =========================
st.markdown(
    """
    <div style="
        background-color: #f5f7fa;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.10);
        padding: 24px 18px 18px 18px;
        margin-bottom: 24px;
        ">
        <h2 style="margin-bottom: 0.2em; color: #22223b; font-size: 18px;">Gráfico de Índice Ambiental - (Todas parcelas)</h2>
        <h4 style="margin-top: 0; color: #4a4e69; font-weight: 400; font-size: 15px;">
            Relação entre a média de produção do local e a produção dos híbridos em cada local.
        </h4>
    </div>
    """,
    unsafe_allow_html=True
)

# Calcula a média de produção por local (fazendaRef) - NÃO AGRUPADO
media_local_nao_agrupado = df_analise_conjunta.groupby(
    'fazendaRef')['prod_sc_ha_corr'].mean().reset_index()
media_local_nao_agrupado = media_local_nao_agrupado.rename(
    columns={'prod_sc_ha_corr': 'media_local_sc_ha'})

# Junta a média de cada local ao DataFrame principal - NÃO AGRUPADO
df_indice_ambiental_nao_agrupado = df_analise_conjunta.merge(
    media_local_nao_agrupado, on='fazendaRef', how='left')

# Gráfico NÃO AGRUPADO
fig_nao_agrupado = px.scatter(
    df_indice_ambiental_nao_agrupado,
    x='media_local_sc_ha',
    y='prod_sc_ha_corr',
    color='nome',  # Nome do híbrido
    hover_data=['fazendaRef', 'nome', 'prod_sc_ha_corr', 'media_local_sc_ha'],
    labels={
        'media_local_sc_ha': 'Média do Local (sc/ha)',
        'prod_sc_ha_corr': 'Produção do Híbrido (sc/ha)',
        'nome': 'Híbrido'
    },
    title='Índice Ambiental: Produção do Híbrido vs. Média do Local'
)
fig_nao_agrupado.update_traces(marker=dict(size=7, line=dict(width=1)))
fig_nao_agrupado.update_traces(marker_line_color=None, marker_line_width=1,
                               selector=dict(mode='markers'))
# Adicionar reta de tendência (ajuste linear) para cada híbrido
hibridos_nao_agrupado = df_indice_ambiental_nao_agrupado['nome'].unique()
cores_nao_agrupado = {}
traces_nao_agrupado = list(fig_nao_agrupado.data)
for i, hibrido in enumerate(hibridos_nao_agrupado):
    if i < len(traces_nao_agrupado):
        trace = traces_nao_agrupado[i]
        if isinstance(trace, Scatter):
            cor = getattr(trace.marker, 'color', None)
            if isinstance(cor, (list, tuple, np.ndarray)):
                if len(cor) > 0:
                    cor = cor[0]
                else:
                    cor = None
            if cor is None:
                cor = px.colors.qualitative.Plotly[i % len(
                    px.colors.qualitative.Plotly)]
            cores_nao_agrupado[hibrido] = cor
for hibrido in hibridos_nao_agrupado:
    dados_hibrido = df_indice_ambiental_nao_agrupado[df_indice_ambiental_nao_agrupado['nome'] == hibrido]
    x = dados_hibrido['media_local_sc_ha']
    y = dados_hibrido['prod_sc_ha_corr']
    mask = pd.notnull(x) & pd.notnull(y)
    if mask.sum() > 1:
        coef = np.polyfit(x[mask], y[mask], 1)
        x_fit = np.linspace(x[mask].min(), x[mask].max(), 100)
        y_fit = coef[0] * x_fit + coef[1]
        import plotly.graph_objects as go
        fig_nao_agrupado.add_trace(go.Scatter(
            x=x_fit,
            y=y_fit,
            mode='lines',
            line=dict(color=cores_nao_agrupado.get(
                hibrido, None), width=2, dash=None),
            name=f'Tendência {hibrido}',
            showlegend=True
        ))
fig_nao_agrupado.update_layout(
    xaxis_title='Média do Local (sc/ha)',
    yaxis_title='Produção do Híbrido (sc/ha)',
    legend_title='Híbrido',
    plot_bgcolor='#f5f7fa',
    xaxis=dict(
        title_font=dict(size=18, color='black'),
        tickfont=dict(size=16, color='black')
    ),
    yaxis=dict(
        title_font=dict(size=18, color='black'),
        tickfont=dict(size=16, color='black')
    )
)
st.plotly_chart(fig_nao_agrupado, use_container_width=True)

# =========================
# Tabela: Produção x Média do Local x Diferença (absoluta e relativa) - NÃO AGRUPADO
# =========================

df_tabela_indice_nao_agrupado = df_indice_ambiental_nao_agrupado[[
    'fazendaRef', 'nome', 'prod_sc_ha_corr', 'media_local_sc_ha']].copy()
df_tabela_indice_nao_agrupado['Diferença Absoluta (sc/ha)'] = df_tabela_indice_nao_agrupado['prod_sc_ha_corr'] - \
    df_tabela_indice_nao_agrupado['media_local_sc_ha']
df_tabela_indice_nao_agrupado['Diferença Relativa (%)'] = 100 * \
    df_tabela_indice_nao_agrupado['Diferença Absoluta (sc/ha)'] / \
    df_tabela_indice_nao_agrupado['media_local_sc_ha']
colunas_tabela_nao_agrupado = {
    'fazendaRef': 'Local',
    'nome': 'Híbrido',
    'prod_sc_ha_corr': 'Produção (sc/ha)',
    'media_local_sc_ha': 'Média do Local (sc/ha)',
    'Diferença Absoluta (sc/ha)': 'Diferença Absoluta (sc/ha)',
    'Diferença Relativa (%)': 'Diferença Relativa (%)'
}
df_tabela_indice_nao_agrupado = df_tabela_indice_nao_agrupado.rename(
    columns=colunas_tabela_nao_agrupado)  # type: ignore
formatar_nao_agrupado = {
    'Produção (sc/ha)': '{:.1f}',
    'Média do Local (sc/ha)': '{:.1f}',
    'Diferença Absoluta (sc/ha)': '{:.1f}',
    'Diferença Relativa (%)': '{:.2f}'
}
for col, fmt in formatar_nao_agrupado.items():
    df_tabela_indice_nao_agrupado[col] = df_tabela_indice_nao_agrupado[col].map(
        lambda x: fmt.format(x) if pd.notnull(x) else "")

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
        Tabela: Produção do Híbrido, Média do Local e Diferença (Todas parcelas)
    </div>
    """,
    unsafe_allow_html=True
)
with st.expander("Ver tabela detalhada por híbrido/local (todas parcelas)", expanded=False):
    st.markdown(
        """
        <div style="
            background-color: #f5f7fa;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.07);
            padding: 16px 18px 10px 18px;
            margin-bottom: 10px;
            margin-top: 0px;
            width: fit-content;
            display: inline-block;
        ">
            <b>Tabela Detalhada: Produção do Híbrido, Média do Local e Diferença (Todas parcelas)</b>
        </div>
        """,
        unsafe_allow_html=True
    )
    gb_detalhada_nao_agrupado = GridOptionsBuilder.from_dataframe(
        df_tabela_indice_nao_agrupado)
    colunas_formatar_nao_agrupado = {
        'Produção (sc/ha)': 1,
        'Média do Local (sc/ha)': 1,
        'Diferença Absoluta (sc/ha)': 1,
        'Diferença Relativa (%)': 2
    }
    for col in df_tabela_indice_nao_agrupado.columns:
        if col in colunas_formatar_nao_agrupado:
            casas = colunas_formatar_nao_agrupado[col]
            gb_detalhada_nao_agrupado.configure_column(
                col,
                headerClass='ag-header-bold',
                menuTabs=['generalMenuTab', 'filterMenuTab', 'columnsMenuTab'],
                valueFormatter=f"value != null ? Number(value).toFixed({casas}) : ''"
            )
        else:
            gb_detalhada_nao_agrupado.configure_column(
                col,
                headerClass='ag-header-bold',
                menuTabs=['generalMenuTab', 'filterMenuTab', 'columnsMenuTab']
            )
    gb_detalhada_nao_agrupado.configure_default_column(
        editable=False, groupable=True, filter=True, resizable=True, cellStyle={'fontSize': '12px'})
    gb_detalhada_nao_agrupado.configure_grid_options(headerHeight=30)
    grid_options_detalhada_nao_agrupado = gb_detalhada_nao_agrupado.build()
    custom_css = {
        ".ag-header-cell-label": {"font-weight": "bold", "font-size": "12px", "color": "black"},
        ".ag-cell": {"color": "black", "font-size": "12px"}
    }
    # Chave única e estática para garantir renderização imediata
    AgGrid(
        df_tabela_indice_nao_agrupado,
        gridOptions=grid_options_detalhada_nao_agrupado,
        enable_enterprise_modules=True,
        fit_columns_on_grid_load=False,
        theme="streamlit",
        height=400,
        reload_data=True,
        custom_css=custom_css,
        key="aggrid_indice_ambiental_detalhado_nao_agrupado_static"
    )
    buffer_tabela_nao_agrupado = io.BytesIO()
    df_tabela_indice_nao_agrupado.to_excel(
        buffer_tabela_nao_agrupado, index=False, engine='xlsxwriter')  # type: ignore
    buffer_tabela_nao_agrupado.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel (Índice Ambiental - Diferenças - Todas parcelas)",
        data=buffer_tabela_nao_agrupado,
        file_name="indice_ambiental_diferencas_todas_parcelas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    # Tabela resumo por híbrido (médias) - NÃO AGRUPADO
    st.markdown(
        """
        <div style="
            background-color: #f5f7fa;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.07);
            padding: 16px 18px 10px 18px;
            margin-bottom: 18px;
            margin-top: 0px;
            width: fit-content;
            display: inline-block;
        ">
            <b>Médias das Diferenças por Híbrido (Todas parcelas)</b>
        </div>
        """,
        unsafe_allow_html=True
    )
    df_tabela_media_nao_agrupado = df_indice_ambiental_nao_agrupado[[
        'nome', 'prod_sc_ha_corr', 'media_local_sc_ha']].copy()
    df_tabela_media_nao_agrupado['Diferença Absoluta (sc/ha)'] = df_tabela_media_nao_agrupado['prod_sc_ha_corr'] - \
        df_tabela_media_nao_agrupado['media_local_sc_ha']
    df_tabela_media_nao_agrupado['Diferença Relativa (%)'] = 100 * \
        df_tabela_media_nao_agrupado['Diferença Absoluta (sc/ha)'] / \
        df_tabela_media_nao_agrupado['media_local_sc_ha']
    resumo_hibrido_nao_agrupado = df_tabela_media_nao_agrupado.groupby('nome').agg({
        'Diferença Absoluta (sc/ha)': 'mean',
        'Diferença Relativa (%)': 'mean'
    }).reset_index()
    resumo_hibrido_nao_agrupado = resumo_hibrido_nao_agrupado.rename(columns={
        'nome': 'Híbrido',
        'Diferença Absoluta (sc/ha)': 'Média Diferença Absoluta (sc/ha)',
        'Diferença Relativa (%)': 'Média Diferença Relativa (%)'
    })
    gb_resumo_nao_agrupado = GridOptionsBuilder.from_dataframe(
        resumo_hibrido_nao_agrupado)
    gb_resumo_nao_agrupado.configure_column('Média Diferença Absoluta (sc/ha)',
                                            valueFormatter="value != null ? Number(value).toFixed(2) : ''", headerClass='ag-header-bold')
    gb_resumo_nao_agrupado.configure_column('Média Diferença Relativa (%)',
                                            valueFormatter="value != null ? Number(value).toFixed(2) : ''", headerClass='ag-header-bold')
    gb_resumo_nao_agrupado.configure_column(
        'Híbrido', headerClass='ag-header-bold')
    gb_resumo_nao_agrupado.configure_default_column(
        editable=False, groupable=True, filter=True, resizable=True, cellStyle={'fontSize': '12px'})
    gb_resumo_nao_agrupado.configure_grid_options(headerHeight=30)
    grid_options_resumo_nao_agrupado = gb_resumo_nao_agrupado.build()
    num_linhas_nao_agrupado = len(resumo_hibrido_nao_agrupado)
    altura_nao_agrupado = min(
        max(32 * (num_linhas_nao_agrupado + 1), 200), 600)
    AgGrid(
        resumo_hibrido_nao_agrupado,
        gridOptions=grid_options_resumo_nao_agrupado,
        enable_enterprise_modules=True,
        fit_columns_on_grid_load=False,
        theme="streamlit",
        height=altura_nao_agrupado,
        reload_data=True,
        custom_css=custom_css,
        key="aggrid_resumo_hibrido_nao_agrupado"
    )
    buffer_resumo_nao_agrupado = io.BytesIO()
    resumo_hibrido_nao_agrupado.to_excel(buffer_resumo_nao_agrupado, index=False,
                                         engine='xlsxwriter')  # type: ignore
    buffer_resumo_nao_agrupado.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel (Resumo por Híbrido - Todas parcelas)",
        data=buffer_resumo_nao_agrupado,
        file_name="resumo_diferencas_por_hibrido_todas_parcelas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )  # type: ignore

# =========================
# Gráfico de Índice Ambiental Agrupado (MÉDIA DAS PARCELAS)
# =========================
st.markdown(
    """
    <div style="
        background-color: #f5f7fa;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.10);
        padding: 24px 18px 18px 18px;
        margin-bottom: 24px;
        ">
        <h2 style="margin-bottom: 0.2em; color: #22223b; font-size: 18px;">Gráfico de Índice Ambiental (Média das parcelas)</h2>
        <h4 style="margin-top: 0; color: #4a4e69; font-weight: 400; font-size: 15px;">
            Relação entre a média de produção do local e a produção dos híbridos em cada local.
        </h4>
    </div>
    """,
    unsafe_allow_html=True
)

# Calcula a média de produção por local (fazendaRef)
media_local = df_analise_conjunta_agrupado.groupby(
    'fazendaRef')['prod_sc_ha_corr'].mean().reset_index()
media_local = media_local.rename(
    columns={'prod_sc_ha_corr': 'media_local_sc_ha'})

# Junta a média de cada local ao DataFrame principal
df_indice_ambiental = df_analise_conjunta_agrupado.merge(
    media_local, on='fazendaRef', how='left')

# Gráfico
fig = px.scatter(
    df_indice_ambiental,
    x='media_local_sc_ha',
    y='prod_sc_ha_corr',
    color='nome',  # Nome do híbrido
    hover_data=['fazendaRef', 'nome', 'prod_sc_ha_corr', 'media_local_sc_ha'],
    labels={
        'media_local_sc_ha': 'Média do Local (sc/ha)',
        'prod_sc_ha_corr': 'Produção do Híbrido (sc/ha)',
        'nome': 'Híbrido'
    },
    title='Índice Ambiental: Produção do Híbrido vs. Média do Local'
)
# Deixar os pontos menores e borda igual ao preenchimento
fig.update_traces(marker=dict(size=7, line=dict(width=1)))
fig.update_traces(marker_line_color=None, marker_line_width=1,
                  selector=dict(mode='markers'))

# Adicionar reta de tendência (ajuste linear) para cada híbrido
hibridos = df_indice_ambiental['nome'].unique()
cores = {}
# Mapear cor de cada híbrido no gráfico (apenas os primeiros N traces, um para cada híbrido)
traces = list(fig.data)
for i, hibrido in enumerate(hibridos):
    if i < len(traces):
        trace = traces[i]
        if isinstance(trace, Scatter):
            # Corrigir acesso à cor do marker de forma segura
            cor = getattr(trace.marker, 'color', None)
            # Se for lista/array, pega a primeira cor
            if isinstance(cor, (list, tuple, np.ndarray)):
                if len(cor) > 0:
                    cor = cor[0]
                else:
                    cor = None
            # Se não encontrou cor, usa cor padrão do Plotly
            if cor is None:
                cor = px.colors.qualitative.Plotly[i % len(
                    px.colors.qualitative.Plotly)]
            cores[hibrido] = cor
for hibrido in hibridos:
    dados_hibrido = df_indice_ambiental[df_indice_ambiental['nome'] == hibrido]
    x = dados_hibrido['media_local_sc_ha']
    y = dados_hibrido['prod_sc_ha_corr']
    mask = pd.notnull(x) & pd.notnull(y)
    if mask.sum() > 1:
        coef = np.polyfit(x[mask], y[mask], 1)
        x_fit = np.linspace(x[mask].min(), x[mask].max(), 100)
        y_fit = coef[0] * x_fit + coef[1]
        import plotly.graph_objects as go
        fig.add_trace(go.Scatter(
            x=x_fit,
            y=y_fit,
            mode='lines',
            line=dict(color=cores.get(hibrido, None), width=2, dash=None),
            name=f'Tendência {hibrido}',
            showlegend=True
        ))
fig.update_layout(
    xaxis_title='Média do Local (sc/ha)',
    yaxis_title='Produção do Híbrido (sc/ha)',
    legend_title='Híbrido',
    plot_bgcolor='#f5f7fa',
    xaxis=dict(
        title_font=dict(size=18, color='black'),
        tickfont=dict(size=16, color='black')
    ),
    yaxis=dict(
        title_font=dict(size=18, color='black'),
        tickfont=dict(size=16, color='black')
    )
)
st.plotly_chart(fig, use_container_width=True, key='indice_ambiental_agrupado')

# =========================
# Tabela: Produção x Média do Local x Diferença (absoluta e relativa) - AGRUPADO
# =========================

# Monta DataFrame para a tabela agrupada (usando fazendaRef, nome, prod_sc_ha_corr, media_local_sc_ha)
df_tabela_indice_agrupado = df_indice_ambiental[[
    'fazendaRef', 'nome', 'prod_sc_ha_corr', 'media_local_sc_ha']].copy()
df_tabela_indice_agrupado['Diferença Absoluta (sc/ha)'] = df_tabela_indice_agrupado['prod_sc_ha_corr'] - \
    df_tabela_indice_agrupado['media_local_sc_ha']
df_tabela_indice_agrupado['Diferença Relativa (%)'] = 100 * df_tabela_indice_agrupado['Diferença Absoluta (sc/ha)'] / \
    df_tabela_indice_agrupado['media_local_sc_ha']

# Renomeia colunas para exibição
df_tabela_indice_agrupado = df_tabela_indice_agrupado.rename(columns={
    'fazendaRef': 'Local',
    'nome': 'Híbrido',
    'prod_sc_ha_corr': 'Produção (sc/ha)',
    'media_local_sc_ha': 'Média do Local (sc/ha)',
    'Diferença Absoluta (sc/ha)': 'Diferença Absoluta (sc/ha)',
    'Diferença Relativa (%)': 'Diferença Relativa (%)'
})  # type: ignore

# Formatação das casas decimais
formatar_agrupado = {
    'Produção (sc/ha)': '{:.1f}',
    'Média do Local (sc/ha)': '{:.1f}',
    'Diferença Absoluta (sc/ha)': '{:.1f}',
    'Diferença Relativa (%)': '{:.2f}'
}
for col, fmt in formatar_agrupado.items():
    df_tabela_indice_agrupado[col] = df_tabela_indice_agrupado[col].map(
        lambda x: fmt.format(x) if pd.notnull(x) else "")

# Exibe a tabela em um expander
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
        Tabela: Produção do Híbrido, Média do Local e Diferença (Agrupado)
    </div>
    """,
    unsafe_allow_html=True
)
with st.expander("Ver tabela detalhada por híbrido/local (agrupado)", expanded=False):
    st.markdown(
        """
        <div style="
            background-color: #f5f7fa;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.07);
            padding: 16px 18px 10px 18px;
            margin-bottom: 10px;
            margin-top: 0px;
            width: fit-content;
            display: inline-block;
        ">
            <b>Tabela Detalhada: Produção do Híbrido, Média do Local e Diferença (Agrupado)</b>
        </div>
        """,
        unsafe_allow_html=True
    )
    # AgGrid para tabela detalhada agrupada
    gb_detalhada_agrupado = GridOptionsBuilder.from_dataframe(
        df_tabela_indice_agrupado)
    colunas_formatar_agrupado = {
        'Produção (sc/ha)': 1,
        'Média do Local (sc/ha)': 1,
        'Diferença Absoluta (sc/ha)': 1,
        'Diferença Relativa (%)': 2
    }
    for col in df_tabela_indice_agrupado.columns:
        if col in colunas_formatar_agrupado:
            casas = colunas_formatar_agrupado[col]
            gb_detalhada_agrupado.configure_column(
                col,
                headerClass='ag-header-bold',
                menuTabs=['generalMenuTab', 'filterMenuTab', 'columnsMenuTab'],
                valueFormatter=f"value != null ? Number(value).toFixed({casas}) : ''"
            )
        else:
            gb_detalhada_agrupado.configure_column(
                col,
                headerClass='ag-header-bold',
                menuTabs=['generalMenuTab', 'filterMenuTab', 'columnsMenuTab']
            )
    gb_detalhada_agrupado.configure_default_column(
        editable=False, groupable=True, filter=True, resizable=True, cellStyle={'fontSize': '12px'})
    gb_detalhada_agrupado.configure_grid_options(headerHeight=30)
    grid_options_detalhada_agrupado = gb_detalhada_agrupado.build()
    custom_css = {
        ".ag-header-cell-label": {"font-weight": "bold", "font-size": "12px", "color": "black"},
        ".ag-cell": {"color": "black", "font-size": "12px"}
    }
    # Chave única e estática para garantir renderização imediata
    AgGrid(
        df_tabela_indice_agrupado,
        gridOptions=grid_options_detalhada_agrupado,
        enable_enterprise_modules=True,
        fit_columns_on_grid_load=False,
        theme="streamlit",
        height=400,
        reload_data=True,
        custom_css=custom_css,
        key="aggrid_indice_ambiental_detalhado_agrupado_static"
    )
    # Botão para exportar a tabela detalhada agrupada
    buffer_tabela_agrupado = io.BytesIO()
    df_tabela_indice_agrupado.to_excel(
        buffer_tabela_agrupado, index=False, engine='xlsxwriter')  # type: ignore
    buffer_tabela_agrupado.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel (Índice Ambiental Agrupado - Diferenças)",
        data=buffer_tabela_agrupado,
        file_name="indice_ambiental_agrupado_diferencas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Exibe a tabela transposta em um novo expander
    with st.expander("Ver tabela transposta (híbrido/local agrupado)", expanded=False):
        df_transposto = df_tabela_indice_agrupado.transpose().reset_index()
        df_transposto = df_transposto.rename(columns={"index": "Atributo"})
        AgGrid(
            df_transposto,
            enable_enterprise_modules=True,
            fit_columns_on_grid_load=False,
            theme="streamlit",
            height=400,
            reload_data=True,
            custom_css=custom_css,
            key="aggrid_indice_ambiental_agrupado_transposto"
        )

    # Tabela resumo por híbrido (médias) - AGRUPADO
    st.markdown(
        """
        <div style="
            background-color: #f5f7fa;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.07);
            padding: 16px 18px 10px 18px;
            margin-bottom: 18px;
            margin-top: 0px;
            width: fit-content;
            display: inline-block;
        ">
            <b>Médias das Diferenças por Híbrido (Agrupado)</b>
        </div>
        """,
        unsafe_allow_html=True
    )
    # Calcular resumo_hibrido_agrupado
    df_tabela_media_agrupado = df_indice_ambiental[[
        'nome', 'prod_sc_ha_corr', 'media_local_sc_ha']].copy()
    df_tabela_media_agrupado['Diferença Absoluta (sc/ha)'] = df_tabela_media_agrupado['prod_sc_ha_corr'] - \
        df_tabela_media_agrupado['media_local_sc_ha']
    df_tabela_media_agrupado['Diferença Relativa (%)'] = 100 * df_tabela_media_agrupado['Diferença Absoluta (sc/ha)'] / \
        df_tabela_media_agrupado['media_local_sc_ha']
    resumo_hibrido_agrupado = df_tabela_media_agrupado.groupby('nome').agg({
        'Diferença Absoluta (sc/ha)': 'mean',
        'Diferença Relativa (%)': 'mean'
    }).reset_index()
    resumo_hibrido_agrupado = resumo_hibrido_agrupado.rename(columns={
        'nome': 'Híbrido',
        'Diferença Absoluta (sc/ha)': 'Média Diferença Absoluta (sc/ha)',
        'Diferença Relativa (%)': 'Média Diferença Relativa (%)'
    })
    # Formatação de casas decimais para AgGrid
    gb_resumo_agrupado = GridOptionsBuilder.from_dataframe(
        resumo_hibrido_agrupado)
    gb_resumo_agrupado.configure_column('Média Diferença Absoluta (sc/ha)',
                                        valueFormatter="value != null ? Number(value).toFixed(2) : ''", headerClass='ag-header-bold')
    gb_resumo_agrupado.configure_column('Média Diferença Relativa (%)',
                                        valueFormatter="value != null ? Number(value).toFixed(2) : ''", headerClass='ag-header-bold')
    gb_resumo_agrupado.configure_column(
        'Híbrido', headerClass='ag-header-bold')
    gb_resumo_agrupado.configure_default_column(
        editable=False, groupable=True, filter=True, resizable=True, cellStyle={'fontSize': '12px'})
    gb_resumo_agrupado.configure_grid_options(headerHeight=30)
    grid_options_resumo_agrupado = gb_resumo_agrupado.build()
    # Altura dinâmica: 32px por linha + 32px para o cabeçalho (mínimo 200px, máximo 600px)
    num_linhas_agrupado = len(resumo_hibrido_agrupado)
    altura_agrupado = min(max(32 * (num_linhas_agrupado + 1), 200), 600)
    AgGrid(
        resumo_hibrido_agrupado,
        gridOptions=grid_options_resumo_agrupado,
        enable_enterprise_modules=True,
        fit_columns_on_grid_load=False,
        theme="streamlit",
        height=altura_agrupado,
        reload_data=True,
        custom_css=custom_css,
        key="aggrid_resumo_hibrido_agrupado"
    )
    # Botão para exportar a tabela resumo por híbrido agrupado
    buffer_resumo_agrupado = io.BytesIO()
    resumo_hibrido_agrupado.to_excel(
        buffer_resumo_agrupado, index=False, engine='xlsxwriter')  # type: ignore
    buffer_resumo_agrupado.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel (Resumo por Híbrido - Agrupado)",
        data=buffer_resumo_agrupado,
        file_name="resumo_diferencas_por_hibrido_agrupado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
