from data_processing.codigo_tratamento import gerar_df_avTratamentoMilho
from supabase import create_client
import io
import pandas as pd
import streamlit as st
import os
import sys
import datetime
import time
sys.path.append(os.path.abspath(os.path.dirname(__file__)))


# Configuração do Supabase
SUPABASE_URL = 'https://lwklfogmduwitmbqbgyp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx3a2xmb2dtZHV3aXRtYnFiZ3lwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzg1MjIyNDQsImV4cCI6MjA1NDA5ODI0NH0.3RMzkQnRcnZj2XtK3YZm4z4VHpLlwe3N8ulOiqcbC-I'

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# Configuração da página
st.set_page_config(layout="wide")


# =========================
# Header customizado do dashboard
# =========================
st.markdown(
    '''
    <div style="background: linear-gradient(90deg, #0070C0 0%, #4a4e69 100%); border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.10); padding: 28px 24px 18px 24px; margin-bottom: 32px; display: flex; align-items: center;">
        <div style="flex:1">
            <h1 style="margin-bottom: 0.2em; color: #fff; font-size: 2.2em; font-weight: 700;">
                JAUM - Avaliações de Milho
            </h1>
            <h3 style="margin-top: 0; color: #e0e0e0; font-weight: 400; font-size: 1.2em;">
                Carregamento, integração e exportação de dados de avaliações de milho
            </h3>
        </div>
    </div>
    ''',
    unsafe_allow_html=True
)

# =========================
# Descrição e explicação do JAUM
# =========================
st.markdown(
    '''
    <div style="background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 12px 18px; margin-bottom: 18px; border-radius: 6px; font-size: 1.18em; color: #22223b;">
        <b>O que é o JAUM?</b><br>
        JAUM representa uma etapa essencial conduzida pelo <b>Time de Desenvolvimento Técnico de Culturas</b>, responsável por avaliar, monitorar e posicionar híbridos em diferentes regiões do Brasil antes e após o lançamento comercial, garantindo um portfólio robusto e alinhado às necessidades do mercado.<br><br>
        <b>Significado da sigla:</b><br>
        <b>J – Jornada</b>: Percurso que o híbrido faz desde os testes iniciais até sua recomendação para lançamento, considerando diferentes regiões, ambientes e manejos.<br>
        <b>A – Avaliação</b>: Análise detalhada do desempenho agronômico, sanidade, produtividade e estabilidade dos híbridos ao longo dos ciclos.<br>
        <b>U – Unificação</b>: Consolidação das informações geradas nos ensaios, permitindo uma visão integrada e comparativa entre diferentes materiais.<br>
        <b>M – Monitoramento</b>: Acompanhamento contínuo e <b>posicionamento técnico</b> baseado em dados reais de campo, apoiando decisões estratégicas e operacionais.
    </div>
    ''',
    unsafe_allow_html=True
)


@st.cache_data
def carregar_tabela_supabase(nome_tabela):
    """Carrega uma tabela do Supabase e retorna um DataFrame."""
    response = supabase.table(nome_tabela).select("*").execute()
    if response.data:
        return pd.DataFrame(response.data)
    else:
        return pd.DataFrame()


def carregar_excel(caminho):
    """Carrega um arquivo Excel e retorna um DataFrame."""
    try:
        return pd.read_excel(caminho)
    except Exception as e:
        st.warning(f"Não foi possível carregar o arquivo Excel: {e}")
        return pd.DataFrame()


# Dicionário: nome da tabela Supabase -> nome do DataFrame
nomes_tabelas = {
    "av1TratamentoMilho": "df_av1TratamentoMilho",
    "av1DetalheTratamentoMilho": "df_av1DetalheTratamentoMilho",
    "av2TratamentoMilho": "df_av2TratamentoMilho",
    "av2DetalheTratamentoMilho": "df_av2DetalheTratamentoMilho",
    "av3TratamentoMilho": "df_av3TratamentoMilho",
    "av3DetalheTratamentoMilho": "df_av3DetalheTratamentoMilho",
    "av4TratamentoMilho": "df_av4TratamentoMilho",
    "av4DetalheTratamentoMilho": "df_av4DetalheTratamentoMilho",
    "avaliacao": "df_avaliacao",
    "fazenda": "df_fazenda",
    "cidade": "df_cidade",
    "estado": "df_estado",
    "users": "df_users",

}

# Carregamento das tabelas do Supabase para o session_state
for nome_tabela, nome_df in nomes_tabelas.items():
    if nome_df not in st.session_state:
        st.session_state[nome_df] = carregar_tabela_supabase(nome_tabela)

# Carregamento do arquivo Excel para o session_state
CAMINHO_EXCEL = os.path.join(
    "datasets", "base_municipios_regioes_soja_milho.xlsx")
nome_df_excel = "df_base_municipios_regioes_soja_milho"
if nome_df_excel not in st.session_state:
    st.session_state[nome_df_excel] = carregar_excel(CAMINHO_EXCEL)
    if not st.session_state[nome_df_excel].empty:
        st.success("Arquivo Excel carregado com sucesso!")

# Gera o DataFrame tratado uma única vez e salva no session_state
if "df_avTratamentoMilho" not in st.session_state:
    df_avTratamentoMilho, df_av2TratamentoMilho_merged, df_av3TratamentoMilho_merged, df_av4TratamentoMilho_merged = gerar_df_avTratamentoMilho(
        st.session_state)
    st.session_state["df_avTratamentoMilho"] = df_avTratamentoMilho
    st.session_state["df_av2TratamentoMilho_merged"] = df_av2TratamentoMilho_merged
    st.session_state["df_av3TratamentoMilho_merged"] = df_av3TratamentoMilho_merged
    st.session_state["df_av4TratamentoMilho_merged"] = df_av4TratamentoMilho_merged

# Exemplo de uso do DataFrame tratado na página principal
# st.title("Bem-vindo ao Analisador de Dados de Milho")
# st.write("DataFrame tratado disponível para todas as páginas:")
# st.dataframe(st.session_state["df_avTratamentoMilho"].head(20), use_container_width=True)

# =========================
# FIM DO BLOCO DE CARREGAMENTO DE DADOS
# =========================

# Divider na parte de baixo da página
st.divider()

# Layout dos botões
col1, col2, col3 = st.columns([2.5, 2.5, 6])  # proporcional: 25%, 25%, 60%

# Função para recarregar tabelas do Supabase (com ou sem cache)


@st.cache_data
def fetch_table(nome_tabela):
    return carregar_tabela_supabase(nome_tabela)


TABELAS = list(nomes_tabelas.keys())

# Sidebar com botões de carregamento e crédito do desenvolvedor

with st.sidebar:
    st.markdown("### 🔄 Carregamento de Dados")
    st.markdown("Escolha como deseja carregar os dados:")
    if st.button("🔄 Carregar Dados com cache (mais rápido)"):
        dataframes = {tabela: fetch_table(tabela) for tabela in TABELAS}
        # Carrega o Excel também
        dataframes[nome_df_excel] = carregar_excel(CAMINHO_EXCEL)
        st.session_state["dataframes"] = dataframes
        st.success("✅ Dados carregados e armazenados!")
    if st.button("♻️ Carregar Dados sem cache (mais lento)"):
        start_time = time.time()

        # Limpeza do cache
        cache_start = time.time()
        fetch_table.clear()  # limpa o cache da função
        carregar_tabela_supabase.clear()  # limpa o cache da função base também
        cache_time = time.time() - cache_start

        # Carregamento dos dados
        load_start = time.time()
        dataframes = {tabela: fetch_table(tabela) for tabela in TABELAS}
        # Carrega o Excel também
        dataframes[nome_df_excel] = carregar_excel(CAMINHO_EXCEL)
        load_time = time.time() - load_start

        # Atualização do session_state
        session_start = time.time()
        st.session_state["dataframes"] = dataframes
        # Atualiza também os DataFrames individuais no session_state
        for nome, df in dataframes.items():
            st.session_state[nome] = df
        session_time = time.time() - session_start

        # Regeneração do DataFrame tratado
        process_start = time.time()
        df_avTratamentoMilho, df_av2TratamentoMilho_merged, df_av3TratamentoMilho_merged, df_av4TratamentoMilho_merged = gerar_df_avTratamentoMilho(
            st.session_state)
        st.session_state["df_avTratamentoMilho"] = df_avTratamentoMilho
        st.session_state["df_av2TratamentoMilho_merged"] = df_av2TratamentoMilho_merged
        st.session_state["df_av3TratamentoMilho_merged"] = df_av3TratamentoMilho_merged
        st.session_state["df_av4TratamentoMilho_merged"] = df_av4TratamentoMilho_merged
        process_time = time.time() - process_start

        total_time = time.time() - start_time

        st.session_state["last_update"] = datetime.datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S")
        st.success(
            f"✅ Dados carregados direto do Supabase! (Atualizado em: {st.session_state['last_update']})")

        # Mostrar tempos de cada etapa
        st.info(f"""
        ⏱️ **Tempos de execução:**
        - Limpeza do cache: {cache_time:.2f}s
        - Carregamento dos dados: {load_time:.2f}s
        - Atualização do session_state: {session_time:.2f}s
        - Processamento do DataFrame: {process_time:.2f}s
        - **Tempo total: {total_time:.2f}s**
        """)

        # Recarrega a página para garantir que tudo seja atualizado
        st.rerun()
    if "last_update" in st.session_state:
        st.markdown(
            f"<span style='font-size:12px;color:#888;'>Última atualização sem cache: <b>{st.session_state['last_update']}</b></span>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(
        "<p style='font-size: 14px;'>Desenvolvido por <a href='https://www.linkedin.com/in/eng-agro-andre-ferreira/' target='_blank'>Andre Ferreira</a></p>",
        unsafe_allow_html=True
    )


# =========================
# VISUALIZAÇÃO E EXPORTAÇÃO DE DATAFRAMES
# =========================

with st.expander("📤 Exportar DataFrame para Excel", expanded=False):
    # Lista de DataFrames disponíveis no session_state['dataframes'] + DataFrame tratado e intermediários
    if "dataframes" in st.session_state:
        dfs_disponiveis = list(st.session_state["dataframes"].keys())
    else:
        dfs_disponiveis = []
    # Adiciona o DataFrame tratado e intermediários à lista, se existirem
    nomes_extra = [
        "df_avTratamentoMilho",
        "df_av2TratamentoMilho_merged",
        "df_av3TratamentoMilho_merged",
        "df_av4TratamentoMilho_merged"
    ]
    for nome in nomes_extra:
        if nome not in dfs_disponiveis and nome in st.session_state:
            dfs_disponiveis.append(nome)

    df_selecionado_nome = st.selectbox(
        "Selecione o DataFrame para exportar:", dfs_disponiveis)

    if df_selecionado_nome:
        if df_selecionado_nome in st.session_state:
            df_selecionado = st.session_state[df_selecionado_nome]
        else:
            df_selecionado = st.session_state["dataframes"][df_selecionado_nome]
        st.dataframe(df_selecionado, use_container_width=True)
        # Botão para exportar
        buffer = io.BytesIO()
        df_selecionado.to_excel(buffer, index=False)
        buffer.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel",
            data=buffer,
            file_name=f"{df_selecionado_nome}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
