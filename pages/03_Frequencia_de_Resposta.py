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
                Análise de Frequência e Performance Relativa de Híbridos em Múltiplos Locais
            </h1>
            <h3 style="margin-top: 0; color: #e0e0e0; font-weight: 400; font-size: 1.2em;">
                Avaliação da produção relativa dos híbridos em relação ao topo produtivo de cada local, evidenciando padrões de adaptação e performance.
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
# Agrupamento por fazendaRef e pares de indexTratamento (Frequência de Resposta)
# =========================
# Cria coluna de agrupamento para pares (101,201), (102,202), ..., (121,221)

# Cria coluna auxiliar para agrupamento
if 'indexTratamento' in df_analise_conjunta.columns:
    df_analise_conjunta['indexTratamentoAgrupado'] = df_analise_conjunta['indexTratamento'].apply(
        agrupa_index)
else:
    st.warning('Coluna indexTratamento não encontrada no DataFrame.')

# Agrupa por fazendaRef e indexTratamentoAgrupado, calculando a média de prod_sc_ha_corr
if all(col in df_analise_conjunta.columns for col in ['fazendaRef', 'indexTratamentoAgrupado', 'prod_sc_ha_corr']):
    df_frequencia = (
        df_analise_conjunta
        .groupby(['fazendaRef', 'indexTratamentoAgrupado'], as_index=False)
        .agg({'prod_sc_ha_corr': 'mean'})
    )
    # Recupera o nome do híbrido para cada par (fazendaRef, indexTratamentoAgrupado)
    df_nome = (
        df_analise_conjunta
        .groupby(['fazendaRef', 'indexTratamentoAgrupado'])['nome']
        .first()
        .reset_index()
    )
    # Recupera o nome da fazenda para cada fazendaRef
    if 'nomeFazenda' in df_analise_conjunta.columns:
        df_fazenda = (
            df_analise_conjunta
            .groupby('fazendaRef')['nomeFazenda']
            .first()
            .reset_index()
        )
        # Junta nomeFazenda ao DataFrame agrupado
        df_frequencia = pd.merge(
            df_frequencia,
            df_fazenda,
            on='fazendaRef',
            how='left'
        )
    # Junta o nome ao DataFrame agrupado
    df_frequencia = pd.merge(
        df_frequencia,
        df_nome,
        on=['fazendaRef', 'indexTratamentoAgrupado'],
        how='left'
    )
    # Renomeia coluna para exibição
    df_frequencia = df_frequencia.rename(columns={
        'indexTratamentoAgrupado': 'indexTratamento',
        'prod_sc_ha_corr': 'Prod@13.5% (sc/ha)',
        'nome': 'Híbrido',
        'nomeFazenda': 'Fazenda'
    })
    # Reordena colunas
    colunas_frequencia = ['fazendaRef', 'Fazenda',
                          'indexTratamento', 'Híbrido', 'Prod@13.5% (sc/ha)']
    df_frequencia = df_frequencia[[
        c for c in colunas_frequencia if c in df_frequencia.columns]]
    # Calcula o maior valor de produção por fazendaRef
    if not df_frequencia.empty:
        # O nome da coluna de produção é 'Prod@13.5% (sc/ha)'
        df_frequencia['Prod_max_fazenda'] = df_frequencia.groupby(
            'fazendaRef')['Prod@13.5% (sc/ha)'].transform('max')
        df_frequencia['Diferença p/ Máx'] = df_frequencia['Prod_max_fazenda'] - \
            df_frequencia['Prod@13.5% (sc/ha)']
        df_frequencia['Prod Rel (%)'] = (
            df_frequencia['Prod@13.5% (sc/ha)'] / df_frequencia['Prod_max_fazenda'] * 100).round(1)
        # Cálculo do Ranking Global (antes dos filtros)

        def agrupa_index(idx):
            if 201 <= idx <= 221:
                return idx - 100
            return idx

        # Calcula o ranking global de cada híbrido dentro de cada fazenda
        _df_ranking_global = (
            st.session_state["df_avTratamentoMilho"].copy()
            .assign(indexTratamentoAgrupado=lambda df: df['indexTratamento'].apply(agrupa_index))
            .groupby(['fazendaRef', 'indexTratamentoAgrupado'])['prod_sc_ha_corr']
            .mean()
            .reset_index()
        )
        _df_ranking_global['Prod_max_fazenda'] = _df_ranking_global.groupby(
            'fazendaRef')['prod_sc_ha_corr'].transform('max')
        _df_ranking_global['Prod Rel (%)'] = (
            _df_ranking_global['prod_sc_ha_corr'] / _df_ranking_global['Prod_max_fazenda'] * 100).round(1)
        _df_ranking_global['Ranking_global'] = _df_ranking_global.groupby(
            'fazendaRef')['Prod Rel (%)'].rank(ascending=False, method='min').astype('Int64')
        _df_ranking_global = _df_ranking_global[[
            'fazendaRef', 'indexTratamentoAgrupado', 'Ranking_global']]
        # Junta o ranking global fixo
        df_frequencia = pd.merge(
            df_frequencia,
            _df_ranking_global,
            left_on=['fazendaRef', 'indexTratamento'],
            right_on=['fazendaRef', 'indexTratamentoAgrupado'],
            how='left'
        )
        df_frequencia = df_frequencia.drop(
            columns=['indexTratamentoAgrupado'], errors='ignore')
        # Exibe o ranking global fixo
        df_frequencia['Ranking'] = df_frequencia['Ranking_global']
        df_frequencia = df_frequencia.drop(
            columns=['Ranking_global'], errors='ignore')
        # Remover cálculo dinâmico do ranking (se existir)
    # Reordena colunas para exibição
    colunas_frequencia = [
        'fazendaRef', 'Fazenda', 'indexTratamento', 'Híbrido', 'Prod@13.5% (sc/ha)',
        'Prod_max_fazenda', 'Diferença p/ Máx', 'Prod Rel (%)', 'Ranking'
    ]
    df_frequencia = df_frequencia[[
        c for c in colunas_frequencia if c in df_frequencia.columns]]

    # =========================
    # Gráfico de frequência do ranking fixo por híbrido
    # =========================
    if isinstance(df_frequencia, pd.DataFrame) and not df_frequencia.empty:
        freq_ranking = (
            df_frequencia
            .groupby(['Híbrido', 'Ranking'])
            .size()
            .reset_index()
            .rename(columns={0: 'Frequência'})
        )
        import plotly.express as px
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
                Frequência de Rankings por Híbrido (Ranking Global)
            </div>
            """,
            unsafe_allow_html=True
        )
        # Garante que o eixo x (Ranking) vai de 1 a 21, mesmo que faltem valores
        ordem_ranking = list(range(1, 22))
        freq_ranking['Ranking'] = pd.Categorical(
            freq_ranking['Ranking'], categories=ordem_ranking, ordered=True)
        fig_freq = px.bar(
            freq_ranking,
            x='Ranking',
            y='Frequência',
            color='Híbrido',
            barmode='group',
            text='Frequência',
            labels={'Ranking': 'Ranking',
                    'Frequência': 'Nº de Fazendas', 'Híbrido': 'Híbrido'},
            title='Frequência de Rankings por Híbrido'
        )
        fig_freq.update_layout(
            xaxis=dict(type='category', title_font=dict(
                size=20, color='black'), tickfont=dict(size=18, color='black')),
            yaxis=dict(title_font=dict(size=20, color='black'),
                       tickfont=dict(size=18, color='black')),
            font=dict(size=18, color='black'),
            legend_title_text='Híbrido',
            legend=dict(font=dict(size=16, color='black')),
            height=600,
            margin=dict(t=120)
        )
        fig_freq.update_xaxes(categoryorder='array',
                              categoryarray=list(range(1, 22)))
        fig_freq.update_traces(
            textfont=dict(size=20, color='black'),
            textposition='outside',
            cliponaxis=False
        )
        st.plotly_chart(fig_freq, use_container_width=True)


# Exibe em um expander
    # with st.expander('Tabela de Frequência de Resposta (por fazenda e híbrido)', expanded=False):
    # st.dataframe(df_frequencia, use_container_width=True)
    # Botão para download
    # buffer_freq = io.BytesIO()
    # if isinstance(df_frequencia, np.ndarray):
    # df_frequencia = pd.DataFrame(df_frequencia)
    # with pd.ExcelWriter(buffer_freq, engine='xlsxwriter') as writer:
    # df_frequencia.to_excel(writer, index=False)
    # buffer_freq.seek(0)
    # st.download_button(
    # label='⬇️ Baixar Excel (Frequência de Resposta)',
    # data=buffer_freq,
    # file_name='frequencia_resposta.xlsx',
    # mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    # )
else:
    st.warning(
        'Colunas necessárias para o agrupamento não encontradas no DataFrame.')

# =========================
# Heatmap de Produção Relativa por Híbrido e Fazenda
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
        <h2 style="margin-bottom: 0.2em; color: #22223b; font-size: 18px;">Frequência de Resposta</h2>
        <h4 style="margin-top: 0; color: #4a4e69; font-weight: 400; font-size: 15px;">
            Produtividade relativa do híbrido em relação ao híbrido de maior produtividade do local.
        </h4>
    </div>
    """,
    unsafe_allow_html=True
)
if isinstance(df_frequencia, np.ndarray):
    df_frequencia = pd.DataFrame(df_frequencia)
if not df_frequencia.empty and all(col in df_frequencia.columns for col in ['Híbrido', 'Fazenda', 'Prod Rel (%)']):
    st.markdown("""
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
        Mapa de Frequência e Produção Rekativa de Híbridos nos Diferentes Locais
    </div>
    """, unsafe_allow_html=True)
    # Pivot para formato de matriz, usando média para resolver duplicidade
    df_heatmap = df_frequencia.pivot_table(
        index='Fazenda', columns='Híbrido', values='Prod Rel (%)', aggfunc='mean'
    )
    # Escala customizada fornecida pelo usuário
    escala_de_cores = [
        (0.00, "lightcoral"),
        (0.35, "lightcoral"),
        (0.45, "lightyellow"),
        (0.55, "lightyellow"),
        (0.70, "lightgreen"),
        (0.80, "mediumseagreen"),
        (1.00, "green")
    ]
    fig = px.imshow(
        df_heatmap,
        labels=dict(x="Híbrido", y="Fazenda", color="Prod Rel (%)"),
        color_continuous_scale=escala_de_cores,
        aspect='auto',
        text_auto=True,
        zmin=0,
        zmax=100
    )
    fig.update_layout(
        xaxis_title="Híbrido",
        yaxis_title="Fazenda",
        margin=dict(l=40, r=40, t=40, b=40),
        height=500,
        font=dict(size=18),  # Fonte geral maior
        xaxis=dict(title_font=dict(size=20, color='black'),
                   tickfont=dict(size=16, color='black')),
        yaxis=dict(title_font=dict(size=20, color='black'),
                   tickfont=dict(size=16, color='black')),
        coloraxis_colorbar=dict(title_font=dict(
            size=18, color='black'), tickfont=dict(size=16, color='black')),
    )
    # Aumenta fonte e coloca negrito nos rótulos dos valores
    fig.update_traces(textfont=dict(
        size=14, family="Arial Black, Arial, sans-serif", color="black"))
    st.plotly_chart(fig, use_container_width=True)

    # Exibe df_frequencia_visualizacao em um AgGrid abaixo do gráfico
    df_frequencia_visualizacao = df_frequencia.copy()
    if 'Ranking' not in df_frequencia_visualizacao.columns and 'Ranking' in df_frequencia.columns:
        df_frequencia_visualizacao['Ranking'] = df_frequencia['Ranking']
    if 'fazendaRef' in df_frequencia_visualizacao.columns:
        df_frequencia_visualizacao = df_frequencia_visualizacao.drop(columns=[
                                                                     'fazendaRef'])

# (após todos os gráficos e heatmaps)

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
        Tabela de Frequência de Resposta por Híbrido e Local
    </div>
    """,
    unsafe_allow_html=True
)
if df_frequencia_visualizacao is not None and not df_frequencia_visualizacao.empty:
    gb_freq = GridOptionsBuilder.from_dataframe(df_frequencia_visualizacao)
    colunas_formatar_freq = {
        'Prod@13.5% (sc/ha)': 1,
        'Prod_max_fazenda': 1,
        'Diferença p/ Máx': 1,
        'Prod Rel (%)': 1
    }
    for col in df_frequencia_visualizacao.columns:
        if col in colunas_formatar_freq:
            casas = colunas_formatar_freq[col]
            gb_freq.configure_column(
                col,
                headerClass='ag-header-bold',
                menuTabs=['generalMenuTab', 'filterMenuTab', 'columnsMenuTab'],
                valueFormatter=f"value != null ? value.toFixed({casas}) : ''"
            )
        else:
            gb_freq.configure_column(
                col,
                headerClass='ag-header-bold',
                menuTabs=['generalMenuTab', 'filterMenuTab', 'columnsMenuTab']
            )
    gb_freq.configure_default_column(
        editable=False, groupable=True, filter=True, resizable=True, cellStyle={'fontSize': '12px'})
    gb_freq.configure_grid_options(headerHeight=30)
    custom_css_freq = {
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
    grid_options_freq = gb_freq.build()
    if isinstance(df_frequencia_visualizacao, pd.Series):
        df_frequencia_visualizacao = df_frequencia_visualizacao.to_frame().T
    AgGrid(
        df_frequencia_visualizacao,
        gridOptions=grid_options_freq,
        enable_enterprise_modules=True,
        fit_columns_on_grid_load=False,
        theme="streamlit",
        height=500,
        reload_data=True,
        custom_css=custom_css_freq
    )
    buffer_freq_vis = io.BytesIO()
    # O uso de BytesIO com pd.ExcelWriter é suportado em tempo de execução, mas pode gerar falso positivo no linter.
    # type: ignore
    with pd.ExcelWriter(buffer_freq_vis, engine='xlsxwriter') as writer:  # type: ignore
        df_frequencia_visualizacao.to_excel(writer, index=False)
    buffer_freq_vis.seek(0)
    st.download_button(
        label='⬇️ Baixar Excel (Tabela Frequência Visualização)',
        data=buffer_freq_vis,
        file_name='frequencia_visualizacao.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
else:
    st.info("Nenhum dado disponível para exibir na tabela. Ajuste os filtros ou carregue os dados.")

# Exibe o heatmap de Ranking APÓS a tabela AgGrid
if not df_frequencia.empty and all(col in df_frequencia.columns for col in ['Híbrido', 'Fazenda', 'Ranking']):
    st.markdown("""
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
        Mapa de Ranking dos Híbridos nos Diferentes Locais
    </div>
    """, unsafe_allow_html=True)
    df_heatmap_ranking = df_frequencia.pivot_table(
        index='Fazenda', columns='Híbrido', values='Ranking', aggfunc='mean'
    )
    escala_de_cores = [
        (0.00, "forestgreen"),
        (0.25, "green"),
        (0.50, "mediumseagreen"),
        (0.75, "lightgreen"),
        (1.00, "honeydew")
    ]
    import plotly.express as px
    fig_ranking = px.imshow(
        df_heatmap_ranking,
        labels=dict(x="Híbrido", y="Fazenda", color="Ranking"),
        color_continuous_scale=escala_de_cores,
        aspect='auto',
        text_auto=True,
        zmin=1,
        zmax=21
    )
    fig_ranking.data[0].hovertemplate = (
        'Fazenda: %{y}<br>Híbrido: %{x}<br>'
        'Ranking: %{z:.1f}<extra></extra>'
    )
    fig_ranking.update_layout(
        xaxis_title="Híbrido",
        yaxis_title="Fazenda",
        margin=dict(l=40, r=40, t=40, b=40),
        height=500,
        font=dict(size=20, color='black'),
        xaxis=dict(title_font=dict(size=22, color='black'),
                   tickfont=dict(size=18, color='black')),
        yaxis=dict(title_font=dict(size=22, color='black'),
                   tickfont=dict(size=18, color='black')),
        coloraxis_colorbar=dict(title_font=dict(
            size=20, color='black'), tickfont=dict(size=18, color='black')),
    )
    fig_ranking.update_traces(textfont=dict(
        size=14, color="black", family="Arial Black, Arial, sans-serif"))
    st.plotly_chart(fig_ranking, use_container_width=True)
