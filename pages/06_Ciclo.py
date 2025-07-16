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
                Ciclo e Precocidade dos Híbridos de Milho
            </h1>
            <h3 style="margin-top: 0; color: #e0e0e0; font-weight: 400; font-size: 1.2em;">
                Informações detalhadas sobre o florescimento feminino e masculino, duração do ciclo e classificação da precocidade.
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

df_analise_ciclo = df_filtrado.copy()

# Desfragmenta o DataFrame para evitar PerformanceWarning
df_analise_ciclo = df_analise_ciclo.copy()

# Mapeamento de colunas para visualização customizada
colunas_renomeadas = [
    ("indexTratamento", "index"),
    ("nome", "Híbrido"),
    ("humidade", "Umd (%)"),
    ("prod_kg_ha_corr", "Prod@13.5% (kg/ha)"),
    ("prod_sc_ha_corr", "Prod@13.5% (sc/ha)"),
    ("numPlantas_ha", "Pop (plantas/ha)"),
    ("plantio", "Plantio"),
    ("colheita", "Colheita"),
    ("ciclo_dias", "Ciclo (dias)"),
    ("dataFlorFem", "Flor Fem"),
    ("flor_fem_dias", "Flor Fem (dias)"),
    ("dataFlorMasc", "Flor Masc"),
    ("flor_masc_dias", "Flor Masc (dias)"),
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
colunas_existentes = [c for c in colunas if c in df_analise_ciclo.columns]
df_analise_ciclo_visualizacao = df_analise_ciclo[colunas_existentes].rename(
    columns=novos_nomes)

# Exibe o DataFrame filtrado original
titulo_expander = "Dados Originais - Análise Ciclos"
with st.expander(titulo_expander, expanded=False):
    st.dataframe(df_filtrado, use_container_width=True)

    # Botão para exportar em Excel o DataFrame filtrado original
    buffer_filtro = io.BytesIO()
    df_filtrado.to_excel(buffer_filtro, index=False)  # type: ignore
    buffer_filtro.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel (dados originais - análise ciclo)",
        data=buffer_filtro,
        file_name="dados_originais_analise_ciclo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =========================
# Configuração visual e funcional do AgGrid
# =========================

# Cria o construtor de opções do grid a partir do DataFrame customizado
# Permite configurar colunas, filtros, menus e estilos
gb = GridOptionsBuilder.from_dataframe(df_analise_ciclo_visualizacao)

# Configuração de casas decimais para colunas numéricas
colunas_formatar = {
    "Prod@13.5% (kg/ha)": 1,
    "Prod@13.5% (sc/ha)": 1,
    "Pop (plantas/ha)": 0,
    "Ciclo (dias)": 0,
    "Flor Fem (dias)": 0,
    "Flor Masc (dias)": 0,
}

for col in df_analise_ciclo_visualizacao.columns:
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
st.subheader("Ciclo de Híbridos de Milho")
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
    df_analise_ciclo_visualizacao,   # DataFrame a ser exibido
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
df_analise_ciclo_visualizacao.to_excel(buffer, index=False)  # type: ignore
buffer.seek(0)
st.download_button(
    label="⬇️ Baixar Excel (Ciclo)",
    data=buffer,
    file_name="ciclo.xlsx",
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


df_analise_ciclo['indexTratamentoAgrupado'] = df_analise_ciclo['indexTratamento'].apply(
    agrupa_index)

# Define as colunas de agrupamento e as colunas numéricas para média
group_cols = ['fazendaRef', 'indexTratamentoAgrupado']
colunas_numericas = df_analise_ciclo.select_dtypes(
    include='number').columns.tolist()
colunas_numericas = [c for c in colunas_numericas if c not in [
    'indexTratamento', 'indexTratamentoAgrupado']]

# Substitui zeros por NaN nas colunas numéricas antes do agrupamento
df_analise_ciclo[colunas_numericas] = df_analise_ciclo[colunas_numericas].replace(
    0, np.nan)

# Realiza o agrupamento e calcula a média das colunas numéricas
df_analise_ciclo_agrupado = (
    df_analise_ciclo
    .groupby(group_cols, as_index=False)[colunas_numericas]
    .mean()
)

# Recupera o nome do híbrido para cada (fazendaRef, indexTratamentoAgrupado)
df_nome = (
    df_analise_ciclo
    .groupby(['fazendaRef', 'indexTratamentoAgrupado'])['nome']
    .first()
    .reset_index()
)

# Junta o nome ao DataFrame agrupado
df_analise_ciclo_agrupado = pd.merge(
    df_analise_ciclo_agrupado,
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
    ("plantio", "Plantio"),
    ("colheita", "Colheita"),
    ("ciclo_dias", "Ciclo (dias)"),
    ("dataFlorFem", "Flor Fem"),
    ("flor_fem_dias", "Flor Fem (dias)"),
    ("dataFlorMasc", "Flor Masc"),
    ("flor_masc_dias", "Flor Masc (dias)")
]
colunas_agrupado = [c[0] for c in colunas_agrupado_renomeadas]
novos_nomes_agrupado = {c[0]: c[1] for c in colunas_agrupado_renomeadas}
colunas_agrupado_existentes = [
    c for c in colunas_agrupado if c in df_analise_ciclo_agrupado.columns]
df_analise_ciclo_agrupado_visualizacao = df_analise_ciclo_agrupado[colunas_agrupado_existentes].rename(
    columns=novos_nomes_agrupado)  # type: ignore

# =========================
# Exibição do DataFrame agrupado customizado com AgGrid
# =========================

st.subheader("Dados Conjuntos por Híbrido - Ciclo")
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
    df_analise_ciclo_agrupado_visualizacao)

# Configuração de casas decimais para colunas numéricas do agrupado
colunas_formatar_agrupado = {
    "Prod@13.5% (kg/ha)": 1,
    "Prod@13.5% (sc/ha)": 1,
    "Pop (plantas/ha)": 0,
    "Ciclo (dias)": 0,
    "Flor Fem (dias)": 0,
    "Flor Masc (dias)": 0,
}

for col in df_analise_ciclo_agrupado_visualizacao.columns:
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
    df_analise_ciclo_agrupado_visualizacao,
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
df_analise_ciclo_agrupado_visualizacao.to_excel(
    buffer_agrupado_vis, index=False)  # type: ignore
buffer_agrupado_vis.seek(0)
st.download_button(
    label="⬇️ Baixar Excel (Resumo da Ciclo)",
    data=buffer_agrupado_vis,
    file_name="resumo_ciclo.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# =========================
# Scatter plot: Umidade vs Produtividade Corrigida
# =========================

if 'Umd (%)' in df_analise_ciclo_agrupado_visualizacao.columns and 'Prod@13.5% (sc/ha)' in df_analise_ciclo_agrupado_visualizacao.columns:
    st.markdown(
        """
        <div style="background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 12px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;">
            Relação entre Umidade e Produtividade Corrigida
        </div>
        """,
        unsafe_allow_html=True
    )
    # Adiciona rótulos nos pontos (nome do híbrido)
    fig_scatter = px.scatter(
        df_analise_ciclo_agrupado_visualizacao,
        x='Umd (%)',
        y='Prod@13.5% (sc/ha)',
        color='Híbrido' if 'Híbrido' in df_analise_ciclo_agrupado_visualizacao.columns else None,
        text='Híbrido' if 'Híbrido' in df_analise_ciclo_agrupado_visualizacao.columns else None,
        labels={
            'Umd (%)': 'Umidade (%)',
            'Prod@13.5% (sc/ha)': 'Produtividade Corrigida (sc/ha)',
            'Híbrido': 'Híbrido'
        },
        title='Dispersão: Umidade vs Produtividade Corrigida'
    )
    fig_scatter.update_traces(
        marker=dict(size=7, line=dict(width=1, color='DarkSlateGrey')),
        textposition="top center"
    )
    fig_scatter.update_layout(
        font=dict(size=16, color='black'),
        xaxis=dict(title_font=dict(size=18, color='black'),
                   tickfont=dict(size=15, color='black')),
        yaxis=dict(title_font=dict(size=18, color='black'),
                   tickfont=dict(size=15, color='black')),
        title_font=dict(size=20, color='black'),
        legend_title_font=dict(size=16, color='black'),
        margin=dict(t=60, b=40, l=40, r=40),
        plot_bgcolor='#f5f7fa'
    )

    # Cálculo das médias descartando zeros e nulos
    media_x = df_analise_ciclo_agrupado_visualizacao['Umd (%)'][df_analise_ciclo_agrupado_visualizacao['Umd (%)'] > 0].mean(
    )
    media_y = df_analise_ciclo_agrupado_visualizacao[
        'Prod@13.5% (sc/ha)'][df_analise_ciclo_agrupado_visualizacao['Prod@13.5% (sc/ha)'] > 0].mean()

    # Adiciona linhas médias
    fig_scatter.add_shape(
        type="line",
        x0=media_x, x1=media_x,
        y0=df_analise_ciclo_agrupado_visualizacao['Prod@13.5% (sc/ha)'].min(),
        y1=df_analise_ciclo_agrupado_visualizacao['Prod@13.5% (sc/ha)'].max(),
        line=dict(color="#0070C0", width=2, dash="dash"),
        name="Média Umidade"
    )
    fig_scatter.add_shape(
        type="line",
        x0=df_analise_ciclo_agrupado_visualizacao['Umd (%)'].min(),
        x1=df_analise_ciclo_agrupado_visualizacao['Umd (%)'].max(),
        y0=media_y, y1=media_y,
        line=dict(color="#C00000", width=2, dash="dash"),
        name="Média Produtividade"
    )
    # Anotações com deslocamento e valor
    fig_scatter.add_annotation(x=media_x, y=df_analise_ciclo_agrupado_visualizacao['Prod@13.5% (sc/ha)'].max(),
                               text=f"Média Umidade ({media_x:.1f})", showarrow=False, yshift=30, font=dict(color="#0070C0", size=14))
    fig_scatter.add_annotation(x=df_analise_ciclo_agrupado_visualizacao['Umd (%)'].max(), y=media_y,
                               text=f"Média Produtividade ({media_y:.1f})", showarrow=False, yshift=-30, font=dict(color="#C00000", size=14))

    st.plotly_chart(fig_scatter, use_container_width=True)

# =========================
# Precocidade: Scatter plot agrupado por Híbrido
# =========================

if 'Híbrido' in df_analise_ciclo_agrupado_visualizacao.columns:
    # Cria o DataFrame agrupado por híbrido
    df_precocidade = df_analise_ciclo_agrupado_visualizacao.groupby(
        'Híbrido', as_index=False).mean(numeric_only=True)

    if 'Umd (%)' in df_precocidade.columns and 'Prod@13.5% (sc/ha)' in df_precocidade.columns:
        st.markdown(
            """
            <div style="background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 12px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;">
                Precocidade: Relação entre Umidade e Produtividade Corrigida (por Híbrido)
            </div>
            """,
            unsafe_allow_html=True
        )
        fig_scatter = px.scatter(
            df_precocidade,
            x='Umd (%)',
            y='Prod@13.5% (sc/ha)',
            color='Híbrido',
            text='Híbrido',
            labels={
                'Umd (%)': 'Umidade (%)',
                'Prod@13.5% (sc/ha)': 'Produtividade Corrigida (sc/ha)',
                'Híbrido': 'Híbrido'
            },
            title='Dispersão: Umidade vs Produtividade Corrigida (por Híbrido)'
        )
        fig_scatter.update_traces(
            marker=dict(size=7, line=dict(width=1, color='DarkSlateGrey')),
            textposition="top center"
        )
        # Cálculo das médias descartando zeros e nulos
        media_x = df_precocidade['Umd (%)'][df_precocidade['Umd (%)'] > 0].mean(
        )
        media_y = df_precocidade['Prod@13.5% (sc/ha)'][df_precocidade['Prod@13.5% (sc/ha)'] > 0].mean()
        # Adiciona linhas médias
        fig_scatter.add_shape(
            type="line",
            x0=media_x, x1=media_x,
            y0=df_precocidade['Prod@13.5% (sc/ha)'].min(),
            y1=df_precocidade['Prod@13.5% (sc/ha)'].max(),
            line=dict(color="#0070C0", width=2, dash="dash"),
            name="Média Umidade"
        )
        fig_scatter.add_shape(
            type="line",
            x0=df_precocidade['Umd (%)'].min(),
            x1=df_precocidade['Umd (%)'].max(),
            y0=media_y, y1=media_y,
            line=dict(color="#C00000", width=2, dash="dash"),
            name="Média Produtividade"
        )
        # Anotações
        fig_scatter.add_annotation(x=media_x, y=df_precocidade['Prod@13.5% (sc/ha)'].max(),
                                   text=f"Média Umidade ({media_x:.1f})", showarrow=False, yshift=30, font=dict(color="#0070C0", size=14))
        fig_scatter.add_annotation(x=df_precocidade['Umd (%)'].max(), y=media_y,
                                   text=f"Média Produtividade ({media_y:.1f})", showarrow=False, yshift=-30, font=dict(color="#C00000", size=14))
        fig_scatter.update_layout(
            font=dict(size=16, color='black'),
            xaxis=dict(title_font=dict(size=18, color='black'),
                       tickfont=dict(size=15, color='black'), dtick=1),
            yaxis=dict(title_font=dict(size=18, color='black'),
                       tickfont=dict(size=15, color='black'), dtick=10),
            title_font=dict(size=20, color='black'),
            legend_title_font=dict(size=16, color='black'),
            margin=dict(t=60, b=40, l=40, r=40),
            plot_bgcolor='#f5f7fa'
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

# =========================
# Precocidade: Scatter plot agrupado por Híbrido (média direta das parcelas)
# =========================
if 'Híbrido' in df_analise_ciclo_visualizacao.columns:
    df_precocidade_parcela = df_analise_ciclo_visualizacao.groupby(
        'Híbrido', as_index=False).mean(numeric_only=True)

    if 'Umd (%)' in df_precocidade_parcela.columns and 'Prod@13.5% (sc/ha)' in df_precocidade_parcela.columns:
        st.markdown(
            """
            <div style="background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 12px; border-radius: 6px; font-size: 1.15em; color: #22223b; font-weight: 600;">
                Precocidade: Média Direta das Parcelas por Híbrido
            </div>
            """,
            unsafe_allow_html=True
        )
        fig_scatter_parcela = px.scatter(
            df_precocidade_parcela,
            x='Umd (%)',
            y='Prod@13.5% (sc/ha)',
            color='Híbrido',
            text='Híbrido',
            labels={
                'Umd (%)': 'Umidade (%)',
                'Prod@13.5% (sc/ha)': 'Produtividade Corrigida (sc/ha)',
                'Híbrido': 'Híbrido'
            },
            title='Dispersão: Umidade vs Produtividade Corrigida (Média Direta das Parcelas)'
        )
        fig_scatter_parcela.update_traces(
            marker=dict(size=7, line=dict(width=1, color='DarkSlateGrey')),
            textposition="top center"
        )
        # Cálculo das médias descartando zeros e nulos
        media_x = df_precocidade_parcela['Umd (%)'][df_precocidade_parcela['Umd (%)'] > 0].mean(
        )
        media_y = df_precocidade_parcela['Prod@13.5% (sc/ha)'][df_precocidade_parcela['Prod@13.5% (sc/ha)'] > 0].mean()
        # Adiciona linhas médias
        fig_scatter_parcela.add_shape(
            type="line",
            x0=media_x, x1=media_x,
            y0=df_precocidade_parcela['Prod@13.5% (sc/ha)'].min(),
            y1=df_precocidade_parcela['Prod@13.5% (sc/ha)'].max(),
            line=dict(color="#0070C0", width=2, dash="dash"),
            name="Média Umidade"
        )
        fig_scatter_parcela.add_shape(
            type="line",
            x0=df_precocidade_parcela['Umd (%)'].min(),
            x1=df_precocidade_parcela['Umd (%)'].max(),
            y0=media_y, y1=media_y,
            line=dict(color="#C00000", width=2, dash="dash"),
            name="Média Produtividade"
        )
        # Anotações com valor e deslocamento
        fig_scatter_parcela.add_annotation(x=media_x, y=df_precocidade_parcela['Prod@13.5% (sc/ha)'].max(),
                                           text=f"Média Umidade ({media_x:.1f})", showarrow=False, yshift=30, font=dict(color="#0070C0", size=14))
        fig_scatter_parcela.add_annotation(x=df_precocidade_parcela['Umd (%)'].max(), y=media_y,
                                           text=f"Média Produtividade ({media_y:.1f})", showarrow=False, yshift=-30, font=dict(color="#C00000", size=14))
        fig_scatter_parcela.update_layout(
            font=dict(size=16, color='black'),
            xaxis=dict(title_font=dict(size=18, color='black'),
                       tickfont=dict(size=15, color='black'), dtick=1),
            yaxis=dict(title_font=dict(size=18, color='black'),
                       tickfont=dict(size=15, color='black'), dtick=10),
            title_font=dict(size=20, color='black'),
            legend_title_font=dict(size=16, color='black'),
            margin=dict(t=60, b=40, l=40, r=40),
            plot_bgcolor='#f5f7fa'
        )
        st.plotly_chart(fig_scatter_parcela, use_container_width=True)
