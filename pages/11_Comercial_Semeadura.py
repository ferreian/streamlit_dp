import itertools
import time
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.express as px
import streamlit as st
import pandas as pd
import io
import numpy as np
import plotly.graph_objects as go
from supabase import create_client
import requests
import unicodedata
import datetime
import os
import tempfile
from plotly.colors import qualitative as plotly_qual
from scipy.stats import zscore
from st_aggrid.shared import JsCode


# =====================
# 1. IMPORTS E CONFIGS
# =====================

# Supabase config
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
if not SUPABASE_URL or not SUPABASE_KEY:
    supabase = None
else:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Painel GD", layout="wide")

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
                Análise Comercial - Semeadura de Milho
            </h1>
            <h3 style="margin-top: 0; color: #e0e0e0; font-weight: 400; font-size: 1.2em;">
                Visualize e explore os dados de semeadura e produtividade de milho.
            </h3>
        </div>
        <!-- Se quiser adicionar um logo, descomente a linha abaixo e coloque o caminho correto -->
        <!-- <img src=\"https://link-para-logo.png\" style=\"height:64px; margin-left:24px;\" /> -->
    </div>
    """,
    unsafe_allow_html=True
)

# =====================
# 2. CARREGAMENTO DE DADOS (RESULTADOS, FAZENDA, USUARIO)
# =====================


def carregar_tabela_supabase(nome_tabela):
    response = supabase.table(nome_tabela).select("*").execute()
    if response.data:
        return pd.DataFrame(response.data)
    else:
        return pd.DataFrame()


@st.cache_data
def fetch_table(nome_tabela):
    return carregar_tabela_supabase(nome_tabela)


TABELAS_COMERCIAL = ["resultados", "fazenda", "usuarios"]

with st.sidebar:
    st.markdown("### 🔄 Carregamento de Dados Comerciais")
    st.markdown("Escolha como deseja carregar os dados:")
    if st.button("🔄 Carregar Dados Comerciais com cache (mais rápido)"):
        dataframes = {tabela: fetch_table(tabela)
                      for tabela in TABELAS_COMERCIAL}
        for nome, df in dataframes.items():
            st.session_state[nome] = df
        st.success("✅ Dados comerciais carregados e armazenados!")
    if st.button("♻️ Carregar Dados Comerciais sem cache (mais lento)"):
        start_time = time.time()
        fetch_table.clear()  # limpa o cache da função
        dataframes = {tabela: fetch_table(tabela)
                      for tabela in TABELAS_COMERCIAL}
        for nome, df in dataframes.items():
            st.session_state[nome] = df
        total_time = time.time() - start_time
        st.success(
            f"✅ Dados comerciais carregados direto do Supabase! (Tempo: {total_time:.2f}s)")


# =========================
# SEÇÃO DE TRATAMENTO DO DATAFRAME RESULTADOS
# =========================
# --- INÍCIO TRATAMENTO DF RESULTADOS ---
if "resultados" in st.session_state and not st.session_state["resultados"].empty:
    df_resultados_tratado = st.session_state["resultados"].copy()
    colunas_remover = [
        "criado_em",
        "cultura",
        "pop_inicial",
        "tratamento_id",
        "area_total",
        "observacoes",
        "fazenda_id",
        "modificado_por",
        "modificado_em",
        "pmg",
        "avariados"
    ]
    df_resultados_tratado = df_resultados_tratado.drop(
        columns=[col for col in colunas_remover if col in df_resultados_tratado.columns], errors="ignore")
    # Converter datas para formato brasileiro
    for col_data in ["data_plantio", "data_colheita"]:
        if col_data in df_resultados_tratado.columns:
            df_resultados_tratado[col_data] = pd.to_datetime(
                df_resultados_tratado[col_data], errors='coerce').dt.strftime('%d/%m/%Y')
    # Remover pontos da coluna pop_final
    if "pop_final" in df_resultados_tratado.columns:
        df_resultados_tratado["pop_final"] = df_resultados_tratado["pop_final"].astype(
            str).str.replace('.', '', regex=False)
    # Trocar vírgula por ponto em umid_colheita e resultado
    for col_float in ["umid_colheita", "resultado"]:
        if col_float in df_resultados_tratado.columns:
            df_resultados_tratado[col_float] = df_resultados_tratado[col_float].astype(
                str).str.replace(',', '.', regex=False)
    # Converter fazenda e produtor para caixa alta
    for col_upper in ["fazenda", "produtor"]:
        if col_upper in df_resultados_tratado.columns:
            df_resultados_tratado[col_upper] = df_resultados_tratado[col_upper].astype(
                str).str.upper()
    # Criar coluna prod_sc_ha_corr corrigindo a umidade para 13.5%
    if "umid_colheita" in df_resultados_tratado.columns and "resultado" in df_resultados_tratado.columns:
        # Converter para float (caso ainda estejam como string)
        df_resultados_tratado["umid_colheita"] = pd.to_numeric(
            df_resultados_tratado["umid_colheita"], errors="coerce")
        df_resultados_tratado["resultado"] = pd.to_numeric(
            df_resultados_tratado["resultado"], errors="coerce")
        df_resultados_tratado["prod_sc_ha_corr"] = df_resultados_tratado["resultado"] * (
            (100 - df_resultados_tratado["umid_colheita"]) / (100 - 13.5)
        )
        df_resultados_tratado["prod_sc_ha_corr"] = df_resultados_tratado["prod_sc_ha_corr"].round(
            1)
    # Criar coluna key como concatenação de fazenda_produtor
    if "fazenda" in df_resultados_tratado.columns and "produtor" in df_resultados_tratado.columns:
        df_resultados_tratado["key"] = df_resultados_tratado["fazenda"].astype(
            str) + "_" + df_resultados_tratado["produtor"].astype(str)
    else:
        df_resultados_tratado = None
    # Criar coluna safra baseada na coluna epoca
    if "epoca" in df_resultados_tratado.columns:
        def definir_safra(epoca):
            if pd.isna(epoca) or str(epoca).strip() == "":
                return "2025"
            epoca_str = str(epoca).strip().lower()
            if epoca_str == "safrinha":
                return "2025"
            elif epoca_str == "safra":
                return "2024-2025"
            else:
                return "2025"
        df_resultados_tratado["safra"] = df_resultados_tratado["epoca"].apply(
            definir_safra)
    # Remover linhas onde prod_sc_ha_corr é 0 ou vazio
    if "prod_sc_ha_corr" in df_resultados_tratado.columns:
        df_resultados_tratado = df_resultados_tratado[
            df_resultados_tratado["prod_sc_ha_corr"].notna() & (
                df_resultados_tratado["prod_sc_ha_corr"] != 0) & (df_resultados_tratado["prod_sc_ha_corr"] != "")
        ]
else:
    df_resultados_tratado = None
# --- FIM TRATAMENTO DF RESULTADOS ---


# =========================
# SEÇÃO DE TRATAMENTO DO DATAFRAME FAZENDA
# =========================
# --- INÍCIO TRATAMENTO DF FAZENDA ---
if "fazenda" in st.session_state and not st.session_state["fazenda"].empty:
    df_fazenda_tratada = st.session_state["fazenda"].copy()
    colunas_remover_fazenda = [
        "criado_em",
        "modificado_por",
        "textura_solo",
        "fertilidade_solo",
        "isIrrigado",
        "tipo_GD",
        "latitude",
        "longitude",
        "altitude",
        "observacoes",
        "aut_imagem",
        "modificado_em",
        "criado_por",
        "codigo_estado",
        "cidade_id",
        "estado_id"
    ]
    df_fazenda_tratada = df_fazenda_tratada.drop(
        columns=[col for col in colunas_remover_fazenda if col in df_fazenda_tratada.columns], errors="ignore")
    # Deixar produtor e fazenda em caixa alta
    for col in ["produtor", "fazenda"]:
        if col in df_fazenda_tratada.columns:
            df_fazenda_tratada[col] = df_fazenda_tratada[col].astype(
                str).str.upper()
    # Criar coluna key como concatenação de fazenda_produtor
    if "fazenda" in df_fazenda_tratada.columns and "produtor" in df_fazenda_tratada.columns:
        df_fazenda_tratada["key"] = df_fazenda_tratada["fazenda"].astype(
            str) + "_" + df_fazenda_tratada["produtor"].astype(str)
    else:
        df_fazenda_tratada = None
else:
    df_fazenda_tratada = None
# --- FIM TRATAMENTO DF FAZENDA ---

# =========================
# MERGE RESULTADOS + FAZENDA PARA CRIAR gd_milho_2025
# =========================
# --- INÍCIO MERGE GD_MILHO_2025 ---
gd_milho_2025 = None
if df_resultados_tratado is not None and not df_resultados_tratado.empty and \
   df_fazenda_tratada is not None and not df_fazenda_tratada.empty:
    # Verificar se a coluna 'key' existe em ambos os DataFrames
    if "key" in df_resultados_tratado.columns and "key" in df_fazenda_tratada.columns:
        # Seleciona apenas as colunas chave e as desejadas de fazenda
        cols_fazenda = ["key"]
        for col in ["nome_cidade", "nome_estado"]:
            if col in df_fazenda_tratada.columns:
                cols_fazenda.append(col)
        gd_milho_2025 = df_resultados_tratado.merge(
            df_fazenda_tratada[cols_fazenda],
            on="key",
            how="left"
        )
    else:
        gd_milho_2025 = None
else:
    gd_milho_2025 = None
# --- FIM MERGE GD_MILHO_2025 ---

# =========================
# MERGE gd_milho_2025 + usuarios (trazendo nome do usuário)
# =========================
# --- INÍCIO MERGE GD_MILHO_2025 + USUARIOS ---
if gd_milho_2025 is not None and not gd_milho_2025.empty and \
   "usuarios" in st.session_state and not st.session_state["usuarios"].empty:
    usuarios_df = st.session_state["usuarios"]
    # Seleciona apenas as colunas necessárias
    usuarios_df = usuarios_df[[
        col for col in usuarios_df.columns if col in ("usuario_id", "nome")]].copy()
    usuarios_df = usuarios_df.rename(columns={"nome": "nome_usuario"})
    gd_milho_2025 = gd_milho_2025.merge(
        usuarios_df,
        left_on="criado_por",
        right_on="usuario_id",
        how="left"
    )
    gd_milho_2025 = gd_milho_2025.drop(columns=["usuario_id"], errors="ignore")
# --- FIM MERGE GD_MILHO_2025 + USUARIOS ---

# Adicionar coluna siglaEstado baseada em nome_estado
if gd_milho_2025 is not None and "nome_estado" in gd_milho_2025.columns:
    estados_siglas = {
        "Acre": "AC", "Alagoas": "AL", "Amapá": "AP", "Amazonas": "AM", "Bahia": "BA",
        "Ceará": "CE", "Distrito Federal": "DF", "Espírito Santo": "ES", "Goiás": "GO",
        "Maranhão": "MA", "Mato Grosso": "MT", "Mato Grosso do Sul": "MS", "Minas Gerais": "MG",
        "Pará": "PA", "Paraíba": "PB", "Paraná": "PR", "Pernambuco": "PE", "Piauí": "PI",
        "Rio de Janeiro": "RJ", "Rio Grande do Norte": "RN", "Rio Grande do Sul": "RS",
        "Rondônia": "RO", "Roraima": "RR", "Santa Catarina": "SC", "São Paulo": "SP",
        "Sergipe": "SE", "Tocantins": "TO"
    }
    gd_milho_2025["siglaEstado"] = gd_milho_2025["nome_estado"].map(
        estados_siglas)

# Deixar nome_usuario em caixa alta
if gd_milho_2025 is not None and "nome_usuario" in gd_milho_2025.columns:
    gd_milho_2025["nome_usuario"] = gd_milho_2025["nome_usuario"].astype(
        str).str.upper()

# Criar coluna cidade_siglaEstado ANTES da renomeação/reordenação
if gd_milho_2025 is not None and not gd_milho_2025.empty:
    # Usar nome_cidade se existir, senão cidade (caso já tenha sido renomeada)
    col_cidade = None
    if "nome_cidade" in gd_milho_2025.columns:
        col_cidade = "nome_cidade"
    elif "cidade" in gd_milho_2025.columns:
        col_cidade = "cidade"
    if col_cidade and "siglaEstado" in gd_milho_2025.columns:
        gd_milho_2025["cidade_siglaEstado"] = gd_milho_2025[col_cidade].astype(
            str) + "_" + gd_milho_2025["siglaEstado"].astype(str)

# Dicionário de renomeação e seleção de colunas permanece igual
if gd_milho_2025 is not None and not gd_milho_2025.empty:
    renomear = {
        "produtor": "cliente",
        "nome_cidade": "cidade",
        "tratamento": "hibrido",
        "umid_colheita": "umidade",
        "nome_usuario": "responsavel"
    }
    colunas_ordem = [
        "cliente",
        "siglaEstado",
        "cidade",
        "cidade_siglaEstado",
        "hibrido",
        "pop_final",
        "data_plantio",
        "data_colheita",
        "prod_sc_ha_corr",
        "umidade",
        "safra",
        "responsavel"
    ]
    gd_milho_2025 = gd_milho_2025.rename(columns=renomear)
    colunas_existentes = [
        col for col in colunas_ordem if col in gd_milho_2025.columns]
    gd_milho_2025 = gd_milho_2025[colunas_existentes]

# Remover linhas onde cidade ou hibrido estão vazios ou nulos
if gd_milho_2025 is not None and not gd_milho_2025.empty:
    gd_milho_2025 = gd_milho_2025[
        gd_milho_2025['cidade'].notna() & (gd_milho_2025['cidade'] != '') &
        gd_milho_2025['hibrido'].notna() & (gd_milho_2025['hibrido'] != '')
    ]

# =========================
# VISUALIZAÇÃO E EXPORTAÇÃO DO DATAFRAME gd_milho_2025
# =========================
if gd_milho_2025 is not None and not gd_milho_2025.empty:
    st.markdown("### Resultados 2025")
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
        GD Milho 2025 - Completo    
    </div>
    """,
        unsafe_allow_html=True
    )
    st.dataframe(gd_milho_2025, use_container_width=True)
    buffer_gd = io.BytesIO()
    gd_milho_2025.to_excel(buffer_gd, index=False)
    buffer_gd.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel (gd_milho_2025)",
        data=buffer_gd,
        file_name="gd_milho_2025.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Tabela gd_milho_2025 não gerada ou está vazia.")

# =========================
# REMOÇÃO DE OUTLIERS (Z-SCORE) EM prod_sc_ha_corr E umidade
# =========================
# --- INÍCIO REMOÇÃO OUTLIERS Z-SCORE ---


def remover_outliers_zscore(df, colunas, threshold=3.0):
    df_limpo = df.copy()
    outlier_mask = pd.Series(False, index=df.index)
    log_remocao = pd.Series("", index=df.index)
    parametros = {}
    for coluna in colunas:
        serie = df[coluna].dropna()
        media = serie.mean()
        std = serie.std()
        z_scores = ((serie - media) / std).abs()
        mask = z_scores > threshold
        # Reindexar para alinhar com o DataFrame original
        mask_full = pd.Series(False, index=df.index)
        mask_full[serie.index] = mask
        outlier_mask = outlier_mask | mask_full
        for idx in serie.index[mask]:
            valor = df.at[idx, coluna]
            z = z_scores.at[idx]
            if valor < media:
                log_remocao.at[idx] += f"Outlier em {coluna} (abaixo do limiar: média - {threshold}*std = {media - threshold*std:.2f}, z-score={z:.2f}); "
            else:
                log_remocao.at[idx] += f"Outlier em {coluna} (acima do limiar: média + {threshold}*std = {media + threshold*std:.2f}, z-score={z:.2f}); "
        parametros[coluna] = {
            'media': media,
            'std': std,
            'limite_inferior': media - threshold*std,
            'limite_superior': media + threshold*std
        }
    df_removidos = df[outlier_mask].copy()
    if not df_removidos.empty:
        df_removidos['log_remocao'] = log_remocao[outlier_mask].str.strip('; ')
    df_limpo = df[~outlier_mask].copy()
    return df_limpo, df_removidos, parametros


# Ajuste do threshold do Z-Score na barra lateral
threshold_zscore = st.sidebar.number_input(
    'Threshold do Z-Score para remoção de outliers', min_value=1.0, max_value=5.0, value=3.0, step=0.1, format="%0.1f")

# Remoção de outliers por Z-Score para gd_milho_2025
if gd_milho_2025 is not None and not gd_milho_2025.empty:
    gd_milho_2025_tratado, gd_milho_2025_outliers, parametros_zscore = remover_outliers_zscore(
        gd_milho_2025, ['prod_sc_ha_corr', 'umidade'], threshold=threshold_zscore
    )
else:
    gd_milho_2025_tratado, gd_milho_2025_outliers, parametros_zscore = None, None, None


# Visualização dos outliers removidos
if gd_milho_2025_outliers is not None and not gd_milho_2025_outliers.empty:

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
        GD Milho 2025 - Outliers (Z-Score)    
    </div>
    """,
        unsafe_allow_html=True
    )
    st.dataframe(gd_milho_2025_outliers, use_container_width=True)
    buffer_outliers = io.BytesIO()
    gd_milho_2025_outliers.to_excel(buffer_outliers, index=False)
    buffer_outliers.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel (outliers_removidos)",
        data=buffer_outliers,
        file_name="outliers_removidos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_outliers_removidos"
    )
    # Exibir parâmetros do Z-Score usados
    st.markdown("**Parâmetros do Z-Score por coluna:**")
    for coluna, info in parametros_zscore.items():
        st.markdown(
            f"<div style='background: #f5f7fa; border-radius: 8px; padding: 10px; margin-bottom: 8px;'><b>{coluna}</b><br>Média: {info['media']:.2f} | Desvio padrão: {info['std']:.2f}<br>Limite inferior: {info['limite_inferior']:.2f} | Limite superior: {info['limite_superior']:.2f}</div>", unsafe_allow_html=True)
else:
    st.info("Nenhuma linha foi removida como outlier com o threshold atual.")


# Visualização do DataFrame tratado (sem outliers)
if gd_milho_2025_tratado is not None and not gd_milho_2025_tratado.empty:
    st.markdown("### Tabela: gd_milho_2025 (sem outliers)")
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
        GD Milho 2025 - Sem Outliers    
    </div>
    """,
        unsafe_allow_html=True
    )
    st.dataframe(gd_milho_2025_tratado, use_container_width=True)
    buffer_gd_tratado = io.BytesIO()
    gd_milho_2025_tratado.to_excel(buffer_gd_tratado, index=False)
    buffer_gd_tratado.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel (gd_milho_2025_tratado)",
        data=buffer_gd_tratado,
        file_name="gd_milho_2025_tratado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_gd_milho_2025_tratado"
    )
else:
    st.info("Tabela gd_milho_2025_tratado não gerada ou está vazia.")


# =========================
# FUNÇÃO CACHEADA PARA PREPARAR DF_COMERCIAL
# =========================


@st.cache_data
def preparar_df_comercial(gd_milho_2025_tratado):
    df_comercial = None
    if gd_milho_2025_tratado is not None and not gd_milho_2025_tratado.empty:
        df_comercial = gd_milho_2025_tratado.copy()
        # Merge com base_municipios
        caminho_base_municipios = os.path.join(
            "datasets", "base_municipios_regioes_soja_milho.xlsx")
        if os.path.exists(caminho_base_municipios):
            base_municipios = pd.read_excel(caminho_base_municipios)
            cols_base = ["cidade_siglaEstado", "mrhMilho", "macroRegiaoMilho",
                         "subConjuntaMilhoSafrinha", "conjuntaGeralMilhoSafrinha"]
            base_municipios = base_municipios[[
                col for col in cols_base if col in base_municipios.columns]]
            if df_comercial is not None and not df_comercial.empty:
                df_comercial = df_comercial.merge(
                    base_municipios,
                    on="cidade_siglaEstado",
                    how="left"
                )
    return df_comercial


# =========================
# FILTRO INTERATIVO NO SIDEBAR PARA df_comercial
# =========================
df_comercial = preparar_df_comercial(gd_milho_2025_tratado)
df_filtrado = None
if df_comercial is not None and not df_comercial.empty:
    df_filtrado = df_comercial.copy()
    # Criar coluna ano_plantio baseada na data_plantio
    df_filtrado['ano_plantio'] = pd.to_datetime(
        df_filtrado['data_plantio'], format='%d/%m/%Y', errors='coerce').dt.year
    # Converter para int, mantendo NaN como NaN
    df_filtrado['ano_plantio'] = pd.to_numeric(
        df_filtrado['ano_plantio'], errors='coerce').astype('Int64')

    filter_keys = [
        ("ano_plantio", "Ano de Plantio", "ano_plantio"),
        ("safra", "Safra", "safra"),
        ("macroRegiaoMilho", "Macro Região", "macro"),
        ("conjuntaGeralMilhoSafrinha", "Conjunta Geral", "conjunta"),
        ("subConjuntaMilhoSafrinha", "Sub Conjunta", "subconjunta"),
        ("mrhMilho", "MRH", "mrh"),
        ("siglaEstado", "Estado", "estado"),
        ("cidade", "Cidade", "cidade"),
        ("hibrido", "Híbrido", "hibrido"),
    ]
    # Inicializa seleções no session_state
    for col, _, key in filter_keys:
        if f"sel_{key}" not in st.session_state:
            st.session_state[f"sel_{key}"] = []
    with st.sidebar:
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
                df_filtrado = df_filtrado[df_filtrado[col].isin(
                    selecionadas)]


# =========================
# DADOS CONJUNTOS - MILHO
# =========================
# --- INÍCIO DADOS CONJUNTOS MILHO ---
st.subheader("Dados Conjuntos - Milho")
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
        Dados Conjuntos para Análise de Semeadura
    </div>
    """,
    unsafe_allow_html=True
)
df_filtrado_customizado = None
if df_filtrado is not None and not df_filtrado.empty:
    df_filtrado_customizado = df_filtrado.copy()
    gb = GridOptionsBuilder.from_dataframe(df_filtrado_customizado)
    gb.configure_default_column(
        groupable=True, value=True, enableRowGroup=True, editable=False, filter=True)
    gb.configure_side_bar()
    grid_options = gb.build()
    # CSS customizado para cabeçalho maior e preto, conteúdo preto
    custom_css = {
        ".ag-header-cell-label": {"justify-content": "center", "font-size": "1.15em", "color": "#222", "font-weight": "bold"},
        ".ag-header": {"color": "#222"},
        ".ag-cell": {"font-size": "1em", "color": "#222"}
    }
    AgGrid(
        df_filtrado_customizado,
        gridOptions=grid_options,
        enable_enterprise_modules=True,
        fit_columns_on_grid_load=False,
        theme="streamlit",
        height=500,
        reload_data=True,
        custom_css=custom_css
    )
    # Botão para exportar em Excel o DataFrame customizado
    buffer = io.BytesIO()
    df_filtrado_customizado.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel (Dados Conjuntos - Milho)",
        data=buffer,
        file_name="dados_conjuntos_milho.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Nenhum dado disponível para exibir em Dados Conjuntos - Milho.")
# --- FIM DADOS CONJUNTOS MILHO ---


# =========================
# MARCHA DE PLANTIO
# =========================
# --- INÍCIO MARCHA DE PLANTIO ---
st.subheader("Marcha de Plantio")
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
        Evolução do Percentual de Área Semeada de Milho
    </div>
    """,
    unsafe_allow_html=True
)

if df_filtrado is not None and not df_filtrado.empty:
    # Converter data_plantio para datetime para análise
    df_marcha_plantio = df_filtrado.copy()
    df_marcha_plantio['data_plantio_dt'] = pd.to_datetime(
        df_marcha_plantio['data_plantio'], format='%d/%m/%Y', errors='coerce')

    # Remover linhas com datas inválidas
    df_marcha_plantio = df_marcha_plantio.dropna(subset=['data_plantio_dt'])

    if not df_marcha_plantio.empty:
        # Filtrar apenas dados de 2025
        df_marcha_plantio = df_marcha_plantio[df_marcha_plantio['data_plantio_dt'].dt.year == 2025]

        if not df_marcha_plantio.empty:
            # Criar semanas a partir da primeira semana de janeiro de 2025
            data_inicio = pd.Timestamp('2025-01-01')
            data_fim = pd.Timestamp('2025-04-30')

            # Gerar todas as semanas
            semanas = pd.date_range(
                start=data_inicio, end=data_fim, freq='W-MON')

            # Calcular percentual cumulativo para cada semana
            percentuais_cumulativos = []
            datas_semana = []

            for semana in semanas:
                # Contar plantios até esta semana
                plantios_ate_semana = df_marcha_plantio[
                    df_marcha_plantio['data_plantio_dt'] <= semana
                ].shape[0]

                # Total de plantios
                total_plantios = df_marcha_plantio.shape[0]

                # Calcular percentual cumulativo
                if total_plantios > 0:
                    percentual = (plantios_ate_semana / total_plantios) * 100
                else:
                    percentual = 0

                percentuais_cumulativos.append(percentual)
                datas_semana.append(semana)

            # Criar DataFrame para o gráfico
            df_marcha = pd.DataFrame({
                'Data': datas_semana,
                'Percentual_Cumulativo': percentuais_cumulativos
            })

            # Formatar datas para exibição
            df_marcha['Data_Formatada'] = df_marcha['Data'].dt.strftime(
                '%d/%m')

            # Criar gráfico de linha
            fig_marcha = go.Figure()

            # Adicionar linha principal
            fig_marcha.add_trace(go.Scatter(
                x=df_marcha['Data_Formatada'],
                y=df_marcha['Percentual_Cumulativo'],
                mode='lines+markers',
                name='Safra 2025',
                line=dict(color='red', width=3),
                marker=dict(size=6, color='red'),
                hovertemplate='<b>%{x}</b><br>Percentual: %{y:.2f}%<extra></extra>'
            ))

            # Configurar layout
            fig_marcha.update_layout(
                title={
                    'text': 'EVOLUÇÃO DO PERCENTUAL DE ÁREA SEMEADA DE MILHO',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 20, 'color': 'black'}
                },
                xaxis_title='Data',
                yaxis_title='Percentual Cumulativo (%)',
                xaxis=dict(
                    title_font=dict(size=16, color='black'),
                    tickfont=dict(size=14, color='black'),
                    tickangle=-45
                ),
                yaxis=dict(
                    title_font=dict(size=16, color='black'),
                    tickfont=dict(size=14, color='black'),
                    range=[0, 100],
                    tickformat='.0f'
                ),
                height=600,
                showlegend=True,
                legend=dict(
                    font=dict(size=14, color='black'),
                    x=0.02,
                    y=0.98
                ),
                hovermode='x unified'
            )

            # Adicionar grid
            fig_marcha.update_xaxes(
                showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig_marcha.update_yaxes(
                showgrid=True, gridwidth=1, gridcolor='lightgray')

            st.plotly_chart(fig_marcha, use_container_width=True)

            # Exibir estatísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    label="Total de Plantios",
                    value=f"{df_marcha_plantio.shape[0]:,}"
                )
            with col2:
                data_primeiro_plantio = df_marcha_plantio['data_plantio_dt'].min(
                )
                st.metric(
                    label="Primeiro Plantio",
                    value=data_primeiro_plantio.strftime(
                        '%d/%m/%Y') if pd.notna(data_primeiro_plantio) else "N/A"
                )
            with col3:
                data_ultimo_plantio = df_marcha_plantio['data_plantio_dt'].max(
                )
                st.metric(
                    label="Último Plantio",
                    value=data_ultimo_plantio.strftime(
                        '%d/%m/%Y') if pd.notna(data_ultimo_plantio) else "N/A"
                )

            # Exportar dados da marcha de plantio
            st.markdown("### 💾 Exportar Dados da Marcha de Plantio")
            buffer_marcha = io.BytesIO()
            df_marcha.to_excel(buffer_marcha, index=False)
            buffer_marcha.seek(0)
            st.download_button(
                label="⬇️ Baixar Excel (Marcha de Plantio)",
                data=buffer_marcha,
                file_name="marcha_plantio.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("Não há dados de plantio em 2025 para gerar a marcha de plantio.")
    else:
        st.info("Não há dados válidos de data de plantio para análise.")
else:
    st.info("Nenhum dado disponível para análise da marcha de plantio.")

# =========================
# ANÁLISE DO PERÍODO DE SEMEADURA
# =========================
# --- INÍCIO ANÁLISE PERÍODO SEMEADURA ---
st.subheader("Análise do Período de Semeadura")
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
        Análise Temporal da Semeadura de Milho
    </div>
    """,
    unsafe_allow_html=True
)

if df_filtrado is not None and not df_filtrado.empty:
    # Converter data_plantio para datetime para análise
    df_analise_semeadura = df_filtrado.copy()
    df_analise_semeadura['data_plantio_dt'] = pd.to_datetime(
        df_analise_semeadura['data_plantio'], format='%d/%m/%Y', errors='coerce')

    # Remover linhas com datas inválidas
    df_analise_semeadura = df_analise_semeadura.dropna(
        subset=['data_plantio_dt'])

    if not df_analise_semeadura.empty:
        # Remover dados de 2024
        df_analise_semeadura = df_analise_semeadura[df_analise_semeadura['data_plantio_dt'].dt.year == 2025]

        # Função para calcular o período de semeadura
        def calcular_periodo_semeadura(data):
            mes = data.month
            dia = data.day

            if mes == 1:  # Janeiro
                return "JAN a 10 FEV"
            elif mes == 2:  # Fevereiro
                if dia <= 10:
                    return "JAN a 10 FEV"
                elif dia <= 25:
                    return "11 FEV a 25 FEV"
                else:
                    return "26 FEV+"
            else:  # Março em diante
                return "26 FEV+"

        # Calcular período de semeadura
        df_analise_semeadura['periodo_semeadura'] = df_analise_semeadura['data_plantio_dt'].apply(
            calcular_periodo_semeadura)
        df_analise_semeadura['mes'] = df_analise_semeadura['data_plantio_dt'].dt.month
        df_analise_semeadura['ano'] = df_analise_semeadura['data_plantio_dt'].dt.year

        # Criar coluna periodo_mes_ano para o eixo X
        df_analise_semeadura['periodo_mes_ano'] = df_analise_semeadura['periodo_semeadura']

        # Agrupar por período de semeadura e calcular estatísticas
        producao_por_periodo = df_analise_semeadura.groupby('periodo_mes_ano').agg({
            'prod_sc_ha_corr': ['mean', 'count', 'std'],
            'hibrido': 'nunique'
        }).round(2)

        # Renomear colunas
        producao_por_periodo.columns = [
            'Produtividade_Média', 'Número_Amostras', 'Desvio_Padrão', 'Número_Híbridos']

        # Ordenar por período (criar uma coluna temporária para ordenação)
        def converter_para_ordenacao(periodo_mes_ano):
            try:
                if "JAN a 10 FEV" in periodo_mes_ano:
                    return 1
                elif "11 FEV a 25 FEV" in periodo_mes_ano:
                    return 2
                elif "26 FEV+" in periodo_mes_ano:
                    return 3
                else:
                    return 4
            except:
                return 999

        producao_por_periodo['ordem_periodo'] = producao_por_periodo.index.map(
            converter_para_ordenacao)
        producao_por_periodo = producao_por_periodo.sort_values(
            'ordem_periodo')
        producao_por_periodo = producao_por_periodo.drop(
            'ordem_periodo', axis=1)

        # Gráfico de barras - Produção média por período
        fig_periodo = px.bar(
            x=producao_por_periodo.index,
            y=producao_por_periodo['Produtividade_Média'],
            title="Produção Média por Período de Semeadura",
            labels={'x': 'Período de Semeadura',
                    'y': 'Produção Média (sc/ha)'},
            text=[f"{valor:.1f} ({producao_por_periodo['Número_Amostras'].iloc[i]})"
                  for i, valor in enumerate(producao_por_periodo['Produtividade_Média'])],
            color=producao_por_periodo['Número_Amostras'],
            color_continuous_scale='Blues'
        )
        fig_periodo.update_traces(
            textposition='outside', textfont=dict(size=14, color='black'))

        # Calcular limite mínimo do eixo Y para melhor visualização
        min_prod = producao_por_periodo['Produtividade_Média'].min()
        max_prod = producao_por_periodo['Produtividade_Média'].max()
        range_prod = max_prod - min_prod
        # 10% abaixo do mínimo, mas não menor que 0
        y_min = max(0, min_prod - (range_prod * 0.1))

        fig_periodo.update_layout(
            height=600,
            xaxis_tickangle=-45,
            showlegend=False,
            title_font=dict(size=20, color='black'),
            xaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black')
            ),
            yaxis=dict(
                title_font=dict(size=16, color='black'),
                tickfont=dict(size=14, color='black'),
                # Ajustar escala Y
                range=[y_min, max_prod + (range_prod * 0.1)]
            )
        )
        st.plotly_chart(fig_periodo, use_container_width=True)

        # Análise detalhada por híbrido

        # Agrupar por híbrido e período
        producao_hibrido_periodo = df_analise_semeadura.groupby(['hibrido', 'periodo_mes_ano']).agg({
            'prod_sc_ha_corr': ['mean', 'count', 'std']
        }).round(2)

        # Renomear colunas
        producao_hibrido_periodo.columns = [
            'Produtividade_Média', 'Número_Amostras', 'Desvio_Padrão']
        producao_hibrido_periodo = producao_hibrido_periodo.reset_index()

        # Selecionar híbridos com mais amostras
        hibridos_principais = df_analise_semeadura['hibrido'].value_counts().head(
            10).index

        # Filtrar apenas os híbridos principais
        df_hibridos_principais = producao_hibrido_periodo[
            producao_hibrido_periodo['hibrido'].isin(hibridos_principais)
        ]

        if not df_hibridos_principais.empty:
            # Ordenar df_hibridos_principais pela mesma lógica de ordenação
            df_hibridos_principais['ordem_periodo'] = df_hibridos_principais['periodo_mes_ano'].map(
                converter_para_ordenacao)
            df_hibridos_principais = df_hibridos_principais.sort_values(
                'ordem_periodo')
            df_hibridos_principais = df_hibridos_principais.drop(
                'ordem_periodo', axis=1)

            # Obter a ordem correta dos períodos baseada no primeiro gráfico
            ordem_periodos = producao_por_periodo.index.tolist()

            # Gráfico de barras por híbrido
            fig_hibrido = px.bar(
                df_hibridos_principais,
                x='periodo_mes_ano',
                y='Produtividade_Média',
                color='hibrido',
                title="Produção Média por Híbrido e Período de Semeadura",
                labels={'x': 'Período de Semeadura',
                        'y': 'Produção Média (sc/ha)', 'color': 'Híbrido'},
                text=[f"{row['Produtividade_Média']:.1f} ({row['Número_Amostras']})"
                      for _, row in df_hibridos_principais.iterrows()],
                barmode='group'
            )

            # Forçar a ordem correta no eixo X
            fig_hibrido.update_layout(
                xaxis=dict(categoryorder='array',
                           categoryarray=ordem_periodos)
            )
            fig_hibrido.update_traces(
                textposition='outside', textfont=dict(size=14, color='black'))
            fig_hibrido.update_layout(
                height=600,
                xaxis_tickangle=-45,
                title_font=dict(size=20, color='black'),
                xaxis=dict(
                    title_font=dict(size=16, color='black'),
                    tickfont=dict(size=14, color='black')
                ),
                yaxis=dict(
                    title_font=dict(size=16, color='black'),
                    tickfont=dict(size=14, color='black')
                ),
                legend=dict(
                    font=dict(size=14, color='black')
                )
            )
            st.plotly_chart(fig_hibrido, use_container_width=True)

            # Tabela detalhada
            st.markdown("**Dados Detalhados por Híbrido:**")
            st.dataframe(df_hibridos_principais, use_container_width=True)

        # Exportar dados da análise
        st.markdown("### 💾 Exportar Dados da Análise")
        buffer_analise = io.BytesIO()
        df_analise_semeadura.to_excel(buffer_analise, index=False)
        buffer_analise.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (Análise Período Semeadura)",
            data=buffer_analise,
            file_name="analise_periodo_semeadura.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        st.info("Não há dados válidos de data de plantio para análise.")
else:
    st.info("Nenhum dado disponível para análise do período de semeadura.")
# --- FIM ANÁLISE PERÍODO SEMEADURA ---


# =========================
# GARANTIR FORMATO DE DATA BRASILEIRO EM data_plantio E data_colheita
# =========================


def formatar_datas_br(df):
    for col in ["data_plantio", "data_colheita"]:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col], errors='coerce').dt.strftime('%d/%m/%Y')
    return df


for _df in [gd_milho_2025, gd_milho_2025_tratado, df_comercial]:
    if _df is not None and not _df.empty:
        formatar_datas_br(_df)
