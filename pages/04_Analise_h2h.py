import streamlit as st
import pandas as pd
import io
from st_aggrid import AgGrid, GridOptionsBuilder
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import gaussian_kde
from plotly.graph_objs import Scatter
from itertools import product
from st_aggrid import JsCode

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
                Análise Head to Head de Híbridos de Milho
            </h1>
            <h3 style="margin-top: 0; color: #e0e0e0; font-weight: 400; font-size: 1.2em;">
                Comparação direta entre híbridos, mostrando vitórias, diferenças médias de produtividade e desempenho relativo nos mesmos ambientes
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
# Botão na sidebar para rodar análise H2H (antes dos filtros)
# =========================
with st.sidebar:
    st.markdown(
        '''
        <div style="margin-bottom: 18px; display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.5em; color: #0070C0;">⚡Análise H2H</span>
            <span style="flex:1;">
        ''', unsafe_allow_html=True)
    if st.button('Rodar Análise H2H (Head-to-Head)', key='btn_h2h', use_container_width=True):
        st.session_state['run_h2h'] = True
        st.session_state['show_h2h_done'] = True
    st.markdown('</span></div>', unsafe_allow_html=True)
    # Mostra a mensagem de sucesso em verde antes do divider
    if st.session_state.get('show_h2h_done', False):
        st.markdown(
            '<div style="background-color:#d4edda;border-left:6px solid #28a745;padding:12px 18px;margin-bottom:12px;border-radius:6px;font-size:1.05em;color:#155724;font-weight:600;">✅ Análise H2H concluída! Veja os resultados ao lado.</div>',
            unsafe_allow_html=True
        )
        st.session_state['show_h2h_done'] = False
    st.markdown('---')


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
# st.subheader("Produção e Componentes Produtivos")
# st.markdown(
#     """
#     <div style="
#         background-color: #e7f0fa;
#         border-left: 6px solid #0070C0;
#         padding: 12px 18px;
#         margin-bottom: 12px;
#         border-radius: 6px;
#         font-size: 1.15em;
#         color: #22223b;
#         font-weight: 600;
#     ">
#         Resultados por Híbrido
#     </div>
#     """,
#     unsafe_allow_html=True
# )
# with st.expander("Ver tabela de Produção e Componentes Produtivos", expanded=False):
#     AgGrid(
#         df_analise_conjunta_visualizacao,   # DataFrame a ser exibido
#         gridOptions=grid_options,           # Opções de configuração do grid
#         enable_enterprise_modules=True,     # Libera recursos avançados do AgGrid
#         fit_columns_on_grid_load=False,     # Não força ajuste automático das colunas
#         theme="streamlit",                # Tema visual do grid
#         height=500,                        # Altura da tabela em pixels
#         reload_data=True,                  # Recarrega dados ao atualizar
#         custom_css=custom_css              # Aplica o CSS customizado definido acima
#     )
#
#     # Botão para exportar em Excel o DataFrame customizado
#     buffer = io.BytesIO()
#     df_analise_conjunta_visualizacao.to_excel(
#         buffer, index=False)  # type: ignore
#     buffer.seek(0)
#     st.download_button(
#         label="⬇️ Baixar Excel (Produção e Componentes Produtivos)",
#         data=buffer,
#         file_name="producao_componentes.xlsx",
#         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )

# =========================
# Agrupamento por fazendaRef e pares de indexTratamento (Frequência de Resposta)
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


# Cria coluna auxiliar para agrupamento
if 'indexTratamento' in df_analise_conjunta.columns:
    df_analise_conjunta['indexTratamentoAgrupado'] = df_analise_conjunta['indexTratamento'].apply(
        agrupa_index)
else:
    st.warning('Coluna indexTratamento não encontrada no DataFrame.')

# Agrupa por fazendaRef e indexTratamentoAgrupado, calculando a média das colunas desejadas
if all(col in df_analise_conjunta.columns for col in ['fazendaRef', 'indexTratamento', 'nomeFazenda', 'nome', 'humidade', 'numPlantas_ha', 'prod_sc_ha_corr']):
    colunas_agrupamento = ['fazendaRef', 'indexTratamento']
    colunas_agrupar = ['humidade', 'numPlantas_ha', 'prod_sc_ha_corr']
    df_agrupado = (
        df_analise_conjunta
        .groupby(['fazendaRef', 'indexTratamento'], as_index=False)[colunas_agrupar]
        .mean()
    )
    # Recupera o nome do híbrido e nomeFazenda para cada par (fazendaRef, indexTratamento)
    df_nome = (
        df_analise_conjunta
        .groupby(['fazendaRef', 'indexTratamento'])[['nome', 'nomeFazenda']]
        .first()
        .reset_index()
    )
    # Junta nome e nomeFazenda ao DataFrame agrupado
    df_agrupado = pd.merge(
        df_agrupado,
        df_nome,
        on=['fazendaRef', 'indexTratamento'],
        how='left'
    )
    # Reordena as colunas
    colunas_final = ['fazendaRef', 'nomeFazenda', 'indexTratamento',
                     'nome', 'humidade', 'numPlantas_ha', 'prod_sc_ha_corr']
    df_agrupado = df_agrupado[[
        c for c in colunas_final if c in df_agrupado.columns]]
    # Visualização com AgGrid
    # st.subheader('Tabela Agrupada por Fazenda e Híbrido')
    # if not isinstance(df_agrupado, pd.DataFrame):
    #     df_agrupado = pd.DataFrame(df_agrupado)
    # gb_agrupado = GridOptionsBuilder.from_dataframe(df_agrupado)
    # gb_agrupado.configure_default_column(
    #     editable=False, groupable=True, filter=True, resizable=True, cellStyle={'fontSize': '12px'})
    # gb_agrupado.configure_grid_options(headerHeight=30)
    # grid_options_agrupado = gb_agrupado.build()
    # custom_css_agrupado = {
    #     ".ag-header-cell-label": {"font-weight": "bold", "font-size": "12px", "color": "black"},
    #     ".ag-cell": {"color": "black", "font-size": "12px"}
    # }
    # AgGrid(
    #     df_agrupado,
    #     gridOptions=grid_options_agrupado,
    #     enable_enterprise_modules=True,
    #     fit_columns_on_grid_load=False,
    #     theme="streamlit",
    #     height=500,
    #     reload_data=True,
    #     custom_css=custom_css_agrupado
    # )
    # # Botão para exportar em Excel
    # buffer_agrupado = io.BytesIO()
    # df_agrupado.to_excel(buffer_agrupado, index=False)  # type: ignore
    # buffer_agrupado.seek(0)
    # st.download_button(
    #     label='⬇️ Baixar Excel (Tabela Agrupada)',
    #     data=buffer_agrupado,
    #     file_name='tabela_agrupada.xlsx',
    #     mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    # )

    # Criação do DataFrame df_analise_h2h como cópia do df_agrupado
    df_analise_h2h = df_agrupado.copy()

# =========================
# Criação do DataFrame df_h2h para visualização e exportação
# =========================

    # Visualização do DataFrame df_analise_h2h
    # st.markdown('---')
    # st.subheader(
    #    'Visualização do DataFrame df_analise_h2h (cópia do agrupado)')
    # st.dataframe(df_analise_h2h, use_container_width=True)

    # =========================
    # Análise Head to Head (H2H) detalhada conforme solicitado
    # =========================
    if st.session_state.get('run_h2h', False):
        resultados_h2h = []
        hibridos = pd.Series(df_agrupado['nome']).dropna().unique()
        locais = pd.Series(df_agrupado['fazendaRef']).dropna().unique()
        for head, check in product(hibridos, repeat=2):
            if head != check:
                for local in locais:
                    row_head = df_agrupado[(df_agrupado['nome'] == head) & (
                        df_agrupado['fazendaRef'] == local)]
                    row_check = df_agrupado[(df_agrupado['nome'] == check) & (
                        df_agrupado['fazendaRef'] == local)]
                    if not isinstance(row_head, pd.DataFrame):
                        row_head = pd.DataFrame(row_head)
                    if not isinstance(row_check, pd.DataFrame):
                        row_check = pd.DataFrame(row_check)
                    if not row_head.empty and not row_check.empty:
                        # Calcula diferença e vitória
                        head_mean = row_head.iloc[0]['prod_sc_ha_corr'] if 'prod_sc_ha_corr' in row_head else None
                        check_mean = row_check.iloc[0]['prod_sc_ha_corr'] if 'prod_sc_ha_corr' in row_check else None
                        diff = head_mean - check_mean if head_mean is not None and check_mean is not None else None
                        vitoria = int(diff > 0) if diff is not None else None
                        # Para granularidade por local, cada comparação é 1
                        resultados_h2h.append({
                            'fazendaRef': local,
                            'nomeFazenda': row_head.iloc[0]['nomeFazenda'] if 'nomeFazenda' in row_head else None,
                            'indexTratamento_Head': row_head.iloc[0]['indexTratamento'] if 'indexTratamento' in row_head else None,
                            'indexTratamento_Check': row_check.iloc[0]['indexTratamento'] if 'indexTratamento' in row_check else None,
                            'Head': head,
                            'Check': check,
                            'Head_umd': row_head.iloc[0]['humidade'] if 'humidade' in row_head else None,
                            'Check_umd': row_check.iloc[0]['humidade'] if 'humidade' in row_check else None,
                            'Head_numPlantas_ha': row_head.iloc[0]['numPlantas_ha'] if 'numPlantas_ha' in row_head else None,
                            'Check_numPlantas_ha': row_check.iloc[0]['numPlantas_ha'] if 'numPlantas_ha' in row_check else None,
                            'Head_mean': head_mean,
                            'Check_mean': check_mean,
                            'Difference': diff,
                            'Number_of_Win': vitoria,
                            'Percentage_of_Win': vitoria * 100 if vitoria is not None else None,
                            'Number_Of_Comparison': 1
                        })
        df_resultado_h2h = pd.DataFrame(resultados_h2h)
        st.session_state['df_resultado_h2h'] = df_resultado_h2h
        st.session_state['run_h2h'] = False

    # Exibir resultado se existir
    if 'df_resultado_h2h' in st.session_state and not st.session_state['df_resultado_h2h'].empty:
        st.subheader('Análise H2H')
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
                Resultados da análise h2h
            </div>
            """,
            unsafe_allow_html=True
        )
        # Renomear e reordenar colunas conforme solicitado
        df_h2h_vis = st.session_state['df_resultado_h2h'].copy()
        colunas_renomear = {
            'fazendaRef': 'fazendaRef',
            'nomeFazenda': 'Local (Fazenda)',
            'Head': 'Head',
            'Check': 'Check',
            'Head_mean': 'Head prod@13.5% (sc/ha)',
            'Check_mean': 'Check prod@13.5% (sc/ha)',
            'Head_umd': 'Head umd (%)',
            'Check_umd': 'Check umd (%)',
            'Head_numPlantas_ha': 'Head pop (plts/ha)',
            'Check_numPlantas_ha': 'Check pop (plts/ha)',
            'indexTratamento_Head': 'indexTratamento Head',
            'indexTratamento_Check': 'indexTratamento Check',
            'Difference': 'Diferença (sc/ha)',
            'Number_of_Win': 'Vitórias',
            'Percentage_of_Win': 'Vitórias (%)',
            'Number_Of_Comparison': 'Comparações',
        }
        ordem_colunas = [
            'fazendaRef',
            'nomeFazenda',
            'Head',
            'Check',
            'indexTratamento_Head',
            'indexTratamento_Check',
            'Head_mean',
            'Check_mean',
            'Difference',
            'Number_of_Win',
            'Percentage_of_Win',
            'Number_Of_Comparison',
            'Head_umd',
            'Check_umd',
            'Head_numPlantas_ha',
            'Check_numPlantas_ha',
        ]
        ordem_colunas_existentes = [
            c for c in ordem_colunas if c in df_h2h_vis.columns]
        df_h2h_vis = df_h2h_vis[ordem_colunas_existentes].rename(
            columns=colunas_renomear)

        # Configuração do AgGrid
        gb_h2h = GridOptionsBuilder.from_dataframe(df_h2h_vis)
        colunas_1_casa = [
            'Head prod@13.5% (sc/ha)',
            'Check prod@13.5% (sc/ha)',
            'Head umd (%)',
            'Check umd (%)'
        ]
        colunas_0_casa = [
            'Head pop (plts/ha)',
            'Check pop (plts/ha)'
        ]
        for col in df_h2h_vis.columns:
            if col in colunas_1_casa:
                gb_h2h.configure_column(
                    col,
                    headerClass='ag-header-bold',
                    menuTabs=['generalMenuTab',
                              'filterMenuTab', 'columnsMenuTab'],
                    valueFormatter="value != null ? value.toFixed(1) : ''"
                )
            elif col in colunas_0_casa:
                gb_h2h.configure_column(
                    col,
                    headerClass='ag-header-bold',
                    menuTabs=['generalMenuTab',
                              'filterMenuTab', 'columnsMenuTab'],
                    valueFormatter="value != null ? value.toFixed(0) : ''"
                )
            else:
                gb_h2h.configure_column(
                    col,
                    headerClass='ag-header-bold',
                    menuTabs=['generalMenuTab',
                              'filterMenuTab', 'columnsMenuTab']
                )
        gb_h2h.configure_default_column(editable=False, groupable=True,
                                        filter=True, resizable=True, cellStyle={'fontSize': '12px'})
        gb_h2h.configure_grid_options(headerHeight=30)
        grid_options_h2h = gb_h2h.build()
        custom_css_h2h = {
            ".ag-header-cell-label": {"font-weight": "bold", "font-size": "12px", "color": "black"},
            ".ag-cell": {"color": "black", "font-size": "12px"}
        }
        with st.expander("Ver tabela da Análise H2H", expanded=True):
            AgGrid(
                df_h2h_vis,
                gridOptions=grid_options_h2h,
                enable_enterprise_modules=True,
                fit_columns_on_grid_load=False,
                theme="streamlit",
                height=500,
                reload_data=True,
                custom_css=custom_css_h2h,
                key="aggrid_h2h_vis"
            )
            # Botão para exportar em Excel
            buffer_h2h = io.BytesIO()
            df_h2h_vis.to_excel(buffer_h2h, index=False)  # type: ignore
            buffer_h2h.seek(0)
            st.download_button(
                label='⬇️ Baixar Excel (Análise H2H)',
                data=buffer_h2h,
                file_name='analise_h2h.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

        # =========================
        # Selecione os cultivares - Filtros Head e Check (detalhamento H2H)
        # =========================
        st.markdown('<h3 style="margin-top: 2em; margin-bottom: 0.5em; color: #0070C0; font-weight: 700;">Selecione os híbridos</h3>', unsafe_allow_html=True)
        # Usa o DataFrame da análise H2H para opções de Head/Check
        df_h2h = st.session_state['df_resultado_h2h'] if 'df_resultado_h2h' in st.session_state else None
        if df_h2h is not None and not df_h2h.empty:
            col1, colx, col2 = st.columns([5, 1, 5])
            with col1:
                head_options = sorted(df_h2h['Head'].dropna().unique())
                head_selected = st.selectbox(
                    'Híbrido Head', head_options, key='h2h_head_dropdown')
            with colx:
                st.markdown(
                    '<div style="text-align:center;font-size:2em;font-weight:700;line-height:2.5em;">×</div>', unsafe_allow_html=True)
            with col2:
                # Remove o Head das opções de Check
                check_options = sorted(
                    [c for c in df_h2h['Check'].dropna().unique() if c != head_selected])
                check_selected = st.selectbox(
                    'Híbrido Check', options=check_options, key='h2h_check_dropdown')

            # Buscar os locais onde ambos os híbridos participaram juntos
            # Usar df_agrupado para granularidade por local
            df_agrup = None
            if 'df_agrupado' in locals():
                df_agrup = df_agrupado.copy()
            elif 'df_agrupado' in globals():
                df_agrup = df_agrupado.copy()
            elif 'df_analise_h2h' in st.session_state:
                df_agrup = st.session_state['df_analise_h2h'].copy()

            if df_agrup is not None and head_selected and check_selected:
                registros = []
                check = check_selected
                head_locs = set(
                    df_agrup[df_agrup['nome'] == head_selected]['fazendaRef'])
                check_locs = set(
                    df_agrup[df_agrup['nome'] == check]['fazendaRef'])
                locais_comuns = head_locs & check_locs
                for loc in sorted(locais_comuns):
                    row_head = df_agrup[(df_agrup['fazendaRef'] == loc) & (
                        df_agrup['nome'] == head_selected)]
                    row_check = df_agrup[(df_agrup['fazendaRef'] == loc) & (
                        df_agrup['nome'] == check)]
                    if not isinstance(row_head, pd.DataFrame):
                        row_head = pd.DataFrame(row_head)
                    if not isinstance(row_check, pd.DataFrame):
                        row_check = pd.DataFrame(row_check)
                    if not row_head.empty and not row_check.empty:
                        head_prod = row_head.iloc[0]['prod_sc_ha_corr'] if 'prod_sc_ha_corr' in row_head else None
                        check_prod = row_check.iloc[0]['prod_sc_ha_corr'] if 'prod_sc_ha_corr' in row_check else None
                        diff = round(
                            head_prod - check_prod, 1) if head_prod is not None and check_prod is not None else None
                        head_pop = row_head.iloc[0]['numPlantas_ha'] if 'numPlantas_ha' in row_head else None
                        check_pop = row_check.iloc[0]['numPlantas_ha'] if 'numPlantas_ha' in row_check else None
                        head_pop_int = int(round(head_pop)) if isinstance(
                            head_pop, (int, float)) and pd.notnull(head_pop) else None
                        check_pop_int = int(round(check_pop)) if isinstance(
                            check_pop, (int, float)) and pd.notnull(check_pop) else None
                        registros.append({
                            'Local (Fazenda)': row_head.iloc[0]['nomeFazenda'] if 'nomeFazenda' in row_head else loc,
                            'Head': head_selected,
                            'Head pop (plts/ha)': head_pop_int,
                            'Head umd (%)': round(row_head.iloc[0]['humidade'], 1) if 'humidade' in row_head else None,
                            'Head prod@13.5% (sc/ha)': round(head_prod, 1) if head_prod is not None else None,
                            'Check': check,
                            'Check pop (plts/ha)': check_pop_int,
                            'Check umd (%)': round(row_check.iloc[0]['humidade'], 1) if 'humidade' in row_check else None,
                            'Check prod@13.5% (sc/ha)': round(check_prod, 1) if check_prod is not None else None,
                            'Diferença (sc/ha)': diff
                        })
                df_h2h_detalhe = pd.DataFrame(registros)
            else:
                df_h2h_detalhe = pd.DataFrame()

            # Visualização simples em AgGrid
            st.markdown("""
                <div style='background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 10px 18px; margin-bottom: 8px; border-radius: 6px; font-size: 1.1em; color: #22223b; font-weight: 600;'>
                    Comparativo H2H - Detalhamento por Local
                </div>
            """, unsafe_allow_html=True)
            if not isinstance(df_h2h_detalhe, pd.DataFrame):
                if hasattr(df_h2h_detalhe, 'to_frame'):
                    df_h2h_detalhe = df_h2h_detalhe.to_frame().T
                else:
                    df_h2h_detalhe = pd.DataFrame()

            # Funções JS para coloração condicional
            cell_style_diff = JsCode("""
            function(params) {
                if (params.value > 1) {
                    return {
                        'backgroundColor': '#01B8AA',
                        'color': 'black',
                        'fontWeight': 'bold'
                    }
                } else if (params.value < -1) {
                    return {
                        'backgroundColor': '#FD625E',
                        'color': 'black',
                        'fontWeight': 'bold'
                    }
                } else {
                    return {
                        'backgroundColor': '#F2C80F',
                        'color': 'black',
                        'fontWeight': 'bold'
                    }
                }
            }
            """)
            cell_style_head = JsCode("""
            function(params) {
                let head = params.data['Head prod@13.5% (sc/ha)'];
                let check = params.data['Check prod@13.5% (sc/ha)'];
                if (head == null || check == null) return {};
                if (Math.abs(head - check) <= 1) {
                    return {'backgroundColor': '#F2C80F', 'color': 'black', 'fontWeight': 'bold'};
                } else if (head > check) {
                    return {'backgroundColor': '#01B8AA', 'color': 'black', 'fontWeight': 'bold'};
                } else if (head < check) {
                    return {'backgroundColor': '#FD625E', 'color': 'black', 'fontWeight': 'bold'};
                } else {
                    return {};
                }
            }
            """)
            cell_style_check = JsCode("""
            function(params) {
                let head = params.data['Head prod@13.5% (sc/ha)'];
                let check = params.data['Check prod@13.5% (sc/ha)'];
                if (head == null || check == null) return {};
                if (Math.abs(head - check) <= 1) {
                    return {'backgroundColor': '#F2C80F', 'color': 'black', 'fontWeight': 'bold'};
                } else if (head > check) {
                    return {'backgroundColor': '#FD625E', 'color': 'black', 'fontWeight': 'bold'};
                } else if (head < check) {
                    return {'backgroundColor': '#01B8AA', 'color': 'black', 'fontWeight': 'bold'};
                } else {
                    return {};
                }
            }
            """)
            gb_h2h_detalhe = GridOptionsBuilder.from_dataframe(df_h2h_detalhe)
            # Coloração condicional para Head prod@13.5% (sc/ha)
            if 'Head prod@13.5% (sc/ha)' in df_h2h_detalhe.columns:
                gb_h2h_detalhe.configure_column(
                    'Head prod@13.5% (sc/ha)',
                    valueFormatter="value != null ? value.toFixed(1) : ''",
                    cellStyle=cell_style_head
                )
            # Coloração condicional para Check prod@13.5% (sc/ha)
            if 'Check prod@13.5% (sc/ha)' in df_h2h_detalhe.columns:
                gb_h2h_detalhe.configure_column(
                    'Check prod@13.5% (sc/ha)',
                    valueFormatter="value != null ? value.toFixed(1) : ''",
                    cellStyle=cell_style_check
                )
            # Coloração condicional para Diferença (sc/ha)
            if 'Diferença (sc/ha)' in df_h2h_detalhe.columns:
                gb_h2h_detalhe.configure_column(
                    'Diferença (sc/ha)',
                    valueFormatter="value != null ? value.toFixed(1) : ''",
                    cellStyle=cell_style_diff
                )
            # Demais colunas padrão
            for col in df_h2h_detalhe.columns:
                if col not in ['Head prod@13.5% (sc/ha)', 'Check prod@13.5% (sc/ha)', 'Diferença (sc/ha)']:
                    gb_h2h_detalhe.configure_column(
                        col,
                        headerClass='ag-header-bold',
                        menuTabs=['generalMenuTab',
                                  'filterMenuTab', 'columnsMenuTab']
                    )
            gb_h2h_detalhe.configure_default_column(
                editable=False, groupable=True, filter=True, resizable=True, cellStyle={'fontSize': '12px'})
            gb_h2h_detalhe.configure_grid_options(headerHeight=30)
            custom_css_h2h_detalhe = {
                ".ag-header-cell-label": {"font-weight": "bold", "font-size": "12px", "color": "black"},
                ".ag-cell": {"color": "black", "font-size": "12px"}
            }
            AgGrid(
                df_h2h_detalhe,
                gridOptions=gb_h2h_detalhe.build(),
                enable_enterprise_modules=True,
                fit_columns_on_grid_load=False,
                theme="streamlit",
                height=400,
                reload_data=True,
                custom_css=custom_css_h2h_detalhe,
                allow_unsafe_jscode=True
            )
            # Reordena as colunas para que 'Diferença (sc/ha)' fique por último
            if 'Diferença (sc/ha)' in df_h2h_detalhe.columns:
                cols = [c for c in df_h2h_detalhe.columns if c !=
                        'Diferença (sc/ha)'] + ['Diferença (sc/ha)']
                df_h2h_detalhe = df_h2h_detalhe[cols]
            # Botão para exportar em Excel abaixo da visualização
            buffer_h2h_detalhe = io.BytesIO()
            df_h2h_detalhe.to_excel(
                buffer_h2h_detalhe, index=False)  # type: ignore
            buffer_h2h_detalhe.seek(0)
            st.download_button(
                label='⬇️ Baixar Excel (Tabela Head to Head Detalhada)',
                data=buffer_h2h_detalhe,
                file_name='tabela_h2h_detalhada.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

            # =========================
            # Cartões de Resultados (Cards)
            # =========================
            if not df_h2h_detalhe.empty and 'Diferença (sc/ha)' in df_h2h_detalhe.columns:
                num_locais = df_h2h_detalhe.shape[0]
                vitorias = (df_h2h_detalhe["Diferença (sc/ha)"] > 1).sum()
                max_diff = df_h2h_detalhe.loc[df_h2h_detalhe["Diferença (sc/ha)"]
                                              > 1, "Diferença (sc/ha)"].max()
                if pd.isna(max_diff):
                    max_diff = 0
                media_diff_vitorias = df_h2h_detalhe.loc[df_h2h_detalhe[
                    "Diferença (sc/ha)"] > 1, "Diferença (sc/ha)"].mean()
                if pd.isna(media_diff_vitorias):
                    media_diff_vitorias = 0
                empates = ((df_h2h_detalhe["Diferença (sc/ha)"] >= -1)
                           & (df_h2h_detalhe["Diferença (sc/ha)"] <= 1)).sum()
                derrotas = (df_h2h_detalhe["Diferença (sc/ha)"] < -1).sum()
                min_diff = df_h2h_detalhe.loc[df_h2h_detalhe["Diferença (sc/ha)"]
                                              < -1, "Diferença (sc/ha)"].min()
                if pd.isna(min_diff):
                    min_diff = 0
                media_diff_derrotas = df_h2h_detalhe.loc[df_h2h_detalhe[
                    "Diferença (sc/ha)"] < -1, "Diferença (sc/ha)"].mean()
                if pd.isna(media_diff_derrotas):
                    media_diff_derrotas = 0

                col4, col5, col6, col7 = st.columns(4)

                # 📍 Locais
                with col4:
                    st.markdown(f"""
                        <div style="background-color:#f2f2f2; padding:15px; border-radius:10px; text-align:center;">
                            <h5 style="font-weight:bold; color:#333;">📍 Número de Locais</h5>
                            <div style="font-size: 20px; font-weight:bold; color:#f2f2f2;">&nbsp;</div>
                            <h2 style="margin: 10px 0; color:#333; font-weight:bold; font-size: 4em;">{num_locais}</h2>
                            <div style="font-size: 20px; font-weight:bold; color:#f2f2f2;">&nbsp;</div>
                        </div>
                    """, unsafe_allow_html=True)

                # ✅ Vitórias
                with col5:
                    st.markdown(f"""
                        <div style="background-color:#01B8AA80; padding:15px; border-radius:10px; text-align:center;">
                            <h5 style="font-weight:bold; color:#004d47;">✅ Vitórias</h5>
                            <div style="font-size: 20px; font-weight:bold; color:#004d47;">Max: {max_diff:.1f} sc/ha</div>
                            <h2 style="margin: 10px 0; color:#004d47; font-weight:bold; font-size: 4em;">{vitorias}</h2>
                            <div style="font-size: 20px; font-weight:bold; color:#004d47;">Média: {media_diff_vitorias:.1f} sc/ha</div>
                        </div>
                    """, unsafe_allow_html=True)

                # ➖ Empates
                with col6:
                    st.markdown(f"""
                        <div style="background-color:#F2C80F80; padding:15px; border-radius:10px; text-align:center;">
                            <h5 style="font-weight:bold; color:#8a7600;">➖ Empates</h5>
                            <div style="font-size: 20px; font-weight:bold; color:#8a7600;">Entre -1 e 1 sc/ha</div>
                            <h2 style="margin: 10px 0; color:#8a7600; font-weight:bold; font-size: 4em;">{empates}</h2>
                            <div style="font-size: 20px; font-weight:bold; color:#F2C80F80;">&nbsp;</div>
                        </div>
                    """, unsafe_allow_html=True)

                # ❌ Derrotas
                with col7:
                    st.markdown(f"""
                        <div style="background-color:#FD625E80; padding:15px; border-radius:10px; text-align:center;">
                            <h5 style="font-weight:bold; color:#7c1f1c;">❌ Derrotas</h5>
                            <div style="font-size: 20px; font-weight:bold; color:#7c1f1c;">Min: {min_diff:.1f} sc/ha</div>
                            <h2 style="margin: 10px 0; color:#7c1f1c; font-weight:bold; font-size: 4em;">{derrotas}</h2>
                            <div style="font-size: 20px; font-weight:bold; color:#7c1f1c;">Média: {media_diff_derrotas:.1f} sc/ha</div>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown("")

            # 📊 Gráfico de Pizza
            col7, col8, col9 = st.columns([1, 2, 1])
            with col8:
                st.markdown("""
                    <div style="background-color: #f9f9f9; padding: 10px; border-radius: 12px; 
                                box-shadow: 0px 2px 5px rgba(0,0,0,0.1); text-align: center;">
                        <h4 style="margin-bottom: 0.5rem;">Resultado Geral do Head</h4>
                """, unsafe_allow_html=True)

                fig = go.Figure(data=[go.Pie(
                    labels=["Vitórias", "Empates", "Derrotas"],
                    values=[vitorias, empates, derrotas],
                    marker=dict(colors=["#01B8AA", "#F2C80F", "#FD625E"]),
                    hole=0.6,
                    textinfo='label+percent',
                    textposition='outside',
                    textfont=dict(size=16, color="black",
                                  family="Arial Black"),
                    pull=[0.04, 0.04, 0.04],
                )])

                fig.update_layout(
                    # aumenta margem inferior
                    margin=dict(t=10, b=80, l=10, r=10),
                    height=370,  # aumenta altura
                    showlegend=False
                )
                fig.update_traces(automargin=True)

                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # 📊 Gráfico de Diferença por Local (Head vs Check) - Ordenado e Horizontal
            if not df_h2h_detalhe.empty and 'Diferença (sc/ha)' in df_h2h_detalhe.columns:
                # st.markdown(
                # f"### <b>Diferença de Produtividade por Local - {head_selected} X {check_selected}</b>", unsafe_allow_html=True)
                # st.markdown("")

                # 🔍 Filtra dados com produtividade válida (> 0) antes do gráfico
                df_graf = df_h2h_detalhe.copy()
                if isinstance(df_graf, pd.DataFrame):
                    df_graf = df_graf[(df_graf["Head prod@13.5% (sc/ha)"] > 0)
                                      & (df_graf["Check prod@13.5% (sc/ha)"] > 0)]

                    # ✅ Ordena para visualização
                    if not df_graf.empty and 'Diferença (sc/ha)' in df_graf.columns:
                        df_graf_sorted = df_graf.sort_values(
                            by=["Diferença (sc/ha)"])  # type: ignore

                        cores_local = df_graf_sorted["Diferença (sc/ha)"].apply(
                            lambda x: "#01B8AA" if x > 1 else "#FD625E" if x < -1 else "#F2C80F"
                        )

                        # Substituir nome da fazenda por código na coluna 'Local (Fazenda)'
                        import unicodedata
                        dicionario_fazendas_local = {
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
                            "LUIZ PAULO PENNA": "SCR_MT"
                        }

                        def padroniza_nome_local(nome):
                            nome = nome.strip().upper()
                            nome = unicodedata.normalize('NFKD', nome).encode(
                                'ASCII', 'ignore').decode('ASCII')
                            return nome
                        dicionario_fazendas_local_padronizado = {padroniza_nome_local(
                            k): v for k, v in dicionario_fazendas_local.items()}

                        def substitui_nome_ou_codigo_local(nome):
                            nome_strip = nome.strip()
                            if '_' in nome_strip and nome_strip[-3:] in ["_GO", "_MS", "_MT", "_MA", "_TO", "_MG"]:
                                return nome_strip
                            return dicionario_fazendas_local_padronizado.get(padroniza_nome_local(nome_strip), nome_strip)
                        df_graf_sorted["Local (Fazenda)"] = df_graf_sorted["Local (Fazenda)"].apply(
                            substitui_nome_ou_codigo_local)

                        # Título e subtítulo no padrão da página
                        st.markdown(f"""
                            <div style='background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 10px 18px; margin-bottom: 8px; border-radius: 6px; font-size: 1.1em; color: #22223b; font-weight: 600;'>
                                Diferença de Produtividade por Local — <b>{head_selected} × {check_selected}</b>
                            </div>
                        """, unsafe_allow_html=True)

                        fig_diff_local = go.Figure()
                        fig_diff_local.add_trace(go.Bar(
                            y=df_graf_sorted["Local (Fazenda)"],
                            x=df_graf_sorted["Diferença (sc/ha)"],
                            orientation='h',
                            text=df_graf_sorted["Diferença (sc/ha)"].round(1),
                            textposition="outside",
                            textfont=dict(
                                size=13, family="Arial Black", color="black"),
                            marker_color=cores_local
                        ))

                        fig_diff_local.update_layout(
                            title=dict(
                                text=f"Diferença de Produtividade por Local — {head_selected} × {check_selected}",
                                font=dict(size=20, color="black")
                            ),
                            xaxis=dict(
                                title=dict(text="<b>Diferença (sc/ha)</b>", font=dict(
                                    size=14, family="Arial Black", color="black")),
                                tickfont=dict(
                                    size=13, family="Arial Black", color="black")
                            ),
                            yaxis=dict(
                                title=dict(
                                    text="<b>Local</b>", font=dict(size=14, family="Arial Black", color="black")),
                                tickfont=dict(
                                    size=13, family="Arial Black", color="black")
                            ),
                            margin=dict(t=30, b=30, l=90, r=30),
                            height=700,  # aumentada de 500 para 700
                            showlegend=False
                        )

                        st.plotly_chart(
                            fig_diff_local, use_container_width=True)

        # =========================
        # Análise MultiCheck (Head x Múltiplos Checks)
        # =========================
        st.markdown("""
            <div style='background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 14px 18px; margin-bottom: 8px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;'>
                Comparação Head x Múltiplos Checks
            </div>
        """, unsafe_allow_html=True)
        st.markdown("""
            <span style='font-size:0.98em; color:#555;'>
                Essa análise permite comparar um híbrido (Head) com vários outros (Checks) ao mesmo tempo.<br>                
            </span>
        """, unsafe_allow_html=True)
        st.markdown("---")

        # Usa df_analise_h2h como base
        df_multi_base = None
        if 'df_analise_h2h' in locals():
            df_multi_base = df_analise_h2h.copy()
        elif 'df_analise_h2h' in globals():
            df_multi_base = df_analise_h2h.copy()
        elif 'df_analise_h2h' in st.session_state:
            df_multi_base = st.session_state['df_analise_h2h'].copy()

        if df_multi_base is not None and not df_multi_base.empty:
            cultivares_unicos = pd.Series(
                df_multi_base['nome']).dropna().unique()
            head_unico = st.selectbox(
                "Híbrido Head", options=cultivares_unicos, key="multi_head")
            opcoes_checks = [c for c in cultivares_unicos if c != head_unico]
            checks_selecionados = st.multiselect(
                "Híbridos Check", options=opcoes_checks, key="multi_checks")

            if head_unico and checks_selecionados:
                # Monta df_resultado_h2h temporário para MultiCheck
                df_multi = st.session_state['df_resultado_h2h']
                df_multi = df_multi[(df_multi["Head"] == head_unico) & (
                    df_multi["Check"].isin(checks_selecionados))]

                if not df_multi.empty:
                    # Produtividade média do Head
                    prod_head_media = df_multi["Head_mean"].mean().round(1)

                    # Título atualizado com produtividade
                    st.markdown(
                        f"#### Híbrido Head: <b>{head_unico}</b> | Produtividade Média: <b>{prod_head_media} sc/ha</b>", unsafe_allow_html=True)

                    resumo = df_multi.groupby("Check").agg({
                        "Number_of_Win": "sum",
                        "Number_Of_Comparison": "sum",
                        "Check_mean": "mean"
                    }).reset_index()

                    resumo.rename(columns={
                        "Check": "Cultivar Check",
                        "Number_of_Win": "Vitórias",
                        "Number_Of_Comparison": "Num_Locais",
                        "Check_mean": "Prod_sc_ha_media"
                    }, inplace=True)

                    resumo["% Vitórias"] = (
                        resumo["Vitórias"] / resumo["Num_Locais"] * 100).round(1)
                    resumo["Prod_sc_ha_media"] = resumo["Prod_sc_ha_media"].round(
                        1)
                    resumo["Diferença Média"] = (
                        prod_head_media - resumo["Prod_sc_ha_media"]).round(1)

                    resumo = resumo[["Cultivar Check", "% Vitórias",
                                     "Num_Locais", "Prod_sc_ha_media", "Diferença Média"]]

                    # Exibe primeiro o gráfico, depois a tabela (um em cima do outro)
                    st.markdown("""
                        <div style='background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 10px 18px; margin-bottom: 8px; border-radius: 6px; font-size: 1.1em; color: #22223b; font-weight: 600;'>
                            Diferença Média de Produtividade
                        </div>
                    """, unsafe_allow_html=True)

                    fig_diff = go.Figure()
                    cores_personalizadas = resumo["Diferença Média"].apply(
                        lambda x: "#01B8AA" if x > 1 else "#FD625E" if x < -1 else "#F2C80F"
                    )

                    fig_diff.add_trace(go.Bar(
                        y=resumo["Cultivar Check"],
                        x=resumo["Diferença Média"],
                        orientation='h',
                        text=resumo["Diferença Média"].round(1),
                        textposition="outside",
                        textfont=dict(
                            size=16, family="Arial Black", color="black"),
                        marker_color=cores_personalizadas
                    ))

                    fig_diff.update_layout(
                        title=dict(text="Diferença Média de Produtividade",
                                   font=dict(size=20, color="black")),
                        xaxis=dict(
                            title=dict(text="Diferença Média (sc/ha)",
                                       font=dict(size=20, color="black")),
                            tickfont=dict(size=18, color="black")
                        ),
                        yaxis=dict(
                            title=dict(text="Check", font=dict(
                                size=20, color="black")),
                            tickfont=dict(size=18, color="black")
                        ),
                        margin=dict(t=30, b=40, l=60, r=30),
                        height=400,
                        showlegend=False
                    )

                    st.plotly_chart(fig_diff, use_container_width=True)

                    st.markdown("""
                        <div style='background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 10px 18px; margin-bottom: 8px; border-radius: 6px; font-size: 1.1em; color: #22223b; font-weight: 600;'>
                            Comparativo H2H - Comparativo MultiCheck
                        </div>
                    """, unsafe_allow_html=True)

                    # Cria uma cópia do resumo para exibir no AgGrid
                    resumo_aggrid = resumo.copy()
                    # st.write("Resumo preview:", resumo_aggrid.head())

                    # Crie o GridOptionsBuilder DEPOIS da renomeação/reordenação
                    gb = GridOptionsBuilder.from_dataframe(resumo_aggrid)
                    gb.configure_default_column(cellStyle={'fontSize': '14px'})
                    gb.configure_grid_options(headerHeight=30)
                    custom_css = {
                        ".ag-header-cell-label": {"font-weight": "bold", "font-size": "15px", "color": "black"}}

                    AgGrid(resumo_aggrid, gridOptions=gb.build(), height=400,
                           custom_css=custom_css, key="aggrid_resumo")

                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:  # type: ignore
                        resumo.to_excel(
                            writer, sheet_name="comparacao_multi_check", index=False)
                    buffer.seek(0)
                    st.download_button(
                        label="📅 Baixar Comparacao (Excel)",
                        data=buffer.getvalue(),
                        file_name=f"comparacao_{head_unico}_vs_checks.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                else:
                    st.info(
                        "❓ Nenhuma comparação disponível com os Checks selecionados.")
