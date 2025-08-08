from st_aggrid import AgGrid, GridOptionsBuilder
import streamlit as st
import pandas as pd
import io
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
                Análise da Densidade de Plantas em Milho
            </h1>
            <h3 style="margin-top: 0; color: #e0e0e0; font-weight: 400; font-size: 1.2em;">
                Avaliação dos impactos da população de plantas sobre a produtividade e a uniformidade de desenvolvimento em diferentes ambientes
            </h3>
        </div>
        <!-- Se quiser adicionar um logo, descomente a linha abaixo e coloque o caminho correto -->
        <!-- <img src=\"https://link-para-logo.png\" style=\"height:64px; margin-left:24px;\" /> -->
    </div>
    """,
    unsafe_allow_html=True
)

# Verifica se o DataFrame tratado está disponível no session_state
if "df_avTratamentoMilhoDensidade" not in st.session_state:
    st.error("O DataFrame de tratamento de densidade não foi carregado. Volte para a página inicial e carregue os dados.")
    st.stop()

# Usar o DataFrame tratado já pronto do session_state
df_avTratamentoMilhoDensidade = st.session_state["df_avTratamentoMilhoDensidade"]

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
    ("populacao_av4", "Densidade", "densidade"),
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
    df_filtrado = df_avTratamentoMilhoDensidade.copy()
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
                if st.checkbox(str(opt), value=checked, key=f"{key}_{opt}"):
                    selecionadas.append(opt)
        st.session_state[f"sel_{key}"] = selecionadas
        if selecionadas:
            df_filtrado = df_filtrado[df_filtrado[col].isin(selecionadas)]

# =========================
# Visualização e exportação do DataFrame filtrado RETIRAR POSTERIORMENTE
# =========================
# st.markdown("### Dados Filtrados")
# st.dataframe(df_filtrado, use_container_width=True)

# buffer = io.BytesIO()
# df_filtrado.to_excel(buffer, index=False)
# buffer.seek(0)
# st.download_button(
#     label="⬇️ Baixar Excel (dados filtrados - densidade)",
#     data=buffer,
#     file_name="dados_filtrados_densidade.xlsx",
#     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# )

# =========================
# Criação do DataFrame principal de análise
# =========================
# O DataFrame df_analise_densidade será a base para todas as análises e visualizações

df_analise_densidade = df_filtrado.copy()

# Desfragmenta o DataFrame para evitar PerformanceWarning
df_analise_densidade = df_analise_densidade.copy()

# Cria a coluna index_tratamento concatenando indexTratamento com populacao_av4
df_analise_densidade['index_tratamento'] = df_analise_densidade['indexTratamento'].astype(
    str) + '_' + df_analise_densidade['populacao_av4'].astype(str)

# Mapeamento de colunas para visualização customizada
colunas_renomeadas = [
    ("indexTratamento", "index"),
    ("index_tratamento", "Index_Tratamento"),
    ("nome", "Híbrido"),
    ("populacao_av4", "Tratamento"),
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

# Cria o DataFrame de visualização customizada a partir do df_analise_densidade
colunas_existentes = [c for c in colunas if c in df_analise_densidade.columns]
df_analise_densidade_visualizacao = df_analise_densidade[colunas_existentes].rename(
    columns=novos_nomes)

# Exibe o DataFrame filtrado original
titulo_expander = "Dados Originais - Análise Densidade"
with st.expander(titulo_expander, expanded=False):
    st.dataframe(df_filtrado, use_container_width=True)

    # Botão para exportar em Excel o DataFrame filtrado original
    buffer_filtro = io.BytesIO()
    df_filtrado.to_excel(buffer_filtro, index=False)  # type: ignore
    buffer_filtro.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel (dados originais - análise densidade)",
        data=buffer_filtro,
        file_name="dados_originais_analise_densidade.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =========================
# Configuração visual e funcional do AgGrid
# =========================
gb = GridOptionsBuilder.from_dataframe(df_analise_densidade_visualizacao)

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

for col in df_analise_densidade_visualizacao.columns:
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
grid_options = gb.build()

# =========================
# Estilização customizada do AgGrid
# =========================
custom_css = {
    ".ag-header-cell-label": {
        "font-weight": "bold",
        "font-size": "12px",
        "color": "black"
    },
    ".ag-cell": {
        "color": "black",
        "font-size": "12px"
    }
}

# =========================
# Exibição do DataFrame customizado com AgGrid (base: df_analise_densidade)
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
        Resultados por Híbrido e Tratamento de Densidade de Plantas
    </div>
    """,
    unsafe_allow_html=True
)
AgGrid(
    df_analise_densidade_visualizacao,
    gridOptions=grid_options,
    enable_enterprise_modules=True,
    fit_columns_on_grid_load=False,
    theme="streamlit",
    height=500,
    reload_data=True,
    custom_css=custom_css
)

# Botão para exportar em Excel o DataFrame customizado
buffer_custom = io.BytesIO()
df_analise_densidade_visualizacao.to_excel(buffer_custom, index=False)
buffer_custom.seek(0)
st.download_button(
    label="⬇️ Baixar Excel (Análise de Densidade - Visualização Customizada)",
    data=buffer_custom,
    file_name="analise_densidade_customizada.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# Agrupamento por fazendaRef e pares de indexTratamento
# =========================
# Cria coluna de agrupamento para pares (101,201), (102,202), ..., (121,221)


def agrupa_index(idx):
    """Agrupa índices de tratamento em pares específicos baseado na densidade"""
    # Padrão: 101_50000 agrupa com 201_50000, 102_50000 com 202_50000, etc.
    pares = {}

    # Para cada densidade, cria os pares de 101-106 com 201-206
    densidades = [50000, 57000, 65000, 74000]
    for densidade in densidades:
        for i in range(101, 107):  # 101 a 106
            pares[f"{i+100}_{densidade}"] = f"{i}_{densidade}"

    return pares.get(idx, idx)


# Cria a coluna de agrupamento baseada na coluna index_tratamento
df_analise_densidade['indexTratamentoAgrupado'] = df_analise_densidade['index_tratamento'].apply(
    agrupa_index)

# Define as colunas de agrupamento e as colunas numéricas para média
group_cols = ['fazendaRef', 'indexTratamentoAgrupado']
colunas_numericas = df_analise_densidade.select_dtypes(
    include='number').columns.tolist()
colunas_numericas = [c for c in colunas_numericas if c not in [
    'indexTratamento', 'indexTratamentoAgrupado']]

# Substitui zeros por NaN nas colunas numéricas antes do agrupamento
df_analise_densidade[colunas_numericas] = df_analise_densidade[colunas_numericas].replace(
    0, np.nan)

# Realiza o agrupamento e calcula a média das colunas numéricas
df_analise_densidade_agrupado = (
    df_analise_densidade
    .groupby(group_cols, as_index=False)[colunas_numericas]
    .mean()
)

# Recupera o nome do híbrido para cada (fazendaRef, indexTratamentoAgrupado)
df_nome = (
    df_analise_densidade
    .groupby(['fazendaRef', 'indexTratamentoAgrupado'])['nome']
    .first()
    .reset_index()
)

# Junta o nome ao DataFrame agrupado
df_analise_densidade_agrupado = pd.merge(
    df_analise_densidade_agrupado,
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
    c for c in colunas_agrupado if c in df_analise_densidade_agrupado.columns]
df_analise_densidade_agrupado_visualizacao = df_analise_densidade_agrupado[colunas_agrupado_existentes].rename(
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
    df_analise_densidade_agrupado_visualizacao)

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

for col in df_analise_densidade_agrupado_visualizacao.columns:
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
    df_analise_densidade_agrupado_visualizacao,
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
df_analise_densidade_agrupado_visualizacao.to_excel(
    buffer_agrupado_vis, index=False)  # type: ignore
buffer_agrupado_vis.seek(0)
st.download_button(
    label="⬇️ Baixar Excel (Resumo da densidade)",
    data=buffer_agrupado_vis,
    file_name="densidade_producao.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# Visualização do DataFrame agrupado original (antes da seleção de colunas) Retirar depois
# =========================
# st.subheader("Dados Agrupados Originais - Análise de Densidade")
# st.markdown(
# """
# <div style="
#    background-color: #f0f8ff;
#    border-left: 6px solid #4682B4;
#    padding: 12px 18px;
#    margin-bottom: 12px;
#    border-radius: 6px;
#    font-size: 1.15em;
#    color: #2F4F4F;
#    font-weight: 600;
# ">
#    DataFrame Completo do Agrupamento - Todos os Dados
# </div>
# """,
# unsafe_allow_html=True
# )

# Exibe o DataFrame agrupado original completo
# st.dataframe(df_analise_densidade_agrupado, use_container_width=True)

# Botão para exportar em Excel o DataFrame agrupado original completo
# buffer_agrupado_original = io.BytesIO()
# df_analise_densidade_agrupado.to_excel(
# buffer_agrupado_original, index=False)  # type: ignore
# buffer_agrupado_original.seek(0)
# st.download_button(
# label="⬇️ Baixar Excel (Dados Agrupados Originais - Completo)",
# data=buffer_agrupado_original,
# file_name="dados_agrupados_originais_completo.xlsx",
# mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# )

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
        <h2 style="margin-bottom: 0.3em; color: #22223b; font-size: 22px; font-weight: 700;">📊 Distribuição da Produtividade de Milho (kg/ha) por Faixa de Densidade</h2>
        <h4 style="margin-top: 0; color: #4a4e69; font-weight: 500; font-size: 18px; line-height: 1.4;">
            Análise estatística detalhada da variação produtiva entre híbridos, localidades e condições de manejo para otimização do cultivo.
        </h4>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================
# Box Plot - Produção (kg/ha) para densidades até 50000
# =========================
with st.expander("📊 Box Plot - Densidades até 50.000 plantas/ha", expanded=False):
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
            Box Plot - Produção (kg/ha) para Densidades até 50.000 plantas/ha
        </div>
        """,
        unsafe_allow_html=True
    )

    # Filtra dados para densidades até 50000
    df_filtrado_50000 = df_analise_densidade_agrupado[
        df_analise_densidade_agrupado['numPlantas_ha'] <= 50000
    ].copy()

    if not df_filtrado_50000.empty:
        # Cria o box plot
        fig = go.Figure()

        # Adiciona o box plot
        fig.add_trace(go.Box(
            x=df_filtrado_50000['prod_kg_ha_corr'],
            name='Prod@13.5% (kg/ha)',
            marker_color='#0070C0',
            boxmean=True,  # Mostra a média
            boxpoints='outliers',  # Mostra outliers
            line=dict(color='#0070C0', width=2),
            fillcolor='rgba(0, 112, 192, 0.1)'
        ))

        # Calcula estatísticas
        serie = df_filtrado_50000['prod_kg_ha_corr']
        media = float(serie.mean())
        mediana = float(serie.median())  # type: ignore
        q1 = float(serie.quantile(0.25))  # type: ignore
        q3 = float(serie.quantile(0.75))  # type: ignore

        # Adiciona linhas de referência
        fig.add_vline(
            x=media,
            line_dash='dot',
            line_color='red',
            line_width=2,
            annotation_text=f"Média: {media:.1f} kg/ha",
            annotation_position="top right",
            annotation_font_color='red',
            annotation_font_size=14
        )

        fig.add_vline(
            x=mediana,
            line_dash='dash',
            line_color='green',
            line_width=2,
            annotation_text=f"Mediana: {mediana:.1f} kg/ha",
            annotation_position="bottom right",
            annotation_font_color='green',
            annotation_font_size=14
        )

        # Configura o layout
        fig.update_layout(
            title={
                'text': f'Box Plot - Produção @13.5% (kg/ha) - Densidades até 50.000 plantas/ha',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#22223b'}
            },
            xaxis_title='Produção @13.5% (kg/ha)',
            yaxis_title='',
            plot_bgcolor='#f5f7fa',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            yaxis=dict(
                tickfont=dict(size=14, color='black'),
                showgrid=False,
                zeroline=False
            ),
            showlegend=False,
            height=500,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        # Adiciona anotações com estatísticas
        fig.add_annotation(
            x=0.02, y=0.98,
            xref='paper', yref='paper',
            text=f"<b>Estatísticas:</b><br>Q1: {q1:.1f}<br>Q3: {q3:.1f}<br>IQR: {q3-q1:.1f}",
            showarrow=False,
            font=dict(size=12, color='black'),
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='gray',
            borderwidth=1
        )

        st.plotly_chart(fig, use_container_width=True)

        # Exibe estatísticas resumidas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Média",
                value=f"{media:.1f} kg/ha",
                delta=None
            )

        with col2:
            st.metric(
                label="Mediana",
                value=f"{mediana:.1f} kg/ha",
                delta=None
            )

        with col3:
            st.metric(
                label="Mínimo",
                value=f"{df_filtrado_50000['prod_kg_ha_corr'].min():.1f} kg/ha",
                delta=None
            )

        with col4:
            st.metric(
                label="Máximo",
                value=f"{df_filtrado_50000['prod_kg_ha_corr'].max():.1f} kg/ha",
                delta=None
            )

        # Botão para exportar dados filtrados
        buffer_boxplot = io.BytesIO()
        df_filtrado_50000.to_excel(buffer_boxplot, index=False)  # type: ignore
        buffer_boxplot.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Dados para Box Plot - até 50.000 plantas/ha)",
            data=buffer_boxplot,
            file_name="dados_boxplot_ate_50000_plantas_ha.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning(
            "Não há dados disponíveis para densidades até 50.000 plantas/ha com os filtros aplicados.")

# =========================
# Box Plot - Produção (kg/ha) para densidades entre 50000 e 57000
# =========================
with st.expander("📊 Box Plot - Densidades entre 50.000 e 57.000 plantas/ha", expanded=False):
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
            Box Plot - Produção (kg/ha) para Densidades entre 50.000 e 57.000 plantas/ha
        </div>
        """,
        unsafe_allow_html=True
    )

    # Filtra dados para densidades entre 50000 e 57000
    df_filtrado_50000_57000 = df_analise_densidade_agrupado[
        (df_analise_densidade_agrupado['numPlantas_ha'] > 50000) &
        (df_analise_densidade_agrupado['numPlantas_ha'] <= 57000)
    ].copy()

    if not df_filtrado_50000_57000.empty:
        # Cria o box plot
        fig = go.Figure()

        # Adiciona o box plot
        fig.add_trace(go.Box(
            x=df_filtrado_50000_57000['prod_kg_ha_corr'],
            name='Prod@13.5% (kg/ha)',
            marker_color='#4CAF50',  # Cor verde para diferenciar
            boxmean=True,  # Mostra a média
            boxpoints='outliers',  # Mostra outliers
            line=dict(color='#4CAF50', width=2),
            fillcolor='rgba(76, 175, 80, 0.1)'
        ))

        # Calcula estatísticas
        serie = df_filtrado_50000_57000['prod_kg_ha_corr']
        media = float(serie.mean())
        mediana = float(serie.median())  # type: ignore
        q1 = float(serie.quantile(0.25))  # type: ignore
        q3 = float(serie.quantile(0.75))  # type: ignore

        # Adiciona linhas de referência
        fig.add_vline(
            x=media,
            line_dash='dot',
            line_color='red',
            line_width=2,
            annotation_text=f"Média: {media:.1f} kg/ha",
            annotation_position="top right",
            annotation_font_color='red',
            annotation_font_size=14
        )

        fig.add_vline(
            x=mediana,
            line_dash='dash',
            line_color='green',
            line_width=2,
            annotation_text=f"Mediana: {mediana:.1f} kg/ha",
            annotation_position="bottom right",
            annotation_font_color='green',
            annotation_font_size=14
        )

        # Configura o layout
        fig.update_layout(
            title={
                'text': f'Box Plot - Produção @13.5% (kg/ha) - Densidades entre 50.000 e 57.000 plantas/ha',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#22223b'}
            },
            xaxis_title='Produção @13.5% (kg/ha)',
            yaxis_title='',
            plot_bgcolor='#f5f7fa',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            yaxis=dict(
                tickfont=dict(size=14, color='black'),
                showgrid=False,
                zeroline=False
            ),
            showlegend=False,
            height=500,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        # Adiciona anotações com estatísticas
        fig.add_annotation(
            x=0.02, y=0.98,
            xref='paper', yref='paper',
            text=f"<b>Estatísticas:</b><br>Q1: {q1:.1f}<br>Q3: {q3:.1f}<br>IQR: {q3-q1:.1f}",
            showarrow=False,
            font=dict(size=12, color='black'),
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='gray',
            borderwidth=1
        )

        st.plotly_chart(fig, use_container_width=True)

        # Exibe estatísticas resumidas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Média",
                value=f"{media:.1f} kg/ha",
                delta=None
            )

        with col2:
            st.metric(
                label="Mediana",
                value=f"{mediana:.1f} kg/ha",
                delta=None
            )

        with col3:
            st.metric(
                label="Mínimo",
                value=f"{df_filtrado_50000_57000['prod_kg_ha_corr'].min():.1f} kg/ha",
                delta=None
            )

        with col4:
            st.metric(
                label="Máximo",
                value=f"{df_filtrado_50000_57000['prod_kg_ha_corr'].max():.1f} kg/ha",
                delta=None
            )

        # Botão para exportar dados filtrados
        buffer_boxplot_50000_57000 = io.BytesIO()
        df_filtrado_50000_57000.to_excel(
            buffer_boxplot_50000_57000, index=False)  # type: ignore
        buffer_boxplot_50000_57000.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Dados para Box Plot - 50.000 a 57.000 plantas/ha)",
            data=buffer_boxplot_50000_57000,
            file_name="dados_boxplot_50000_a_57000_plantas_ha.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning(
            "Não há dados disponíveis para densidades entre 50.000 e 57.000 plantas/ha com os filtros aplicados.")

# =========================
# Box Plot - Produção (kg/ha) para densidades entre 57000 e 65000
# =========================
with st.expander("📊 Box Plot - Densidades entre 57.000 e 65.000 plantas/ha", expanded=False):
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
            Box Plot - Produção (kg/ha) para Densidades entre 57.000 e 65.000 plantas/ha
        </div>
        """,
        unsafe_allow_html=True
    )

    # Filtra dados para densidades entre 57000 e 65000
    df_filtrado_57000_65000 = df_analise_densidade_agrupado[
        (df_analise_densidade_agrupado['numPlantas_ha'] > 57000) &
        (df_analise_densidade_agrupado['numPlantas_ha'] <= 65000)
    ].copy()

    if not df_filtrado_57000_65000.empty:
        # Cria o box plot
        fig = go.Figure()

        # Adiciona o box plot
        fig.add_trace(go.Box(
            x=df_filtrado_57000_65000['prod_kg_ha_corr'],
            name='Prod@13.5% (kg/ha)',
            marker_color='#FF9800',  # Cor laranja para diferenciar
            boxmean=True,  # Mostra a média
            boxpoints='outliers',  # Mostra outliers
            line=dict(color='#FF9800', width=2),
            fillcolor='rgba(255, 152, 0, 0.1)'
        ))

        # Calcula estatísticas
        serie = df_filtrado_57000_65000['prod_kg_ha_corr']
        media = float(serie.mean())
        mediana = float(serie.median())  # type: ignore
        q1 = float(serie.quantile(0.25))  # type: ignore
        q3 = float(serie.quantile(0.75))  # type: ignore

        # Adiciona linhas de referência
        fig.add_vline(
            x=media,
            line_dash='dot',
            line_color='red',
            line_width=2,
            annotation_text=f"Média: {media:.1f} kg/ha",
            annotation_position="top right",
            annotation_font_color='red',
            annotation_font_size=14
        )

        fig.add_vline(
            x=mediana,
            line_dash='dash',
            line_color='green',
            line_width=2,
            annotation_text=f"Mediana: {mediana:.1f} kg/ha",
            annotation_position="bottom right",
            annotation_font_color='green',
            annotation_font_size=14
        )

        # Configura o layout
        fig.update_layout(
            title={
                'text': f'Box Plot - Produção @13.5% (kg/ha) - Densidades entre 57.000 e 65.000 plantas/ha',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#22223b'}
            },
            xaxis_title='Produção @13.5% (kg/ha)',
            yaxis_title='',
            plot_bgcolor='#f5f7fa',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            yaxis=dict(
                tickfont=dict(size=14, color='black'),
                showgrid=False,
                zeroline=False
            ),
            showlegend=False,
            height=500,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        # Adiciona anotações com estatísticas
        fig.add_annotation(
            x=0.02, y=0.98,
            xref='paper', yref='paper',
            text=f"<b>Estatísticas:</b><br>Q1: {q1:.1f}<br>Q3: {q3:.1f}<br>IQR: {q3-q1:.1f}",
            showarrow=False,
            font=dict(size=12, color='black'),
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='gray',
            borderwidth=1
        )

        st.plotly_chart(fig, use_container_width=True)

        # Exibe estatísticas resumidas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Média",
                value=f"{media:.1f} kg/ha",
                delta=None
            )

        with col2:
            st.metric(
                label="Mediana",
                value=f"{mediana:.1f} kg/ha",
                delta=None
            )

        with col3:
            st.metric(
                label="Mínimo",
                value=f"{df_filtrado_57000_65000['prod_kg_ha_corr'].min():.1f} kg/ha",
                delta=None
            )

        with col4:
            st.metric(
                label="Máximo",
                value=f"{df_filtrado_57000_65000['prod_kg_ha_corr'].max():.1f} kg/ha",
                delta=None
            )

        # Botão para exportar dados filtrados
        buffer_boxplot_57000_65000 = io.BytesIO()
        df_filtrado_57000_65000.to_excel(
            buffer_boxplot_57000_65000, index=False)  # type: ignore
        buffer_boxplot_57000_65000.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Dados para Box Plot - 57.000 a 65.000 plantas/ha)",
            data=buffer_boxplot_57000_65000,
            file_name="dados_boxplot_57000_a_65000_plantas_ha.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning(
            "Não há dados disponíveis para densidades entre 57.000 e 65.000 plantas/ha com os filtros aplicados.")

# =========================
# Box Plot - Produção (kg/ha) para densidades entre 65000 e 74000
# =========================
with st.expander("📊 Box Plot - Densidades entre 65.000 e 74.000 plantas/ha", expanded=False):
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
            Box Plot - Produção (kg/ha) para Densidades entre 65.000 e 74.000 plantas/ha
        </div>
        """,
        unsafe_allow_html=True
    )

    # Filtra dados para densidades entre 65000 e 74000
    df_filtrado_65000_74000 = df_analise_densidade_agrupado[
        (df_analise_densidade_agrupado['numPlantas_ha'] > 65000) &
        (df_analise_densidade_agrupado['numPlantas_ha'] <= 74000)
    ].copy()

    if not df_filtrado_65000_74000.empty:
        # Cria o box plot
        fig = go.Figure()

        # Adiciona o box plot
        fig.add_trace(go.Box(
            x=df_filtrado_65000_74000['prod_kg_ha_corr'],
            name='Prod@13.5% (kg/ha)',
            marker_color='#E91E63',  # Cor rosa/magenta para diferenciar
            boxmean=True,  # Mostra a média
            boxpoints='outliers',  # Mostra outliers
            line=dict(color='#E91E63', width=2),
            fillcolor='rgba(233, 30, 99, 0.1)'
        ))

        # Calcula estatísticas
        serie = df_filtrado_65000_74000['prod_kg_ha_corr']
        media = float(serie.mean())
        mediana = float(serie.median())  # type: ignore
        q1 = float(serie.quantile(0.25))  # type: ignore
        q3 = float(serie.quantile(0.75))  # type: ignore

        # Adiciona linhas de referência
        fig.add_vline(
            x=media,
            line_dash='dot',
            line_color='red',
            line_width=2,
            annotation_text=f"Média: {media:.1f} kg/ha",
            annotation_position="top right",
            annotation_font_color='red',
            annotation_font_size=14
        )

        fig.add_vline(
            x=mediana,
            line_dash='dash',
            line_color='green',
            line_width=2,
            annotation_text=f"Mediana: {mediana:.1f} kg/ha",
            annotation_position="bottom right",
            annotation_font_color='green',
            annotation_font_size=14
        )

        # Configura o layout
        fig.update_layout(
            title={
                'text': f'Box Plot - Produção @13.5% (kg/ha) - Densidades entre 65.000 e 74.000 plantas/ha',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#22223b'}
            },
            xaxis_title='Produção @13.5% (kg/ha)',
            yaxis_title='',
            plot_bgcolor='#f5f7fa',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            yaxis=dict(
                tickfont=dict(size=14, color='black'),
                showgrid=False,
                zeroline=False
            ),
            showlegend=False,
            height=500,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        # Adiciona anotações com estatísticas
        fig.add_annotation(
            x=0.02, y=0.98,
            xref='paper', yref='paper',
            text=f"<b>Estatísticas:</b><br>Q1: {q1:.1f}<br>Q3: {q3:.1f}<br>IQR: {q3-q1:.1f}",
            showarrow=False,
            font=dict(size=12, color='black'),
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='gray',
            borderwidth=1
        )

        st.plotly_chart(fig, use_container_width=True)

        # Exibe estatísticas resumidas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Média",
                value=f"{media:.1f} kg/ha",
                delta=None
            )

        with col2:
            st.metric(
                label="Mediana",
                value=f"{mediana:.1f} kg/ha",
                delta=None
            )

        with col3:
            st.metric(
                label="Mínimo",
                value=f"{df_filtrado_65000_74000['prod_kg_ha_corr'].min():.1f} kg/ha",
                delta=None
            )

        with col4:
            st.metric(
                label="Máximo",
                value=f"{df_filtrado_65000_74000['prod_kg_ha_corr'].max():.1f} kg/ha",
                delta=None
            )

        # Botão para exportar dados filtrados
        buffer_boxplot_65000_74000 = io.BytesIO()
        df_filtrado_65000_74000.to_excel(
            buffer_boxplot_65000_74000, index=False)  # type: ignore
        buffer_boxplot_65000_74000.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Dados para Box Plot - 65.000 a 74.000 plantas/ha)",
            data=buffer_boxplot_65000_74000,
            file_name="dados_boxplot_65000_a_74000_plantas_ha.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning(
            "Não há dados disponíveis para densidades entre 65.000 e 74.000 plantas/ha com os filtros aplicados.")

# =========================
# Box Plot - Produção (kg/ha) para densidades maiores que 74000
# =========================
with st.expander("📊 Box Plot - Densidades maiores que 74.000 plantas/ha", expanded=False):
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
            Box Plot - Produção (kg/ha) para Densidades maiores que 74.000 plantas/ha
        </div>
        """,
        unsafe_allow_html=True
    )

    # Filtra dados para densidades maiores que 74000
    df_filtrado_maior_74000 = df_analise_densidade_agrupado[
        df_analise_densidade_agrupado['numPlantas_ha'] > 74000
    ].copy()

    if not df_filtrado_maior_74000.empty:
        # Cria o box plot
        fig = go.Figure()

        # Adiciona o box plot
        fig.add_trace(go.Box(
            x=df_filtrado_maior_74000['prod_kg_ha_corr'],
            name='Prod@13.5% (kg/ha)',
            marker_color='#9C27B0',  # Cor roxa para diferenciar
            boxmean=True,  # Mostra a média
            boxpoints='outliers',  # Mostra outliers
            line=dict(color='#9C27B0', width=2),
            fillcolor='rgba(156, 39, 176, 0.1)'
        ))

        # Calcula estatísticas
        serie = df_filtrado_maior_74000['prod_kg_ha_corr']
        media = float(serie.mean())
        mediana = float(serie.median())  # type: ignore
        q1 = float(serie.quantile(0.25))  # type: ignore
        q3 = float(serie.quantile(0.75))  # type: ignore

        # Adiciona linhas de referência
        fig.add_vline(
            x=media,
            line_dash='dot',
            line_color='red',
            line_width=2,
            annotation_text=f"Média: {media:.1f} kg/ha",
            annotation_position="top right",
            annotation_font_color='red',
            annotation_font_size=14
        )

        fig.add_vline(
            x=mediana,
            line_dash='dash',
            line_color='green',
            line_width=2,
            annotation_text=f"Mediana: {mediana:.1f} kg/ha",
            annotation_position="bottom right",
            annotation_font_color='green',
            annotation_font_size=14
        )

        # Configura o layout
        fig.update_layout(
            title={
                'text': f'Box Plot - Produção @13.5% (kg/ha) - Densidades maiores que 74.000 plantas/ha',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#22223b'}
            },
            xaxis_title='Produção @13.5% (kg/ha)',
            yaxis_title='',
            plot_bgcolor='#f5f7fa',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            yaxis=dict(
                tickfont=dict(size=14, color='black'),
                showgrid=False,
                zeroline=False
            ),
            showlegend=False,
            height=500,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        # Adiciona anotações com estatísticas
        fig.add_annotation(
            x=0.02, y=0.98,
            xref='paper', yref='paper',
            text=f"<b>Estatísticas:</b><br>Q1: {q1:.1f}<br>Q3: {q3:.1f}<br>IQR: {q3-q1:.1f}",
            showarrow=False,
            font=dict(size=12, color='black'),
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='gray',
            borderwidth=1
        )

        st.plotly_chart(fig, use_container_width=True)

        # Exibe estatísticas resumidas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Média",
                value=f"{media:.1f} kg/ha",
                delta=None
            )

        with col2:
            st.metric(
                label="Mediana",
                value=f"{mediana:.1f} kg/ha",
                delta=None
            )

        with col3:
            st.metric(
                label="Mínimo",
                value=f"{df_filtrado_maior_74000['prod_kg_ha_corr'].min():.1f} kg/ha",
                delta=None
            )

        with col4:
            st.metric(
                label="Máximo",
                value=f"{df_filtrado_maior_74000['prod_kg_ha_corr'].max():.1f} kg/ha",
                delta=None
            )

        # Botão para exportar dados filtrados
        buffer_boxplot_maior_74000 = io.BytesIO()
        df_filtrado_maior_74000.to_excel(
            buffer_boxplot_maior_74000, index=False)  # type: ignore
        buffer_boxplot_maior_74000.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Dados para Box Plot - maiores que 74.000 plantas/ha)",
            data=buffer_boxplot_maior_74000,
            file_name="dados_boxplot_maior_74000_plantas_ha.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning(
            "Não há dados disponíveis para densidades maiores que 74.000 plantas/ha com os filtros aplicados.")

# =========================
# Box Plot com Facetas - Todos os dados de densidade
# =========================
with st.expander("📊 Box Plot - Todas as Faixas de Densidade", expanded=False):
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
            Box Plot Todas as Faixas de Densidade - Produção (kg/ha) por Faixa de Densidade
        </div>
        """,
        unsafe_allow_html=True
    )

    # Cria DataFrame com todas as faixas de densidade
    df_todas_faixas = df_analise_densidade_agrupado.copy()

    # Cria coluna de faixa de densidade
    def definir_faixa_densidade(densidade):
        if densidade < 50000:
            return "< 50.000"
        elif 50000 <= densidade <= 57000:
            return "50.001 - 57.000"
        elif 57001 <= densidade <= 65000:
            return "57.001 - 65.000"
        elif 65001 <= densidade <= 74000:
            return "65.001 - 74.000"
        else:
            return "> 74.000"

    df_todas_faixas['faixa_densidade'] = df_todas_faixas['numPlantas_ha'].apply(
        definir_faixa_densidade)

    # Cria coluna auxiliar para ordenação
    def criar_ordem_faixa(faixa):
        if faixa == "< 50.000":
            return 1
        elif faixa == "50.001 - 57.000":
            return 2
        elif faixa == "57.001 - 65.000":
            return 3
        elif faixa == "65.001 - 74.000":
            return 4
        else:  # "> 74.000"
            return 5

    df_todas_faixas['ordem_faixa'] = df_todas_faixas['faixa_densidade'].apply(
        criar_ordem_faixa)

    # Ordena o DataFrame pela coluna auxiliar
    df_todas_faixas = df_todas_faixas.sort_values('ordem_faixa')

    # Filtra apenas dados com produção válida
    df_todas_faixas_filtrado = df_todas_faixas[df_todas_faixas['prod_kg_ha_corr'].notna(
    )].copy()

    if not df_todas_faixas_filtrado.empty:
        # Cria o box plot com facetas usando Plotly Express
        fig = px.box(
            df_todas_faixas_filtrado,
            x='faixa_densidade',
            y='prod_kg_ha_corr',
            color='faixa_densidade',
            title='Box Plot - Produção @13.5% (kg/ha) por Faixa de Densidade',
            labels={
                'faixa_densidade': 'Faixa de Densidade (plantas/ha)',
                'prod_kg_ha_corr': 'Produção @13.5% (kg/ha)'
            },
            color_discrete_map={
                "< 50.000": "#0070C0",
                "50.001 - 57.000": "#4CAF50",
                "57.001 - 65.000": "#FF9800",
                "65.001 - 74.000": "#E91E63",
                "> 74.000": "#9C27B0"
            },
            category_orders={'faixa_densidade': [
                "< 50.000", "50.001 - 57.000", "57.001 - 65.000", "65.001 - 74.000", "> 74.000"]}
        )

        # Configura o layout
        fig.update_layout(
            title={
                'text': f'Box Plot - Produção @13.5% (kg/ha) por Faixa de Densidade<br><sub>Total de observações: {len(df_todas_faixas_filtrado)}</sub>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#22223b'}
            },
            plot_bgcolor='#f5f7fa',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            yaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            showlegend=False,
            height=600,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        # Adiciona estatísticas por faixa
        stats_por_faixa = df_todas_faixas_filtrado.groupby('faixa_densidade')['prod_kg_ha_corr'].agg([
            'count', 'mean', 'median', 'std', 'min', 'max'
        ]).round(1)

        st.plotly_chart(fig, use_container_width=True)

        # Exibe estatísticas resumidas por faixa
        st.markdown("### Estatísticas por Faixa de Densidade")

        # Renomeia colunas para visualização
        stats_por_faixa = stats_por_faixa.rename(columns={  # type: ignore
            'count': 'N',
            'mean': 'Média',
            'median': 'Mediana',
            'std': 'Desvio Padrão',
            'min': 'Mínimo',
            'max': 'Máximo'
        })

        # Configuração do AgGrid para estatísticas por faixa
        gb_stats = GridOptionsBuilder.from_dataframe(stats_por_faixa)

        # Configuração de casas decimais para colunas numéricas
        colunas_formatar_stats = {
            "Média": 1,
            "Mediana": 1,
            "Desvio Padrão": 1,
            "Mínimo": 1,
            "Máximo": 1
        }

        for col in stats_por_faixa.columns:
            if col in colunas_formatar_stats:
                casas = colunas_formatar_stats[col]
                gb_stats.configure_column(
                    col,
                    headerClass='ag-header-bold',
                    menuTabs=['generalMenuTab',
                              'filterMenuTab', 'columnsMenuTab'],
                    valueFormatter=f"value != null ? value.toFixed({casas}) : ''"
                )
            else:
                gb_stats.configure_column(
                    col,
                    headerClass='ag-header-bold',
                    menuTabs=['generalMenuTab',
                              'filterMenuTab', 'columnsMenuTab']
                )

        # Configura opções padrão para todas as colunas
        gb_stats.configure_default_column(editable=False, groupable=True,
                                          filter=True, resizable=True, cellStyle={'fontSize': '12px'})
        gb_stats.configure_grid_options(headerHeight=30)
        grid_options_stats = gb_stats.build()

        # Exibe tabela de estatísticas com AgGrid
        AgGrid(
            stats_por_faixa,
            gridOptions=grid_options_stats,
            enable_enterprise_modules=True,
            fit_columns_on_grid_load=False,
            theme="streamlit",
            height=300,
            reload_data=True,
            custom_css=custom_css
        )

        # Botão para exportar dados com facetas
        buffer_facetas = io.BytesIO()
        df_todas_faixas_filtrado.to_excel(
            buffer_facetas, index=False)  # type: ignore
        buffer_facetas.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Dados com Facetas por Faixa de Densidade)",
            data=buffer_facetas,
            file_name="dados_boxplot_facetas_por_faixa_densidade.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Botão para exportar estatísticas por faixa
        buffer_stats_faixas = io.BytesIO()
        stats_por_faixa.to_excel(buffer_stats_faixas)  # type: ignore
        buffer_stats_faixas.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Estatísticas por Faixa de Densidade)",
            data=buffer_stats_faixas,
            file_name="estatisticas_por_faixa_densidade.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning(
            "Não há dados válidos disponíveis para criar o box plot com facetas.")

# =========================
# NOVA SEÇÃO: Box Plots para Produção em Sacas por Hectare (prod_sc_ha_corr)
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
        <h2 style="margin-bottom: 0.3em; color: #22223b; font-size: 22px; font-weight: 700;">📊 Distribuição da Produtividade de Milho (sc/ha) por Faixa de Densidade</h2>
        <h4 style="margin-top: 0; color: #4a4e69; font-weight: 500; font-size: 18px; line-height: 1.4;">
            Análise estatística detalhada da variação produtiva entre híbridos, localidades e condições de manejo para otimização do cultivo.
        </h4>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================
# Box Plot - Produção (sc/ha) para densidades até 50000
# =========================
with st.expander("📊 Box Plot - Densidades até 50.000 plantas/ha (Sacas/ha)", expanded=False):
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
            Box Plot - Produção (sc/ha) para Densidades até 50.000 plantas/ha
        </div>
        """,
        unsafe_allow_html=True
    )

    # Filtra dados para densidades até 50000
    df_filtrado_50000_sc = df_analise_densidade_agrupado[
        df_analise_densidade_agrupado['numPlantas_ha'] <= 50000
    ].copy()

    if not df_filtrado_50000_sc.empty:
        # Cria o box plot
        fig = go.Figure()

        # Adiciona o box plot
        fig.add_trace(go.Box(
            x=df_filtrado_50000_sc['prod_sc_ha_corr'],
            name='Prod@13.5% (sc/ha)',
            marker_color='#0070C0',
            boxmean=True,  # Mostra a média
            boxpoints='outliers',  # Mostra outliers
            line=dict(color='#0070C0', width=2),
            fillcolor='rgba(0, 112, 192, 0.1)'
        ))

        # Calcula estatísticas
        serie = df_filtrado_50000_sc['prod_sc_ha_corr']
        media = float(serie.mean())
        mediana = float(serie.median())  # type: ignore
        q1 = float(serie.quantile(0.25))  # type: ignore
        q3 = float(serie.quantile(0.75))  # type: ignore

        # Adiciona linhas de referência
        fig.add_vline(
            x=media,
            line_dash='dot',
            line_color='red',
            line_width=2,
            annotation_text=f"Média: {media:.1f} sc/ha",
            annotation_position="top right",
            annotation_font_color='red',
            annotation_font_size=14
        )

        fig.add_vline(
            x=mediana,
            line_dash='dash',
            line_color='green',
            line_width=2,
            annotation_text=f"Mediana: {mediana:.1f} sc/ha",
            annotation_position="bottom right",
            annotation_font_color='green',
            annotation_font_size=14
        )

        # Configura o layout
        fig.update_layout(
            title={
                'text': f'Box Plot - Produção @13.5% (sc/ha) - Densidades até 50.000 plantas/ha',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black'}
            },
            xaxis_title='Produção @13.5% (sc/ha)',
            yaxis_title='',
            plot_bgcolor='#f5f7fa',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            yaxis=dict(
                tickfont=dict(size=14, color='black'),
                showgrid=False,
                zeroline=False
            ),
            showlegend=False,
            height=500,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        # Adiciona anotações com estatísticas
        fig.add_annotation(
            x=0.02, y=0.98,
            xref='paper', yref='paper',
            text=f"<b>Estatísticas:</b><br>Q1: {q1:.1f}<br>Q3: {q3:.1f}<br>IQR: {q3-q1:.1f}",
            showarrow=False,
            font=dict(size=12, color='black'),
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='gray',
            borderwidth=1
        )

        st.plotly_chart(fig, use_container_width=True)

        # Exibe estatísticas resumidas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Média",
                value=f"{media:.1f} sc/ha",
                delta=None
            )

        with col2:
            st.metric(
                label="Mediana",
                value=f"{mediana:.1f} sc/ha",
                delta=None
            )

        with col3:
            st.metric(
                label="Mínimo",
                value=f"{df_filtrado_50000_sc['prod_sc_ha_corr'].min():.1f} sc/ha",
                delta=None
            )

        with col4:
            st.metric(
                label="Máximo",
                value=f"{df_filtrado_50000_sc['prod_sc_ha_corr'].max():.1f} sc/ha",
                delta=None
            )

        # Botão para exportar dados filtrados
        buffer_boxplot_sc = io.BytesIO()
        df_filtrado_50000_sc.to_excel(
            buffer_boxplot_sc, index=False)  # type: ignore
        buffer_boxplot_sc.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Dados para Box Plot - até 50.000 plantas/ha - Sacas)",
            data=buffer_boxplot_sc,
            file_name="dados_boxplot_ate_50000_plantas_ha_sacas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning(
            "Não há dados disponíveis para densidades até 50.000 plantas/ha com os filtros aplicados.")

# =========================
# Box Plot - Produção (sc/ha) para densidades entre 50000 e 57000
# =========================
with st.expander("📊 Box Plot - Densidades entre 50.000 e 57.000 plantas/ha (Sacas/ha)", expanded=False):
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
            Box Plot - Produção (sc/ha) para Densidades entre 50.000 e 57.000 plantas/ha
        </div>
        """,
        unsafe_allow_html=True
    )

    # Filtra dados para densidades entre 50000 e 57000
    df_filtrado_50000_57000_sc = df_analise_densidade_agrupado[
        (df_analise_densidade_agrupado['numPlantas_ha'] > 50000) &
        (df_analise_densidade_agrupado['numPlantas_ha'] <= 57000)
    ].copy()

    if not df_filtrado_50000_57000_sc.empty:
        # Cria o box plot
        fig = go.Figure()

        # Adiciona o box plot
        fig.add_trace(go.Box(
            x=df_filtrado_50000_57000_sc['prod_sc_ha_corr'],
            name='Prod@13.5% (sc/ha)',
            marker_color='#4CAF50',  # Cor verde para diferenciar
            boxmean=True,  # Mostra a média
            boxpoints='outliers',  # Mostra outliers
            line=dict(color='#4CAF50', width=2),
            fillcolor='rgba(76, 175, 80, 0.1)'
        ))

        # Calcula estatísticas
        serie = df_filtrado_50000_57000_sc['prod_sc_ha_corr']
        media = float(serie.mean())
        mediana = float(serie.median())  # type: ignore
        q1 = float(serie.quantile(0.25))  # type: ignore
        q3 = float(serie.quantile(0.75))  # type: ignore

        # Adiciona linhas de referência
        fig.add_vline(
            x=media,
            line_dash='dot',
            line_color='red',
            line_width=2,
            annotation_text=f"Média: {media:.1f} sc/ha",
            annotation_position="top right",
            annotation_font_color='red',
            annotation_font_size=14
        )

        fig.add_vline(
            x=mediana,
            line_dash='dash',
            line_color='green',
            line_width=2,
            annotation_text=f"Mediana: {mediana:.1f} sc/ha",
            annotation_position="bottom right",
            annotation_font_color='green',
            annotation_font_size=14
        )

        # Configura o layout
        fig.update_layout(
            title={
                'text': f'Box Plot - Produção @13.5% (sc/ha) - Densidades entre 50.000 e 57.000 plantas/ha',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black'}
            },
            xaxis_title='Produção @13.5% (sc/ha)',
            yaxis_title='',
            plot_bgcolor='#f5f7fa',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            yaxis=dict(
                tickfont=dict(size=14, color='black'),
                showgrid=False,
                zeroline=False
            ),
            showlegend=False,
            height=500,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        # Adiciona anotações com estatísticas
        fig.add_annotation(
            x=0.02, y=0.98,
            xref='paper', yref='paper',
            text=f"<b>Estatísticas:</b><br>Q1: {q1:.1f}<br>Q3: {q3:.1f}<br>IQR: {q3-q1:.1f}",
            showarrow=False,
            font=dict(size=12, color='black'),
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='gray',
            borderwidth=1
        )

        st.plotly_chart(fig, use_container_width=True)

        # Exibe estatísticas resumidas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Média",
                value=f"{media:.1f} sc/ha",
                delta=None
            )

        with col2:
            st.metric(
                label="Mediana",
                value=f"{mediana:.1f} sc/ha",
                delta=None
            )

        with col3:
            st.metric(
                label="Mínimo",
                value=f"{df_filtrado_50000_57000_sc['prod_sc_ha_corr'].min():.1f} sc/ha",
                delta=None
            )

        with col4:
            st.metric(
                label="Máximo",
                value=f"{df_filtrado_50000_57000_sc['prod_sc_ha_corr'].max():.1f} sc/ha",
                delta=None
            )

        # Botão para exportar dados filtrados
        buffer_boxplot_50000_57000_sc = io.BytesIO()
        df_filtrado_50000_57000_sc.to_excel(
            buffer_boxplot_50000_57000_sc, index=False)  # type: ignore
        buffer_boxplot_50000_57000_sc.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Dados para Box Plot - 50.000 a 57.000 plantas/ha - Sacas)",
            data=buffer_boxplot_50000_57000_sc,
            file_name="dados_boxplot_50000_a_57000_plantas_ha_sacas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning(
            "Não há dados disponíveis para densidades entre 50.000 e 57.000 plantas/ha com os filtros aplicados.")

# =========================
# Box Plot - Produção (sc/ha) para densidades entre 57000 e 65000
# =========================
with st.expander("📊 Box Plot - Densidades entre 57.000 e 65.000 plantas/ha (Sacas/ha)", expanded=False):
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
            Box Plot - Produção (sc/ha) para Densidades entre 57.000 e 65.000 plantas/ha
        </div>
        """,
        unsafe_allow_html=True
    )

    # Filtra dados para densidades entre 57000 e 65000
    df_filtrado_57000_65000_sc = df_analise_densidade_agrupado[
        (df_analise_densidade_agrupado['numPlantas_ha'] > 57000) &
        (df_analise_densidade_agrupado['numPlantas_ha'] <= 65000)
    ].copy()

    if not df_filtrado_57000_65000_sc.empty:
        # Cria o box plot
        fig = go.Figure()

        # Adiciona o box plot
        fig.add_trace(go.Box(
            x=df_filtrado_57000_65000_sc['prod_sc_ha_corr'],
            name='Prod@13.5% (sc/ha)',
            marker_color='#FF9800',  # Cor laranja para diferenciar
            boxmean=True,  # Mostra a média
            boxpoints='outliers',  # Mostra outliers
            line=dict(color='#FF9800', width=2),
            fillcolor='rgba(255, 152, 0, 0.1)'
        ))

        # Calcula estatísticas
        serie = df_filtrado_57000_65000_sc['prod_sc_ha_corr']
        media = float(serie.mean())
        mediana = float(serie.median())  # type: ignore
        q1 = float(serie.quantile(0.25))  # type: ignore
        q3 = float(serie.quantile(0.75))  # type: ignore

        # Adiciona linhas de referência
        fig.add_vline(
            x=media,
            line_dash='dot',
            line_color='red',
            line_width=2,
            annotation_text=f"Média: {media:.1f} sc/ha",
            annotation_position="top right",
            annotation_font_color='red',
            annotation_font_size=14
        )

        fig.add_vline(
            x=mediana,
            line_dash='dash',
            line_color='green',
            line_width=2,
            annotation_text=f"Mediana: {mediana:.1f} sc/ha",
            annotation_position="bottom right",
            annotation_font_color='green',
            annotation_font_size=14
        )

        # Configura o layout
        fig.update_layout(
            title={
                'text': f'Box Plot - Produção @13.5% (sc/ha) - Densidades entre 57.000 e 65.000 plantas/ha',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black'}
            },
            xaxis_title='Produção @13.5% (sc/ha)',
            yaxis_title='',
            plot_bgcolor='#f5f7fa',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            yaxis=dict(
                tickfont=dict(size=14, color='black'),
                showgrid=False,
                zeroline=False
            ),
            showlegend=False,
            height=500,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        # Adiciona anotações com estatísticas
        fig.add_annotation(
            x=0.02, y=0.98,
            xref='paper', yref='paper',
            text=f"<b>Estatísticas:</b><br>Q1: {q1:.1f}<br>Q3: {q3:.1f}<br>IQR: {q3-q1:.1f}",
            showarrow=False,
            font=dict(size=12, color='black'),
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='gray',
            borderwidth=1
        )

        st.plotly_chart(fig, use_container_width=True)

        # Exibe estatísticas resumidas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Média",
                value=f"{media:.1f} sc/ha",
                delta=None
            )

        with col2:
            st.metric(
                label="Mediana",
                value=f"{mediana:.1f} sc/ha",
                delta=None
            )

        with col3:
            st.metric(
                label="Mínimo",
                value=f"{df_filtrado_57000_65000_sc['prod_sc_ha_corr'].min():.1f} sc/ha",
                delta=None
            )

        with col4:
            st.metric(
                label="Máximo",
                value=f"{df_filtrado_57000_65000_sc['prod_sc_ha_corr'].max():.1f} sc/ha",
                delta=None
            )

        # Botão para exportar dados filtrados
        buffer_boxplot_57000_65000_sc = io.BytesIO()
        df_filtrado_57000_65000_sc.to_excel(
            buffer_boxplot_57000_65000_sc, index=False)  # type: ignore
        buffer_boxplot_57000_65000_sc.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Dados para Box Plot - 57.000 a 65.000 plantas/ha - Sacas)",
            data=buffer_boxplot_57000_65000_sc,
            file_name="dados_boxplot_57000_a_65000_plantas_ha_sacas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning(
            "Não há dados disponíveis para densidades entre 57.000 e 65.000 plantas/ha com os filtros aplicados.")

# =========================
# Box Plot - Produção (sc/ha) para densidades entre 65000 e 74000
# =========================
with st.expander("📊 Box Plot - Densidades entre 65.000 e 74.000 plantas/ha (Sacas/ha)", expanded=False):
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
            Box Plot - Produção (sc/ha) para Densidades entre 65.000 e 74.000 plantas/ha
        </div>
        """,
        unsafe_allow_html=True
    )

    # Filtra dados para densidades entre 65000 e 74000
    df_filtrado_65000_74000_sc = df_analise_densidade_agrupado[
        (df_analise_densidade_agrupado['numPlantas_ha'] > 65000) &
        (df_analise_densidade_agrupado['numPlantas_ha'] <= 74000)
    ].copy()

    if not df_filtrado_65000_74000_sc.empty:
        # Cria o box plot
        fig = go.Figure()

        # Adiciona o box plot
        fig.add_trace(go.Box(
            x=df_filtrado_65000_74000_sc['prod_sc_ha_corr'],
            name='Prod@13.5% (sc/ha)',
            marker_color='#E91E63',  # Cor rosa/magenta para diferenciar
            boxmean=True,  # Mostra a média
            boxpoints='outliers',  # Mostra outliers
            line=dict(color='#E91E63', width=2),
            fillcolor='rgba(233, 30, 99, 0.1)'
        ))

        # Calcula estatísticas
        serie = df_filtrado_65000_74000_sc['prod_sc_ha_corr']
        media = float(serie.mean())
        mediana = float(serie.median())  # type: ignore
        q1 = float(serie.quantile(0.25))  # type: ignore
        q3 = float(serie.quantile(0.75))  # type: ignore

        # Adiciona linhas de referência
        fig.add_vline(
            x=media,
            line_dash='dot',
            line_color='red',
            line_width=2,
            annotation_text=f"Média: {media:.1f} sc/ha",
            annotation_position="top right",
            annotation_font_color='red',
            annotation_font_size=14
        )

        fig.add_vline(
            x=mediana,
            line_dash='dash',
            line_color='green',
            line_width=2,
            annotation_text=f"Mediana: {mediana:.1f} sc/ha",
            annotation_position="bottom right",
            annotation_font_color='green',
            annotation_font_size=14
        )

        # Configura o layout
        fig.update_layout(
            title={
                'text': f'Box Plot - Produção @13.5% (sc/ha) - Densidades entre 65.000 e 74.000 plantas/ha',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black'}
            },
            xaxis_title='Produção @13.5% (sc/ha)',
            yaxis_title='',
            plot_bgcolor='#f5f7fa',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            yaxis=dict(
                tickfont=dict(size=14, color='black'),
                showgrid=False,
                zeroline=False
            ),
            showlegend=False,
            height=500,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        # Adiciona anotações com estatísticas
        fig.add_annotation(
            x=0.02, y=0.98,
            xref='paper', yref='paper',
            text=f"<b>Estatísticas:</b><br>Q1: {q1:.1f}<br>Q3: {q3:.1f}<br>IQR: {q3-q1:.1f}",
            showarrow=False,
            font=dict(size=12, color='black'),
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='gray',
            borderwidth=1
        )

        st.plotly_chart(fig, use_container_width=True)

        # Exibe estatísticas resumidas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Média",
                value=f"{media:.1f} sc/ha",
                delta=None
            )

        with col2:
            st.metric(
                label="Mediana",
                value=f"{mediana:.1f} sc/ha",
                delta=None
            )

        with col3:
            st.metric(
                label="Mínimo",
                value=f"{df_filtrado_65000_74000_sc['prod_sc_ha_corr'].min():.1f} sc/ha",
                delta=None
            )

        with col4:
            st.metric(
                label="Máximo",
                value=f"{df_filtrado_65000_74000_sc['prod_sc_ha_corr'].max():.1f} sc/ha",
                delta=None
            )

        # Botão para exportar dados filtrados
        buffer_boxplot_65000_74000_sc = io.BytesIO()
        df_filtrado_65000_74000_sc.to_excel(
            buffer_boxplot_65000_74000_sc, index=False)  # type: ignore
        buffer_boxplot_65000_74000_sc.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Dados para Box Plot - 65.000 a 74.000 plantas/ha - Sacas)",
            data=buffer_boxplot_65000_74000_sc,
            file_name="dados_boxplot_65000_a_74000_plantas_ha_sacas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning(
            "Não há dados disponíveis para densidades entre 65.000 e 74.000 plantas/ha com os filtros aplicados.")

# =========================
# Box Plot - Produção (sc/ha) para densidades maiores que 74000
# =========================
with st.expander("📊 Box Plot - Densidades maiores que 74.000 plantas/ha (Sacas/ha)", expanded=False):
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
            Box Plot - Produção (sc/ha) para Densidades maiores que 74.000 plantas/ha
        </div>
        """,
        unsafe_allow_html=True
    )

    # Filtra dados para densidades maiores que 74000
    df_filtrado_maior_74000_sc = df_analise_densidade_agrupado[
        df_analise_densidade_agrupado['numPlantas_ha'] > 74000
    ].copy()

    if not df_filtrado_maior_74000_sc.empty:
        # Cria o box plot
        fig = go.Figure()

        # Adiciona o box plot
        fig.add_trace(go.Box(
            x=df_filtrado_maior_74000_sc['prod_sc_ha_corr'],
            name='Prod@13.5% (sc/ha)',
            marker_color='#9C27B0',  # Cor roxa para diferenciar
            boxmean=True,  # Mostra a média
            boxpoints='outliers',  # Mostra outliers
            line=dict(color='#9C27B0', width=2),
            fillcolor='rgba(156, 39, 176, 0.1)'
        ))

        # Calcula estatísticas
        serie = df_filtrado_maior_74000_sc['prod_sc_ha_corr']
        media = float(serie.mean())
        mediana = float(serie.median())  # type: ignore
        q1 = float(serie.quantile(0.25))  # type: ignore
        q3 = float(serie.quantile(0.75))  # type: ignore

        # Adiciona linhas de referência
        fig.add_vline(
            x=media,
            line_dash='dot',
            line_color='red',
            line_width=2,
            annotation_text=f"Média: {media:.1f} sc/ha",
            annotation_position="top right",
            annotation_font_color='red',
            annotation_font_size=14
        )

        fig.add_vline(
            x=mediana,
            line_dash='dash',
            line_color='green',
            line_width=2,
            annotation_text=f"Mediana: {mediana:.1f} sc/ha",
            annotation_position="bottom right",
            annotation_font_color='green',
            annotation_font_size=14
        )

        # Configura o layout
        fig.update_layout(
            title={
                'text': f'Box Plot - Produção @13.5% (sc/ha) - Densidades maiores que 74.000 plantas/ha',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black'}
            },
            xaxis_title='Produção @13.5% (sc/ha)',
            yaxis_title='',
            plot_bgcolor='#f5f7fa',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            yaxis=dict(
                tickfont=dict(size=14, color='black'),
                showgrid=False,
                zeroline=False
            ),
            showlegend=False,
            height=500,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        # Adiciona anotações com estatísticas
        fig.add_annotation(
            x=0.02, y=0.98,
            xref='paper', yref='paper',
            text=f"<b>Estatísticas:</b><br>Q1: {q1:.1f}<br>Q3: {q3:.1f}<br>IQR: {q3-q1:.1f}",
            showarrow=False,
            font=dict(size=12, color='black'),
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='gray',
            borderwidth=1
        )

        st.plotly_chart(fig, use_container_width=True)

        # Exibe estatísticas resumidas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Média",
                value=f"{media:.1f} sc/ha",
                delta=None
            )

        with col2:
            st.metric(
                label="Mediana",
                value=f"{mediana:.1f} sc/ha",
                delta=None
            )

        with col3:
            st.metric(
                label="Mínimo",
                value=f"{df_filtrado_maior_74000_sc['prod_sc_ha_corr'].min():.1f} sc/ha",
                delta=None
            )

        with col4:
            st.metric(
                label="Máximo",
                value=f"{df_filtrado_maior_74000_sc['prod_sc_ha_corr'].max():.1f} sc/ha",
                delta=None
            )

        # Botão para exportar dados filtrados
        buffer_boxplot_maior_74000_sc = io.BytesIO()
        df_filtrado_maior_74000_sc.to_excel(
            buffer_boxplot_maior_74000_sc, index=False)  # type: ignore
        buffer_boxplot_maior_74000_sc.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Dados para Box Plot - maiores que 74.000 plantas/ha - Sacas)",
            data=buffer_boxplot_maior_74000_sc,
            file_name="dados_boxplot_maior_74000_plantas_ha_sacas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning(
            "Não há dados disponíveis para densidades maiores que 74.000 plantas/ha com os filtros aplicados.")

# =========================
# Box Plot com Facetas - Todos os dados de densidade (Sacas/ha)
# =========================
with st.expander("📊 Box Plot com Facetas - Todas as Faixas de Densidade (Sacas/ha)", expanded=False):
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
            Box Plot com Facetas - Produção (sc/ha) por Faixa de Densidade
        </div>
        """,
        unsafe_allow_html=True
    )

    # Cria DataFrame com todas as faixas de densidade para sacas
    df_todas_faixas_sc = df_analise_densidade_agrupado.copy()

    # Cria coluna de faixa de densidade
    def definir_faixa_densidade_sc(densidade):
        if densidade < 50000:
            return "< 50.000"
        elif 50000 <= densidade <= 57000:
            return "50.001 - 57.000"
        elif 57001 <= densidade <= 65000:
            return "57.001 - 65.000"
        elif 65001 <= densidade <= 74000:
            return "65.001 - 74.000"
        else:
            return "> 74.000"

    df_todas_faixas_sc['faixa_densidade'] = df_todas_faixas_sc['numPlantas_ha'].apply(
        definir_faixa_densidade_sc)

    # Cria coluna auxiliar para ordenação
    def criar_ordem_faixa_sc(faixa):
        if faixa == "< 50.000":
            return 1
        elif faixa == "50.001 - 57.000":
            return 2
        elif faixa == "57.001 - 65.000":
            return 3
        elif faixa == "65.001 - 74.000":
            return 4
        else:  # "> 74.000"
            return 5

    df_todas_faixas_sc['ordem_faixa'] = df_todas_faixas_sc['faixa_densidade'].apply(
        criar_ordem_faixa_sc)

    # Ordena o DataFrame pela coluna auxiliar
    df_todas_faixas_sc = df_todas_faixas_sc.sort_values('ordem_faixa')

    # Filtra apenas dados com produção válida
    df_todas_faixas_filtrado_sc = df_todas_faixas_sc[df_todas_faixas_sc['prod_sc_ha_corr'].notna(
    )].copy()

    if not df_todas_faixas_filtrado_sc.empty:
        # Cria o box plot com facetas usando Plotly Express
        fig = px.box(
            df_todas_faixas_filtrado_sc,
            x='faixa_densidade',
            y='prod_sc_ha_corr',
            color='faixa_densidade',
            title='Box Plot - Produção @13.5% (sc/ha) por Faixa de Densidade',
            labels={
                'faixa_densidade': 'Faixa de Densidade (plantas/ha)',
                'prod_sc_ha_corr': 'Produção @13.5% (sc/ha)'
            },
            color_discrete_map={
                "< 50.000": "#0070C0",
                "50.001 - 57.000": "#4CAF50",
                "57.001 - 65.000": "#FF9800",
                "65.001 - 74.000": "#E91E63",
                "> 74.000": "#9C27B0"
            },
            category_orders={'faixa_densidade': [
                "< 50.000", "50.001 - 57.000", "57.001 - 65.000", "65.001 - 74.000", "> 74.000"]}
        )

        # Configura o layout
        fig.update_layout(
            title={
                'text': f'Box Plot - Produção @13.5% (sc/ha) por Faixa de Densidade<br><sub>Total de observações: {len(df_todas_faixas_filtrado_sc)}</sub>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black'}
            },
            plot_bgcolor='#f5f7fa',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            yaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            showlegend=False,
            height=600,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        # Adiciona estatísticas por faixa
        stats_por_faixa_sc = df_todas_faixas_filtrado_sc.groupby('faixa_densidade')['prod_sc_ha_corr'].agg([
            'count', 'mean', 'median', 'std', 'min', 'max'
        ]).round(1)

        st.plotly_chart(fig, use_container_width=True)

        # Exibe estatísticas resumidas por faixa
        st.markdown("### Estatísticas por Faixa de Densidade (Sacas/ha)")

        # Renomeia colunas para visualização
        stats_por_faixa_sc = stats_por_faixa_sc.rename(columns={  # type: ignore
            'count': 'N',
            'mean': 'Média',
            'median': 'Mediana',
            'std': 'Desvio Padrão',
            'min': 'Mínimo',
            'max': 'Máximo'
        })

        # Configuração do AgGrid para estatísticas por faixa
        gb_stats_sc = GridOptionsBuilder.from_dataframe(stats_por_faixa_sc)

        # Configuração de casas decimais para colunas numéricas
        colunas_formatar_stats_sc = {
            "Média": 1,
            "Mediana": 1,
            "Desvio Padrão": 1,
            "Mínimo": 1,
            "Máximo": 1
        }

        for col in stats_por_faixa_sc.columns:
            if col in colunas_formatar_stats_sc:
                casas = colunas_formatar_stats_sc[col]
                gb_stats_sc.configure_column(
                    col,
                    headerClass='ag-header-bold',
                    menuTabs=['generalMenuTab',
                              'filterMenuTab', 'columnsMenuTab'],
                    valueFormatter=f"value != null ? value.toFixed({casas}) : ''"
                )
            else:
                gb_stats_sc.configure_column(
                    col,
                    headerClass='ag-header-bold',
                    menuTabs=['generalMenuTab',
                              'filterMenuTab', 'columnsMenuTab']
                )

        # Configura opções padrão para todas as colunas
        gb_stats_sc.configure_default_column(editable=False, groupable=True,
                                             filter=True, resizable=True, cellStyle={'fontSize': '12px'})
        gb_stats_sc.configure_grid_options(headerHeight=30)
        grid_options_stats_sc = gb_stats_sc.build()

        # Exibe tabela de estatísticas com AgGrid
        AgGrid(
            stats_por_faixa_sc,
            gridOptions=grid_options_stats_sc,
            enable_enterprise_modules=True,
            fit_columns_on_grid_load=False,
            theme="streamlit",
            height=300,
            reload_data=True,
            custom_css=custom_css
        )

        # Botão para exportar dados com facetas
        buffer_facetas_sc = io.BytesIO()
        df_todas_faixas_filtrado_sc.to_excel(
            buffer_facetas_sc, index=False)  # type: ignore
        buffer_facetas_sc.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Dados com Facetas por Faixa de Densidade - Sacas)",
            data=buffer_facetas_sc,
            file_name="dados_boxplot_facetas_por_faixa_densidade_sacas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Botão para exportar estatísticas por faixa
        buffer_stats_faixas_sc = io.BytesIO()
        stats_por_faixa_sc.to_excel(buffer_stats_faixas_sc)  # type: ignore
        buffer_stats_faixas_sc.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Estatísticas por Faixa de Densidade - Sacas)",
            data=buffer_stats_faixas_sc,
            file_name="estatisticas_por_faixa_densidade_sacas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning(
            "Não há dados válidos disponíveis para criar o box plot com facetas para sacas por hectare.")

# =========================
# NOVA SEÇÃO: Correlação entre Produção e População de Plantas
# =========================

st.markdown("---")
st.markdown(
    """
    <div style="
        background: linear-gradient(90deg, #2E8B57 0%, #3CB371 100%);
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.10);
        padding: 28px 24px 18px 24px;
        margin-bottom: 32px;
        display: flex;
        align-items: center;
    ">
        <div style="flex:1">
            <h1 style="margin-bottom: 0.2em; color: #fff; font-size: 2.2em; font-weight: 700;">
                Correlação entre Produção e População de Plantas
            </h1>
            <h3 style="margin-top: 0; color: #e0e0e0; font-weight: 400; font-size: 1.2em;">
                Análise da relação entre densidade de plantas e produtividade em milho
            </h3>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================
# Gráfico de Dispersão - Produção (kg/ha) vs População de Plantas
# =========================
with st.expander("📈 Gráfico de Dispersão - Produção (kg/ha) vs População de Plantas", expanded=False):
    st.markdown(
        """
        <div style="
            background-color: #e8f5e8;
            border-left: 6px solid #2E8B57;
            padding: 12px 18px;
            margin-bottom: 12px;
            border-radius: 6px;
            font-size: 1.15em;
            color: #2E8B57;
            font-weight: 600;
        ">
            Gráfico de Dispersão - Produção (kg/ha) vs População de Plantas
        </div>
        """,
        unsafe_allow_html=True
    )

    # Filtra dados válidos para correlação
    df_correlacao_kg = df_analise_densidade_agrupado[
        (df_analise_densidade_agrupado['prod_kg_ha_corr'].notna()) &
        (df_analise_densidade_agrupado['numPlantas_ha'].notna())
    ].copy()

    if not df_correlacao_kg.empty:
        # Calcula correlação
        correlacao_kg = float(df_correlacao_kg['prod_kg_ha_corr'].corr(
            df_correlacao_kg['numPlantas_ha']))  # type: ignore[attr-defined]

        # Cria o gráfico de dispersão
        fig = go.Figure()

        # Adiciona pontos de dispersão
        fig.add_trace(go.Scatter(
            x=df_correlacao_kg['numPlantas_ha'],
            y=df_correlacao_kg['prod_kg_ha_corr'],
            mode='markers',
            name='Observações',
            marker=dict(
                color='#0070C0',
                size=8,
                opacity=0.7,
                line=dict(color='#005a9e', width=1)
            ),
            hovertemplate='<b>População:</b> %{x:,.0f} plantas/ha<br>' +
            '<b>Produção:</b> %{y:,.1f} kg/ha<br>' +
            '<extra></extra>'
        ))

        # Adiciona linha de tendência
        z = np.polyfit(
            df_correlacao_kg['numPlantas_ha'], df_correlacao_kg['prod_kg_ha_corr'], 1)
        p = np.poly1d(z)
        fig.add_trace(go.Scatter(
            x=df_correlacao_kg['numPlantas_ha'],
            y=p(df_correlacao_kg['numPlantas_ha']),
            mode='lines',
            name='Linha de Tendência',
            line=dict(color='red', width=3, dash='dash'),
            hovertemplate='<b>Linha de Tendência</b><extra></extra>'
        ))

        # Configura o layout
        fig.update_layout(
            title={
                'text': f'Correlação entre Produção (kg/ha) e População de Plantas<br><sub>Coeficiente de Correlação: r = {correlacao_kg:.3f}</sub>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black'}
            },
            xaxis_title='População de Plantas (plantas/ha)',
            yaxis_title='Produção @13.5% (kg/ha)',
            plot_bgcolor='#f5f7fa',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False,
                tickmode='array',
                tickvals=[40000, 50000, 60000, 70000],
                ticktext=['40.000', '50.000', '60.000', '70.000'],
                range=[40000, 70000]
            ),
            yaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            showlegend=True,
            legend=dict(
                x=0.02, y=0.98,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='gray',
                borderwidth=1
            ),
            height=600,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        # Adiciona anotações com estatísticas
        fig.add_annotation(
            x=0.98, y=0.98,
            xref='paper', yref='paper',
            text=f"<b>Estatísticas:</b><br>Correlação: {correlacao_kg:.3f}<br>R²: {correlacao_kg**2:.3f}",
            showarrow=False,
            font=dict(size=12, color='black'),
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='gray',
            borderwidth=1
        )

        st.plotly_chart(fig, use_container_width=True)

        # Exibe estatísticas resumidas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Coeficiente de Correlação (r)",
                value=f"{correlacao_kg:.3f}",
                delta=None
            )

        with col2:
            st.metric(
                label="Coeficiente de Determinação (R²)",
                value=f"{correlacao_kg**2:.3f}",
                delta=None
            )

        with col3:
            st.metric(
                label="Número de Observações",
                value=f"{len(df_correlacao_kg)}",
                delta=None
            )

        with col4:
            # Interpretação da correlação
            if abs(correlacao_kg) >= 0.7:
                interpretacao = "Forte"
            elif abs(correlacao_kg) >= 0.5:
                interpretacao = "Moderada"
            elif abs(correlacao_kg) >= 0.3:
                interpretacao = "Fraca"
            else:
                interpretacao = "Muito Fraca"

            st.metric(
                label="Força da Correlação",
                value=interpretacao,
                delta=None
            )

        # Botão para exportar dados de correlação
        buffer_correlacao_kg = io.BytesIO()
        df_correlacao_kg.to_excel(
            buffer_correlacao_kg, index=False)  # type: ignore
        buffer_correlacao_kg.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Dados para Correlação - kg/ha)",
            data=buffer_correlacao_kg,
            file_name="dados_correlacao_producao_kg_ha.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning("Não há dados válidos disponíveis para análise de correlação.")

# =========================
# Gráfico de Dispersão - Produção (sc/ha) vs População de Plantas
# =========================
with st.expander("📈 Gráfico de Dispersão - Produção (sc/ha) vs População de Plantas", expanded=False):
    st.markdown(
        """
        <div style="
            background-color: #e8f5e8;
            border-left: 6px solid #2E8B57;
            padding: 12px 18px;
            margin-bottom: 12px;
            border-radius: 6px;
            font-size: 1.15em;
            color: #2E8B57;
            font-weight: 600;
        ">
            Gráfico de Dispersão - Produção (sc/ha) vs População de Plantas
        </div>
        """,
        unsafe_allow_html=True
    )

    # Filtra dados válidos para correlação
    df_correlacao_sc = df_analise_densidade_agrupado[
        (df_analise_densidade_agrupado['prod_sc_ha_corr'].notna()) &
        (df_analise_densidade_agrupado['numPlantas_ha'].notna())
    ].copy()

    if not df_correlacao_sc.empty:
        # Calcula correlação
        correlacao_sc = float(df_correlacao_sc['prod_sc_ha_corr'].corr(
            df_correlacao_sc['numPlantas_ha']))  # type: ignore[attr-defined]

        # Cria o gráfico de dispersão
        fig = go.Figure()

        # Adiciona pontos de dispersão
        fig.add_trace(go.Scatter(
            x=df_correlacao_sc['numPlantas_ha'],
            y=df_correlacao_sc['prod_sc_ha_corr'],
            mode='markers',
            name='Observações',
            marker=dict(
                color='#0070C0',
                size=8,
                opacity=0.7,
                line=dict(color='#005a9e', width=1)
            ),
            hovertemplate='<b>População:</b> %{x:,.0f} plantas/ha<br>' +
            '<b>Produção:</b> %{y:.1f} sc/ha<br>' +
            '<extra></extra>'
        ))

        # Adiciona linha de tendência
        z = np.polyfit(
            df_correlacao_sc['numPlantas_ha'], df_correlacao_sc['prod_sc_ha_corr'], 1)
        p = np.poly1d(z)
        fig.add_trace(go.Scatter(
            x=df_correlacao_sc['numPlantas_ha'],
            y=p(df_correlacao_sc['numPlantas_ha']),
            mode='lines',
            name='Linha de Tendência',
            line=dict(color='red', width=3, dash='dash'),
            hovertemplate='<b>Linha de Tendência</b><extra></extra>'
        ))

        # Configura o layout
        fig.update_layout(
            title={
                'text': f'Correlação entre Produção (sc/ha) e População de Plantas<br><sub>Coeficiente de Correlação: r = {correlacao_sc:.3f}</sub>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black'}
            },
            xaxis_title='População de Plantas (plantas/ha)',
            yaxis_title='Produção @13.5% (sc/ha)',
            plot_bgcolor='#f5f7fa',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False,
                tickmode='array',
                tickvals=[40000, 50000, 60000, 70000],
                ticktext=['40.000', '50.000', '60.000', '70.000'],
                range=[40000, 70000]
            ),
            yaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            showlegend=True,
            legend=dict(
                x=0.02, y=0.98,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='gray',
                borderwidth=1
            ),
            height=600,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        # Adiciona anotações com estatísticas
        fig.add_annotation(
            x=0.98, y=0.98,
            xref='paper', yref='paper',
            text=f"<b>Estatísticas:</b><br>Correlação: {correlacao_sc:.3f}<br>R²: {correlacao_sc**2:.3f}",
            showarrow=False,
            font=dict(size=12, color='black'),
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='gray',
            borderwidth=1
        )

        st.plotly_chart(fig, use_container_width=True)

        # Exibe estatísticas resumidas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Coeficiente de Correlação (r)",
                value=f"{correlacao_sc:.3f}",
                delta=None
            )

        with col2:
            st.metric(
                label="Coeficiente de Determinação (R²)",
                value=f"{correlacao_sc**2:.3f}",
                delta=None
            )

        with col3:
            st.metric(
                label="Número de Observações",
                value=f"{len(df_correlacao_sc)}",
                delta=None
            )

        with col4:
            # Interpretação da correlação
            if abs(correlacao_sc) >= 0.7:
                interpretacao = "Forte"
            elif abs(correlacao_sc) >= 0.5:
                interpretacao = "Moderada"
            elif abs(correlacao_sc) >= 0.3:
                interpretacao = "Fraca"
            else:
                interpretacao = "Muito Fraca"

            st.metric(
                label="Força da Correlação",
                value=interpretacao,
                delta=None
            )

        # Botão para exportar dados de correlação
        buffer_correlacao_sc = io.BytesIO()
        df_correlacao_sc.to_excel(
            buffer_correlacao_sc, index=False)  # type: ignore
        buffer_correlacao_sc.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Dados para Correlação - sc/ha)",
            data=buffer_correlacao_sc,
            file_name="dados_correlacao_producao_sc_ha.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning("Não há dados válidos disponíveis para análise de correlação.")

# =========================
# Matriz de Correlação - Todas as Variáveis
# =========================
with st.expander("📊 Matriz de Correlação - Variáveis de Produção e Densidade", expanded=False):
    st.markdown(
        """
        <div style="
            background-color: #e8f5e8;
            border-left: 6px solid #2E8B57;
            padding: 12px 18px;
            margin-bottom: 12px;
            border-radius: 6px;
            font-size: 1.15em;
            color: #2E8B57;
            font-weight: 600;
        ">
            Matriz de Correlação - Variáveis de Produção e Densidade
        </div>
        """,
        unsafe_allow_html=True
    )

    # Seleciona variáveis para matriz de correlação
    variaveis_correlacao = [
        'prod_kg_ha_corr', 'prod_sc_ha_corr', 'numPlantas_ha'
    ]

    df_matriz_correlacao = df_analise_densidade_agrupado[variaveis_correlacao].copy(
    )

    # Remove linhas com valores nulos
    df_matriz_correlacao = df_matriz_correlacao.dropna()

    if not df_matriz_correlacao.empty and len(df_matriz_correlacao) > 1:
        # Calcula matriz de correlação
        matriz_correlacao = df_matriz_correlacao.corr()  # type: ignore

        # Renomeia colunas para visualização
        matriz_correlacao = matriz_correlacao.rename(columns={  # type: ignore
            'prod_kg_ha_corr': 'Prod (kg/ha)',
            'prod_sc_ha_corr': 'Prod (sc/ha)',
            'numPlantas_ha': 'Pop (plantas/ha)'
        })

        matriz_correlacao = matriz_correlacao.rename(index={  # type: ignore
            'prod_kg_ha_corr': 'Prod (kg/ha)',
            'prod_sc_ha_corr': 'Prod (sc/ha)',
            'numPlantas_ha': 'Pop (plantas/ha)'
        })

        # Cria heatmap da matriz de correlação
        fig = go.Figure(data=go.Heatmap(
            z=matriz_correlacao.values,
            x=matriz_correlacao.columns,
            y=matriz_correlacao.index,
            colorscale='RdYlBu_r',
            zmid=0,
            text=matriz_correlacao.values.round(3),
            texttemplate="%{text}",
            textfont={"size": 14},
            hoverongaps=False,
            hovertemplate='<b>%{y} vs %{x}</b><br>' +
            'Correlação: %{z:.3f}<extra></extra>'
        ))

        fig.update_layout(
            title={
                'text': f'Matriz de Correlação - Variáveis de Produção e Densidade',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black'}
            },
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black')
            ),
            yaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black')
            ),
            height=500,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Exibe matriz de correlação em formato de tabela
        st.markdown("### Matriz de Correlação (Valores Numéricos)")

        # Configuração do AgGrid para matriz de correlação
        gb_matriz = GridOptionsBuilder.from_dataframe(matriz_correlacao)

        # Configuração de casas decimais para todas as colunas
        for col in matriz_correlacao.columns:
            gb_matriz.configure_column(
                col,
                headerClass='ag-header-bold',
                menuTabs=['generalMenuTab', 'filterMenuTab', 'columnsMenuTab'],
                valueFormatter="value != null ? value.toFixed(3) : ''"
            )

        # Configura opções padrão para todas as colunas
        gb_matriz.configure_default_column(editable=False, groupable=True,
                                           filter=True, resizable=True, cellStyle={'fontSize': '12px'})
        gb_matriz.configure_grid_options(headerHeight=30)
        grid_options_matriz = gb_matriz.build()

        # Exibe matriz de correlação com AgGrid
        AgGrid(
            matriz_correlacao,
            gridOptions=grid_options_matriz,
            enable_enterprise_modules=True,
            fit_columns_on_grid_load=False,
            theme="streamlit",
            height=300,
            reload_data=True,
            custom_css=custom_css
        )

        # Botão para exportar matriz de correlação
        buffer_matriz = io.BytesIO()
        matriz_correlacao.to_excel(buffer_matriz)  # type: ignore
        buffer_matriz.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Matriz de Correlação)",
            data=buffer_matriz,
            file_name="matriz_correlacao_producao_densidade.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning("Não há dados suficientes para criar a matriz de correlação.")

# =========================
# Análise de Regressão Linear
# =========================
with st.expander("📈 Análise de Regressão Linear - Produção vs População", expanded=False):
    st.markdown(
        """
        <div style="
            background-color: #e8f5e8;
            border-left: 6px solid #2E8B57;
            padding: 12px 18px;
            margin-bottom: 12px;
            border-radius: 6px;
            font-size: 1.15em;
            color: #2E8B57;
            font-weight: 600;
        ">
            Análise de Regressão Linear - Produção vs População de Plantas
        </div>
        """,
        unsafe_allow_html=True
    )

    # Filtra dados válidos para regressão
    df_regressao = df_analise_densidade_agrupado[
        (df_analise_densidade_agrupado['prod_kg_ha_corr'].notna()) &
        (df_analise_densidade_agrupado['numPlantas_ha'].notna())
    ].copy()

    if not df_regressao.empty and len(df_regressao) > 2:
        # Calcula regressão linear
        x = df_regressao['numPlantas_ha'].values  # type: ignore
        y = df_regressao['prod_kg_ha_corr'].values  # type: ignore

        # Ajusta a regressão linear
        coeffs = np.polyfit(x, y, 1)  # type: ignore
        slope = coeffs[0]
        intercept = coeffs[1]

        # Calcula R²
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)  # type: ignore
        r_squared = 1 - (ss_res / ss_tot)

        # Calcula correlação
        correlacao = np.corrcoef(x, y)[0, 1]  # type: ignore

        # Cria gráfico de regressão
        fig = go.Figure()

        # Adiciona pontos de dispersão
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode='markers',
            name='Observações',
            marker=dict(
                color='#0070C0',
                size=8,
                opacity=0.7,
                line=dict(color='#005a9e', width=1)
            ),
            hovertemplate='<b>População:</b> %{x:,.0f} plantas/ha<br>' +
            '<b>Produção:</b> %{y:,.1f} kg/ha<br>' +
            '<extra></extra>'
        ))

        # Adiciona linha de regressão
        fig.add_trace(go.Scatter(
            x=x,
            y=y_pred,
            mode='lines',
            name=f'Regressão: y = {slope:.4f}x + {intercept:.1f}',
            line=dict(color='red', width=3),
            hovertemplate='<b>Linha de Regressão</b><extra></extra>'
        ))

        # Configura o layout
        fig.update_layout(
            title={
                'text': f'Regressão Linear: Produção vs População de Plantas<br><sub>R² = {r_squared:.3f} | r = {correlacao:.3f}</sub>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black'}
            },
            xaxis_title='População de Plantas (plantas/ha)',
            yaxis_title='Produção @13.5% (kg/ha)',
            plot_bgcolor='#f5f7fa',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False,
                tickmode='array',
                tickvals=[40000, 50000, 60000, 70000],
                ticktext=['40.000', '50.000', '60.000', '70.000'],
                range=[40000, 70000]
            ),
            yaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            showlegend=True,
            legend=dict(
                x=0.02, y=0.98,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='gray',
                borderwidth=1
            ),
            height=600,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        # Adiciona anotações com estatísticas da regressão
        fig.add_annotation(
            x=0.98, y=0.98,
            xref='paper', yref='paper',
            text=f"<b>Estatísticas da Regressão:</b><br>" +
                 f"Equação: y = {slope:.4f}x + {intercept:.1f}<br>" +
                 f"R²: {r_squared:.3f}<br>" +
                 f"Correlação: {correlacao:.3f}",
            showarrow=False,
            font=dict(size=12, color='black'),
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='gray',
            borderwidth=1
        )

        st.plotly_chart(fig, use_container_width=True)

        # Exibe estatísticas da regressão
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Coeficiente Angular (Slope)",
                value=f"{slope:.4f}",
                delta=None
            )

        with col2:
            st.metric(
                label="Intercepto",
                value=f"{intercept:.1f}",
                delta=None
            )

        with col3:
            st.metric(
                label="R² (Coeficiente de Determinação)",
                value=f"{r_squared:.3f}",
                delta=None
            )

        with col4:
            st.metric(
                label="Correlação (r)",
                value=f"{correlacao:.3f}",
                delta=None
            )

        # Interpretação da regressão
        st.markdown("### Interpretação da Regressão Linear")

        if slope > 0:
            direcao = "positiva"
            interpretacao_slope = f"Para cada aumento de 1.000 plantas/ha, a produção aumenta em média {slope*1000:.1f} kg/ha"
        else:
            direcao = "negativa"
            interpretacao_slope = f"Para cada aumento de 1.000 plantas/ha, a produção diminui em média {abs(slope*1000):.1f} kg/ha"

        st.markdown(f"""
        - **Direção da relação:** {direcao}
        - **Interpretação do coeficiente angular:** {interpretacao_slope}
        - **Força da relação:** O modelo explica {r_squared*100:.1f}% da variabilidade na produção
        - **Qualidade do ajuste:** {'Excelente' if r_squared >= 0.7 else 'Boa' if r_squared >= 0.5 else 'Moderada' if r_squared >= 0.3 else 'Fraca'}
        """)

        # Botão para exportar dados de regressão
        buffer_regressao = io.BytesIO()
        df_regressao.to_excel(buffer_regressao, index=False)  # type: ignore
        buffer_regressao.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Dados para Regressão Linear)",
            data=buffer_regressao,
            file_name="dados_regressao_linear_producao_populacao.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning(
            "Não há dados suficientes para criar o gráfico de pontos baseados na equação da reta.")

# =========================
# Análise de Regressão Linear - Produção (sc/ha) vs População
# =========================
with st.expander("📈 Análise de Regressão Linear - Produção (sc/ha) vs População", expanded=False):
    st.markdown(
        """
        <div style="
            background-color: #e8f5e8;
            border-left: 6px solid #2E8B57;
            padding: 12px 18px;
            margin-bottom: 12px;
            border-radius: 6px;
            font-size: 1.15em;
            color: #2E8B57;
            font-weight: 600;
        ">
            Análise de Regressão Linear - Produção (sc/ha) vs População de Plantas
        </div>
        """,
        unsafe_allow_html=True
    )

    # Filtra dados válidos para regressão
    df_regressao_sc = df_analise_densidade_agrupado[
        (df_analise_densidade_agrupado['prod_sc_ha_corr'].notna()) &
        (df_analise_densidade_agrupado['numPlantas_ha'].notna())
    ].copy()

    if not df_regressao_sc.empty and len(df_regressao_sc) > 2:
        # Calcula regressão linear
        x = df_regressao_sc['numPlantas_ha'].values  # type: ignore
        y = df_regressao_sc['prod_sc_ha_corr'].values  # type: ignore

        # Ajusta a regressão linear
        coeffs = np.polyfit(x, y, 1)  # type: ignore
        slope = coeffs[0]
        intercept = coeffs[1]

        # Calcula R²
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)  # type: ignore
        r_squared = 1 - (ss_res / ss_tot)

        # Calcula correlação
        correlacao = np.corrcoef(x, y)[0, 1]  # type: ignore

        # Cria gráfico de regressão
        fig = go.Figure()

        # Adiciona pontos de dispersão
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode='markers',
            name='Observações',
            marker=dict(
                color='#0070C0',
                size=8,
                opacity=0.7,
                line=dict(color='#005a9e', width=1)
            ),
            hovertemplate='<b>População:</b> %{x:,.0f} plantas/ha<br>' +
            '<b>Produção:</b> %{y:.1f} sc/ha<br>' +
            '<extra></extra>'
        ))

        # Adiciona linha de regressão
        fig.add_trace(go.Scatter(
            x=x,
            y=y_pred,
            mode='lines',
            name=f'Regressão: y = {slope:.4f}x + {intercept:.1f}',
            line=dict(color='red', width=3),
            hovertemplate='<b>Linha de Regressão</b><extra></extra>'
        ))

        # Configura o layout
        fig.update_layout(
            title={
                'text': f'Regressão Linear: Produção (sc/ha) vs População de Plantas<br><sub>R² = {r_squared:.3f} | r = {correlacao:.3f}</sub>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black'}
            },
            xaxis_title='População de Plantas (plantas/ha)',
            yaxis_title='Produção @13.5% (sc/ha)',
            plot_bgcolor='#f5f7fa',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False,
                tickmode='array',
                tickvals=[40000, 50000, 60000, 70000],
                ticktext=['40.000', '50.000', '60.000', '70.000'],
                range=[40000, 70000]
            ),
            yaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            showlegend=True,
            legend=dict(
                x=0.02, y=0.98,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='gray',
                borderwidth=1
            ),
            height=600,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        # Adiciona anotações com estatísticas da regressão
        fig.add_annotation(
            x=0.98, y=0.98,
            xref='paper', yref='paper',
            text=f"<b>Estatísticas da Regressão:</b><br>" +
                 f"Equação: y = {slope:.4f}x + {intercept:.1f}<br>" +
                 f"R²: {r_squared:.3f}<br>" +
                 f"Correlação: {correlacao:.3f}",
            showarrow=False,
            font=dict(size=12, color='black'),
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='gray',
            borderwidth=1
        )

        st.plotly_chart(fig, use_container_width=True)

        # Exibe estatísticas da regressão
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Coeficiente Angular (Slope)",
                value=f"{slope:.4f}",
                delta=None
            )

        with col2:
            st.metric(
                label="Intercepto",
                value=f"{intercept:.1f}",
                delta=None
            )

        with col3:
            st.metric(
                label="R² (Coeficiente de Determinação)",
                value=f"{r_squared:.3f}",
                delta=None
            )

        with col4:
            st.metric(
                label="Correlação (r)",
                value=f"{correlacao:.3f}",
                delta=None
            )

        # Interpretação da regressão
        st.markdown("### Interpretação da Regressão Linear")

        if slope > 0:
            direcao = "positiva"
            interpretacao_slope = f"Para cada aumento de 1.000 plantas/ha, a produção aumenta em média {slope*1000:.1f} sc/ha"
        else:
            direcao = "negativa"
            interpretacao_slope = f"Para cada aumento de 1.000 plantas/ha, a produção diminui em média {abs(slope*1000):.1f} sc/ha"

        st.markdown(f"""
        - **Direção da relação:** {direcao}
        - **Interpretação do coeficiente angular:** {interpretacao_slope}
        - **Força da relação:** O modelo explica {r_squared*100:.1f}% da variabilidade na produção
        - **Qualidade do ajuste:** {'Excelente' if r_squared >= 0.7 else 'Boa' if r_squared >= 0.5 else 'Moderada' if r_squared >= 0.3 else 'Fraca'}
        """)

        # Botão para exportar dados de regressão
        buffer_regressao_sc = io.BytesIO()
        df_regressao_sc.to_excel(
            buffer_regressao_sc, index=False)  # type: ignore
        buffer_regressao_sc.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Dados para Regressão Linear - sc/ha)",
            data=buffer_regressao_sc,
            file_name="dados_regressao_linear_producao_sc_populacao.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # =========================
    # Gráfico de Pontos Baseados na Equação da Reta
    # =========================
    st.markdown(
        """
        <div style="
            background-color: #e8f5e8;
            border-left: 6px solid #2E8B57;
            padding: 12px 18px;
            margin-bottom: 12px;
            border-radius: 6px;
            font-size: 1.15em;
            color: #2E8B57;
            font-weight: 600;
        ">
            Gráfico de Pontos Baseados na Equação da Reta - População 40.000 a 70.000
        </div>
        """,
        unsafe_allow_html=True
    )

    # Verifica se há dados para criar o gráfico
    if not df_regressao.empty and not df_regressao_sc.empty:
        # Gera pontos baseados na equação da reta
        populacoes = [40000, 50000, 60000, 70000]

        # Calcula coeficientes para kg/ha (usando dados da primeira regressão)
        x_kg = df_regressao['numPlantas_ha'].values
        y_kg = df_regressao['prod_kg_ha_corr'].values
        coeffs_kg = np.polyfit(x_kg, y_kg, 1)
        slope_kg = coeffs_kg[0]
        intercept_kg = coeffs_kg[1]

        # Calcula coeficientes para sc/ha (usando dados da segunda regressão)
        x_sc = df_regressao_sc['numPlantas_ha'].values
        y_sc = df_regressao_sc['prod_sc_ha_corr'].values
        coeffs_sc = np.polyfit(x_sc, y_sc, 1)
        slope_sc = coeffs_sc[0]
        intercept_sc = coeffs_sc[1]

        producoes_kg = [slope_kg * pop + intercept_kg for pop in populacoes]
        producoes_sc = [slope_sc * pop + intercept_sc for pop in populacoes]

        # Cria o gráfico para kg/ha
        fig_pontos_kg = go.Figure()

        # Adiciona linha baseada na equação
        fig_pontos_kg.add_trace(go.Scatter(
            x=populacoes,
            y=producoes_kg,
            mode='lines',
            name='Linha da Equação',
            line=dict(color='#0070C0', width=3),
            hovertemplate='<b>População:</b> %{x:,.0f} plantas/ha<br>' +
            '<b>Produção Estimada:</b> %{y:,.1f} kg/ha<br>' +
            '<extra></extra>'
        ))

        # Configura o layout
        fig_pontos_kg.update_layout(
            title={
                'text': f'Pontos Baseados na Equação da Reta (kg/ha)<br><sub>Equação: y = {slope_kg:.4f}x + {intercept_kg:.1f}</sub>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black'}
            },
            xaxis_title='População de Plantas (plantas/ha)',
            yaxis_title='Produção Estimada @13.5% (kg/ha)',
            plot_bgcolor='#f5f7fa',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False,
                tickmode='array',
                tickvals=[40000, 50000, 60000, 70000],
                ticktext=['40.000', '50.000', '60.000', '70.000'],
                range=[40000, 70000]
            ),
            yaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            showlegend=True,
            legend=dict(
                x=0.02, y=0.98,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='gray',
                borderwidth=1
            ),
            height=500,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        st.plotly_chart(fig_pontos_kg, use_container_width=True)

        # Cria o gráfico para sc/ha
        fig_pontos_sc = go.Figure()

        # Adiciona linha baseada na equação
        fig_pontos_sc.add_trace(go.Scatter(
            x=populacoes,
            y=producoes_sc,
            mode='lines',
            name='Linha da Equação',
            line=dict(color='#0070C0', width=3),
            hovertemplate='<b>População:</b> %{x:,.0f} plantas/ha<br>' +
            '<b>Produção Estimada:</b> %{y:,.1f} sc/ha<br>' +
            '<extra></extra>'
        ))

        # Configura o layout
        fig_pontos_sc.update_layout(
            title={
                'text': f'Pontos Baseados na Equação da Reta (sc/ha)<br><sub>Equação: y = {slope_sc:.4f}x + {intercept_sc:.1f}</sub>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': 'black'}
            },
            xaxis_title='População de Plantas (plantas/ha)',
            yaxis_title='Produção Estimada @13.5% (sc/ha)',
            plot_bgcolor='#f5f7fa',
            paper_bgcolor='white',
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False,
                tickmode='array',
                tickvals=[40000, 50000, 60000, 70000],
                ticktext=['40.000', '50.000', '60.000', '70.000'],
                range=[40000, 70000]
            ),
            yaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                gridcolor='lightgray',
                zeroline=False
            ),
            showlegend=True,
            legend=dict(
                x=0.02, y=0.98,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='gray',
                borderwidth=1
            ),
            height=500,
            margin=dict(l=50, r=50, t=100, b=50)
        )

        st.plotly_chart(fig_pontos_sc, use_container_width=True)

        # Tabela com os valores calculados
        st.markdown("### Valores Estimados pela Equação da Reta")

        # Cria DataFrame com os valores
        df_pontos = pd.DataFrame({
            'População (plantas/ha)': populacoes,
            'Produção Estimada (kg/ha)': [f"{prod:.1f}" for prod in producoes_kg],
            'Produção Estimada (sc/ha)': [f"{prod:.1f}" for prod in producoes_sc]
        })

        # Configuração do AgGrid para tabela de pontos
        gb_pontos = GridOptionsBuilder.from_dataframe(df_pontos)
        gb_pontos.configure_default_column(editable=False, groupable=True,
                                           filter=True, resizable=True, cellStyle={'fontSize': '12px'})
        gb_pontos.configure_grid_options(headerHeight=30)
        grid_options_pontos = gb_pontos.build()

        # Exibe tabela com AgGrid
        AgGrid(
            df_pontos,
            gridOptions=grid_options_pontos,
            enable_enterprise_modules=True,
            fit_columns_on_grid_load=False,
            theme="streamlit",
            height=200,
            reload_data=True,
            custom_css=custom_css
        )

        # Botão para exportar dados dos pontos
        buffer_pontos = io.BytesIO()
        df_pontos.to_excel(buffer_pontos, index=False)
        buffer_pontos.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Pontos da Equação da Reta)",
            data=buffer_pontos,
            file_name="pontos_equacao_retta_producao_populacao.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.warning("Não há dados suficientes para análise de regressão linear.")
