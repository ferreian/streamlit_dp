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

gd_milho_2024 = None
gd_milho_2023 = None

# =====================
# 1. IMPORTS E CONFIGS
# =====================

# Supabase config
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
if not SUPABASE_URL or not SUPABASE_KEY:
    st.warning(
        "URL ou chave do Supabase não encontrada. Defina as variáveis de ambiente SUPABASE_URL e SUPABASE_KEY.")
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
                Análise Comercial - Geração de Demanda (análise Head to Head)
            </h1>
            <h3 style="margin-top: 0; color: #e0e0e0; font-weight: 400; font-size: 1.2em;">
                Visualize e explore os dados de demanda gerados pela análise Head to Head.
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
        # carregar_tabela_supabase.clear()  # NÃO EXISTE .clear() para função normal
        dataframes = {tabela: fetch_table(tabela)
                      for tabela in TABELAS_COMERCIAL}
        for nome, df in dataframes.items():
            st.session_state[nome] = df
        total_time = time.time() - start_time
        st.success(
            f"✅ Dados comerciais carregados direto do Supabase! (Tempo: {total_time:.2f}s)")

# =========================
# VISUALIZAÇÃO DAS TABELAS CARREGADAS (BLOCO FÁCIL DE COMENTAR)
# =========================
# --- INÍCIO VISUALIZAÇÃO TABELAS ---
# for nome, label in zip(["resultados", "usuarios", "fazenda"], ["resultados", "usuarios", "fazenda"]):
#     if nome in st.session_state and not st.session_state[nome].empty:
#         st.markdown(f"### Tabela: {label}")
#         st.dataframe(st.session_state[nome], use_container_width=True)
#         # Botão para exportar em Excel
#         buffer = io.BytesIO()
#         st.session_state[nome].to_excel(buffer, index=False)
#         buffer.seek(0)
#         st.download_button(
#             label=f"⬇️ Baixar Excel ({label})",
#             data=buffer,
#             file_name=f"{label}.xlsx",
#             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#         )
#     else:
#         st.info(f"Tabela {label} não carregada ou vazia.")
# --- FIM VISUALIZAÇÃO TABELAS ---

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
# VISUALIZAÇÃO E EXPORTAÇÃO DO DATAFRAME TRATADO (BLOCO FÁCIL DE COMENTAR)
# =========================
# --- INÍCIO VISUALIZAÇÃO/EXPORTAÇÃO DF_RESULTADOS_TRATADO ---
# if df_resultados_tratado is not None and not df_resultados_tratado.empty:
#     st.markdown("### Tabela: resultados tratados")
#     st.dataframe(df_resultados_tratado, use_container_width=True)
#     buffer_tratado = io.BytesIO()
#     df_resultados_tratado.to_excel(buffer_tratado, index=False)
#     buffer_tratado.seek(0)
#     st.download_button(
#         label="⬇️ Baixar Excel (resultados_tratados)",
#         data=buffer_tratado,
#         file_name="resultados_tratados.xlsx",
#         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )
# else:
#     st.info("Tabela resultados tratados não gerada ou está vazia.")
# --- FIM VISUALIZAÇÃO/EXPORTAÇÃO DF_RESULTADOS_TRATADO ---

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
# --- FIM TRATAMENTO DF FAZENDA ---

# =========================
# MERGE RESULTADOS + FAZENDA PARA CRIAR gd_milho_2025
# =========================
# --- INÍCIO MERGE GD_MILHO_2025 ---
gd_milho_2025 = None
if df_resultados_tratado is not None and not df_resultados_tratado.empty and \
   df_fazenda_tratada is not None and not df_fazenda_tratada.empty:
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
# VISUALIZAÇÃO E EXPORTAÇÃO DO DATAFRAME gd_milho_2025 (BLOCO FÁCIL DE COMENTAR)
# =========================
# --- INÍCIO VISUALIZAÇÃO/EXPORTAÇÃO GD_MILHO_2025 ---
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
# --- FIM VISUALIZAÇÃO/EXPORTAÇÃO GD_MILHO_2025 ---

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

# Remoção de outliers por Z-Score para gd_milho_2024
if gd_milho_2024 is not None and not gd_milho_2024.empty:
    gd_milho_2024_tratado, gd_milho_2024_outliers_tratado, parametros_zscore_2024_tratado = remover_outliers_zscore(
        gd_milho_2024, ['prod_sc_ha_corr', 'umidade'], threshold=threshold_zscore
    )
else:
    gd_milho_2024_tratado, gd_milho_2024_outliers_tratado, parametros_zscore_2024_tratado = None, None, None

# Remoção de outliers por Z-Score para gd_milho_2023
if gd_milho_2023 is not None and not gd_milho_2023.empty:
    gd_milho_2023_tratado, gd_milho_2023_outliers_tratado, parametros_zscore_2023_tratado = remover_outliers_zscore(
        gd_milho_2023, ['prod_sc_ha_corr', 'umidade'], threshold=threshold_zscore
    )
else:
    gd_milho_2023_tratado, gd_milho_2023_outliers_tratado, parametros_zscore_2023_tratado = None, None, None


# Visualização dos outliers removidos
if gd_milho_2025_outliers is not None and not gd_milho_2025_outliers.empty:
    # st.markdown("### Linhas removidas como outliers (Z-Score)")
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
# VISUALIZAÇÃO DO ARQUIVO EXCEL gd_milho_2024 (BLOCO FÁCIL DE COMENTAR)
# =========================
# --- INÍCIO VISUALIZAÇÃO/EXPORTAÇÃO GD_MILHO_2024 ---
gd_milho_2024 = None
caminho_gd_2024 = os.path.join("datasets", "gd_milho_2024.xlsx")
if os.path.exists(caminho_gd_2024):
    gd_milho_2024 = pd.read_excel(caminho_gd_2024)
    st.markdown("### Resultados 2024")
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
        GD Milho 2024 - Completo    
    </div>
    """,
        unsafe_allow_html=True
    )
    st.dataframe(gd_milho_2024, use_container_width=True)
    buffer_gd_2024 = io.BytesIO()
    gd_milho_2024.to_excel(buffer_gd_2024, index=False)
    buffer_gd_2024.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel (gd_milho_2024)",
        data=buffer_gd_2024,
        file_name="gd_milho_2024.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_gd_milho_2024"
    )
else:
    st.info("Arquivo gd_milho_2024.xlsx não encontrado em datasets/.")
# --- FIM VISUALIZAÇÃO/EXPORTAÇÃO GD_MILHO_2024 ---

# =========================
# REMOÇÃO DE OUTLIERS (Z-SCORE) EM gd_milho_2024 (BLOCO FÁCIL DE COMENTAR)
# =========================
# --- INÍCIO REMOÇÃO OUTLIERS Z-SCORE gd_milho_2024 ---
gd_milho_2024_tratado, gd_milho_2024_outliers_tratado, parametros_zscore_2024_tratado = None, None, None
if gd_milho_2024 is not None and not gd_milho_2024.empty:
    # Reutiliza a função remover_outliers_zscore já definida
    gd_milho_2024_tratado, gd_milho_2024_outliers_tratado, parametros_zscore_2024_tratado = remover_outliers_zscore(
        gd_milho_2024, ['prod_sc_ha_corr', 'umidade'], threshold=threshold_zscore
    )
    # Visualização dos outliers removidos
    # st.markdown("### Linhas removidas como outliers (Z-Score) - gd_milho_2024")
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
        GD Milho 2024 - Outliers (Z-Score)    
    </div>
    """,
        unsafe_allow_html=True
    )
    if gd_milho_2024_outliers_tratado is not None and not gd_milho_2024_outliers_tratado.empty:
        st.dataframe(gd_milho_2024_outliers_tratado, use_container_width=True)
        buffer_outliers_2024 = io.BytesIO()
        gd_milho_2024_outliers_tratado.to_excel(
            buffer_outliers_2024, index=False)
        buffer_outliers_2024.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (outliers_removidos_2024)",
            data=buffer_outliers_2024,
            file_name="outliers_removidos_2024.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_outliers_removidos_2024"
        )
        # Exibir parâmetros do Z-Score usados
        st.markdown("**Parâmetros do Z-Score por coluna (gd_milho_2024):**")
        for coluna, info in parametros_zscore_2024_tratado.items():
            st.markdown(
                f"<div style='background: #f5f7fa; border-radius: 8px; padding: 10px; margin-bottom: 8px;'><b>{coluna}</b><br>Média: {info['media']:.2f} | Desvio padrão: {info['std']:.2f}<br>Limite inferior: {info['limite_inferior']:.2f} | Limite superior: {info['limite_superior']:.2f}</div>", unsafe_allow_html=True)
    else:
        st.info("Nenhuma linha foi removida como outlier com o threshold atual.")
    # Visualização do DataFrame tratado (sem outliers)
    # st.markdown("### Tabela: gd_milho_2024 (sem outliers)")
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
        GD Milho 2024 - Sem Outliers    
    </div>
    """,
        unsafe_allow_html=True
    )
    if gd_milho_2024_tratado is not None and not gd_milho_2024_tratado.empty:
        st.dataframe(gd_milho_2024_tratado, use_container_width=True)
        buffer_gd_2024_tratado = io.BytesIO()
        gd_milho_2024_tratado.to_excel(buffer_gd_2024_tratado, index=False)
        buffer_gd_2024_tratado.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (gd_milho_2024_tratado)",
            data=buffer_gd_2024_tratado,
            file_name="gd_milho_2024_tratado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_gd_milho_2024_tratado"
        )
    else:
        st.info("Tabela gd_milho_2024_tratado não gerada ou está vazia.")
# --- FIM REMOÇÃO OUTLIERS Z-SCORE gd_milho_2024 ---

# =========================
# VISUALIZAÇÃO E TRATAMENTO DO ARQUIVO EXCEL gd_milho_2023 (BLOCO FÁCIL DE COMENTAR)
# =========================
# --- INÍCIO VISUALIZAÇÃO/EXPORTAÇÃO/TRATAMENTO GD_MILHO_2023 ---
gd_milho_2023 = None
caminho_gd_2023 = os.path.join("datasets", "gd_milho_2023.xlsx")
if os.path.exists(caminho_gd_2023):
    gd_milho_2023 = pd.read_excel(caminho_gd_2023)
    st.markdown("### Resultados 2023")
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
        GD Milho 2023 - Completo    
    </div>
    """,
        unsafe_allow_html=True
    )
    st.dataframe(gd_milho_2023, use_container_width=True)
    buffer_gd_2023 = io.BytesIO()
    gd_milho_2023.to_excel(buffer_gd_2023, index=False)
    buffer_gd_2023.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel (gd_milho_2023)",
        data=buffer_gd_2023,
        file_name="gd_milho_2023.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_gd_milho_2023"
    )
    # Remoção de outliers por Z-Score
    gd_milho_2023_tratado, gd_milho_2023_outliers_tratado, parametros_zscore_2023_tratado = remover_outliers_zscore(
        gd_milho_2023, ['prod_sc_ha_corr', 'umidade'], threshold=threshold_zscore
    )
    # st.markdown("### Linhas removidas como outliers (Z-Score) - gd_milho_2023")
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
        GD Milho 2023 - Outliers (Z-Score)  
    </div>
    """,
        unsafe_allow_html=True
    )
    if gd_milho_2023_outliers_tratado is not None and not gd_milho_2023_outliers_tratado.empty:
        st.dataframe(gd_milho_2023_outliers_tratado, use_container_width=True)
        buffer_outliers_2023 = io.BytesIO()
        gd_milho_2023_outliers_tratado.to_excel(
            buffer_outliers_2023, index=False)
        buffer_outliers_2023.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (outliers_removidos_2023)",
            data=buffer_outliers_2023,
            file_name="outliers_removidos_2023.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_outliers_removidos_2023"
        )
        st.markdown("**Parâmetros do Z-Score por coluna (gd_milho_2023):**")
        for coluna, info in parametros_zscore_2023_tratado.items():
            st.markdown(
                f"<div style='background: #f5f7fa; border-radius: 8px; padding: 10px; margin-bottom: 8px;'><b>{coluna}</b><br>Média: {info['media']:.2f} | Desvio padrão: {info['std']:.2f}<br>Limite inferior: {info['limite_inferior']:.2f} | Limite superior: {info['limite_superior']:.2f}</div>", unsafe_allow_html=True)
    else:
        st.info("Nenhuma linha foi removida como outlier com o threshold atual.")
    # st.markdown("### Tabela: gd_milho_2023 (sem outliers)")
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
        GD Milho 2023 - Sem Outliers     
    </div>
    """,
        unsafe_allow_html=True
    )
    if gd_milho_2023_tratado is not None and not gd_milho_2023_tratado.empty:
        st.dataframe(gd_milho_2023_tratado, use_container_width=True)
        buffer_gd_2023_tratado = io.BytesIO()
        gd_milho_2023_tratado.to_excel(buffer_gd_2023_tratado, index=False)
        buffer_gd_2023_tratado.seek(0)
        st.download_button(
            label="⬇️ Baixar Excel (gd_milho_2023_tratado)",
            data=buffer_gd_2023_tratado,
            file_name="gd_milho_2023_tratado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_gd_milho_2023_tratado"
        )
    else:
        st.info("Tabela gd_milho_2023_tratado não gerada ou está vazia.")
else:
    st.info("Arquivo gd_milho_2023.xlsx não encontrado em datasets/.")
# --- FIM VISUALIZAÇÃO/EXPORTAÇÃO/TRATAMENTO GD_MILHO_2023 ---

# =========================
# CONCATENAÇÃO DOS DATAFRAMES TRATADOS EM df_comercial (BLOCO FÁCIL DE COMENTAR)
# =========================
# --- INÍCIO CONCATENAÇÃO/EXPORTAÇÃO DF_COMERCIAL ---
# lista_df = []
# for df in [gd_milho_2025_tratado, gd_milho_2024_tratado, gd_milho_2023_tratado]:
#     if df is not None and not df.empty:
#         lista_df.append(df)
# df_comercial = None
# if lista_df:
#     df_comercial = pd.concat(lista_df, ignore_index=True)
#     # Visualização/exportação do df_comercial (todos os anos, sem outliers)
#     if df_comercial is not None and not df_comercial.empty:
#         st.markdown("### Tabela: df_comercial (todos os anos, sem outliers)")
#         st.dataframe(df_comercial, use_container_width=True)
#         buffer_comercial = io.BytesIO()
#         df_comercial.to_excel(buffer_comercial, index=False)
#         buffer_comercial.seek(0)
#         st.download_button(
#             label="⬇️ Baixar Excel (df_comercial)",
#             data=buffer_comercial,
#             file_name="df_comercial.xlsx",
#             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#             key="download_df_comercial"
#         )
#     else:
#         st.info("Nenhum DataFrame tratado disponível para concatenar em df_comercial.")
# --- FIM CONCATENAÇÃO/EXPORTAÇÃO DF_COMERCIAL ---

# =========================
# FUNÇÃO CACHEADA PARA PREPARAR DF_COMERCIAL
# =========================


@st.cache_data
def preparar_df_comercial(gd_milho_2025_tratado, gd_milho_2024_tratado, gd_milho_2023_tratado):
    lista_df = []
    for df in [gd_milho_2025_tratado, gd_milho_2024_tratado, gd_milho_2023_tratado]:
        if df is not None and not df.empty:
            lista_df.append(df)
    df_comercial = None
    if lista_df:
        df_comercial = pd.concat(lista_df, ignore_index=True)
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
# FILTRO INTERATIVO NO SIDEBAR PARA df_comercial (BLOCO FÁCIL DE COMENTAR)
# =========================
# --- INÍCIO FILTRO SIDEBAR DF_FILTRADO ---
df_comercial = preparar_df_comercial(
    gd_milho_2025_tratado, gd_milho_2024_tratado, gd_milho_2023_tratado)
df_filtrado = None
if df_comercial is not None and not df_comercial.empty:
    df_filtrado = df_comercial.copy()
    filter_keys = [
        ("safra", "Safra", "safra"),
        ("macroRegiaoMilho", "Macro Região", "macro"),
        ("conjuntaGeralMilhoSafrinha", "Conjunta Geral", "conjunta"),
        ("subConjuntaMilhoSafrinha", "Sub Conjunta", "subconjunta"),
        ("mrhMilho", "MRH", "mrh"),
        ("siglaEstado", "Estado", "estado"),
        ("cidade", "Cidade", "cidade"),
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
    # st.markdown("### Resultados GD Milho")
    # st.markdown(
        # """
    # <div style="
    #    background-color: #e7f0fa;
    #    border-left: 6px solid #0070C0;
    #    padding: 12px 18px;
    #    margin-bottom: 12px;
    #    border-radius: 6px;
    #    font-size: 1.15em;
    #    color: #22223b;
    #    font-weight: 600;
    # ">
    #    GD Milho - Completo  (todos os anos, sem outliers)
    # </div>
    # """,
        # unsafe_allow_html=True
    # )
    # st.dataframe(df_filtrado, use_container_width=True)
    # buffer_filtrado = io.BytesIO()
    # df_filtrado.to_excel(buffer_filtrado, index=False)
    # buffer_filtrado.seek(0)
    # st.download_button(
    #    label="⬇️ Baixar Excel (df_filtrado)",
    #    data=buffer_filtrado,
    #    file_name="df_filtrado.xlsx",
    #    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    #    key="download_df_filtrado"
    # )
# else:
    # st.info("df_comercial não gerado ou está vazio para aplicar filtros.")
# --- FIM FILTRO SIDEBAR DF_FILTRADO ---

# --- INÍCIO CRIAÇÃO DF_ANALISE_H2H ---
df_analise_h2h = None
if df_filtrado is not None and not df_filtrado.empty:
    df_analise_h2h = df_filtrado.copy()
# --- FIM CRIAÇÃO DF_ANALISE_H2H ---

# =========================
# GERAÇÃO DE DEMANDA - MILHO (BLOCO FÁCIL DE COMENTAR)
# =========================
# --- INÍCIO GERAÇÃO DE DEMANDA MILHO ---
st.subheader("Geração de Demanda - Milho")
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
        Dados Conjuntos para Análise Head to Head
    </div>
    """,
    unsafe_allow_html=True
)
df_filtrado_customizado = None
if df_filtrado is not None and not df_filtrado.empty:
    df_filtrado_customizado = df_filtrado.copy()
    gb = GridOptionsBuilder.from_dataframe(df_filtrado_customizado)
    gb.configure_pagination(paginationAutoPageSize=True)
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
        label="⬇️ Baixar Excel (Geração de Demanda - Milho)",
        data=buffer,
        file_name="geracao_demanda_milho.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Nenhum dado disponível para exibir em Geração de Demanda - Milho.")
# --- FIM GERAÇÃO DE DEMANDA MILHO ---


# =========================
# SELEÇÃO DE HÍBRIDOS PARA ANÁLISE H2H (NA PÁGINA PRINCIPAL)
# =========================
st.markdown('<h3 style="margin-top: 2em; margin-bottom: 0.5em; color: #0070C0; font-weight: 700;">Selecione os híbridos para análise H2H</h3>', unsafe_allow_html=True)
hibridos_unicos = sorted(df_analise_h2h['hibrido'].dropna(
).unique()) if df_analise_h2h is not None else []
head_selected = None
check_selected = None
if hibridos_unicos:
    col1, colx, col2 = st.columns([5, 1, 5])
    with col1:
        head_selected = st.selectbox(
            'Híbrido Head', hibridos_unicos, key='h2h_head_dropdown')
    with colx:
        st.markdown(
            '<div style="text-align:center;font-size:2em;font-weight:700;line-height:2.5em;">×</div>', unsafe_allow_html=True)
    with col2:
        check_options = [h for h in hibridos_unicos if h != head_selected]
        check_selected = st.selectbox(
            'Híbrido Check', check_options, key='h2h_check_dropdown')
    if head_selected and check_selected:
        if st.button('Rodar Análise H2H', key='btn_run_h2h_page'):
            st.session_state['run_h2h'] = True
else:
    st.info('Nenhum híbrido disponível para seleção.')

# =========================
# ANÁLISE HEAD TO HEAD (H2H) - MILHO (APENAS PARA O PAR SELECIONADO)
# =========================
if st.session_state.get('run_h2h', False) and head_selected and check_selected:
    resultados_h2h = []
    locais = pd.Series(df_analise_h2h['cidade_siglaEstado']).dropna().unique()
    for local in locais:
        row_head = df_analise_h2h[(df_analise_h2h['hibrido'] == head_selected) & (
            df_analise_h2h['cidade_siglaEstado'] == local)]
        row_check = df_analise_h2h[(df_analise_h2h['hibrido'] == check_selected) & (
            df_analise_h2h['cidade_siglaEstado'] == local)]
        if not isinstance(row_head, pd.DataFrame):
            row_head = pd.DataFrame(row_head)
        if not isinstance(row_check, pd.DataFrame):
            row_check = pd.DataFrame(row_check)
        if not row_head.empty and not row_check.empty:
            head_mean = row_head.iloc[0]['prod_sc_ha_corr'] if 'prod_sc_ha_corr' in row_head else None
            check_mean = row_check.iloc[0]['prod_sc_ha_corr'] if 'prod_sc_ha_corr' in row_check else None
            diff = head_mean - check_mean if head_mean is not None and check_mean is not None else None
            vitoria = int(diff > 0) if diff is not None else None
            resultados_h2h.append({
                'Local': local,
                'Head': head_selected,
                'Check': check_selected,
                'Head prod@13.5% (sc/ha)': head_mean,
                'Check prod@13.5% (sc/ha)': check_mean,
                'Diferença (sc/ha)': diff,
                'Vitória Head': vitoria,
                'Head umidade (%)': row_head.iloc[0]['umidade'] if 'umidade' in row_head else None,
                'Check umidade (%)': row_check.iloc[0]['umidade'] if 'umidade' in row_check else None,
            })
    df_resultado_h2h = pd.DataFrame(resultados_h2h)
    # Exibição
    if not df_resultado_h2h.empty:
        # Seleção e ordenação das colunas conforme solicitado
        colunas_ordem = [
            'Local',
            'Head',
            'Head umidade (%)',
            'Head prod@13.5% (sc/ha)',
            'Check',
            'Check umidade (%)',
            'Check prod@13.5% (sc/ha)',
            'Diferença (sc/ha)'
        ]
        colunas_existentes = [
            col for col in colunas_ordem if col in df_resultado_h2h.columns]
        df_resultado_h2h = df_resultado_h2h[colunas_existentes]
        st.subheader('Análise H2H - Milho')
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
                Resultados da análise head to head entre híbridos por local
            </div>
            """,
            unsafe_allow_html=True
        )
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
        gb_h2h = GridOptionsBuilder.from_dataframe(df_resultado_h2h)
        # Coloração condicional para Head prod@13.5% (sc/ha)
        if 'Head prod@13.5% (sc/ha)' in df_resultado_h2h.columns:
            gb_h2h.configure_column(
                'Head prod@13.5% (sc/ha)',
                valueFormatter="value != null ? value.toFixed(1) : ''",
                cellStyle=cell_style_head
            )
        # Coloração condicional para Check prod@13.5% (sc/ha)
        if 'Check prod@13.5% (sc/ha)' in df_resultado_h2h.columns:
            gb_h2h.configure_column(
                'Check prod@13.5% (sc/ha)',
                valueFormatter="value != null ? value.toFixed(1) : ''",
                cellStyle=cell_style_check
            )
        # Coloração condicional para Diferença (sc/ha)
        if 'Diferença (sc/ha)' in df_resultado_h2h.columns:
            gb_h2h.configure_column(
                'Diferença (sc/ha)',
                valueFormatter="value != null ? value.toFixed(1) : ''",
                cellStyle=cell_style_diff
            )
        # Demais colunas padrão
        for col in df_resultado_h2h.columns:
            if col not in ['Head prod@13.5% (sc/ha)', 'Check prod@13.5% (sc/ha)', 'Diferença (sc/ha)']:
                gb_h2h.configure_column(
                    col,
                    headerClass='ag-header-bold',
                    menuTabs=['generalMenuTab',
                              'filterMenuTab', 'columnsMenuTab']
                )
        gb_h2h.configure_default_column(
            editable=False, groupable=True, filter=True, resizable=True, cellStyle={'fontSize': '13px'})
        gb_h2h.configure_grid_options(headerHeight=32)
        grid_options_h2h = gb_h2h.build()
        custom_css_h2h = {
            ".ag-header-cell-label": {"font-weight": "bold", "font-size": "1.15em", "color": "#222"},
            ".ag-cell": {"color": "#222", "font-size": "1em"}
        }
        with st.expander("Ver tabela da Análise H2H", expanded=True):
            AgGrid(
                df_resultado_h2h,
                gridOptions=grid_options_h2h,
                enable_enterprise_modules=True,
                fit_columns_on_grid_load=False,
                theme="streamlit",
                height=500,
                reload_data=True,
                custom_css=custom_css_h2h,
                key="aggrid_h2h_milho",
                allow_unsafe_jscode=True
            )
            # Botão para exportar em Excel
            buffer_h2h = io.BytesIO()
            df_resultado_h2h.to_excel(buffer_h2h, index=False)
            buffer_h2h.seek(0)
            st.download_button(
                label='⬇️ Baixar Excel (Análise H2H - Milho)',
                data=buffer_h2h,
                file_name='analise_h2h_milho.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        # ====== CARTÕES DE RESUMO H2H (agora abaixo da tabela) ======
        if 'Diferença (sc/ha)' in df_resultado_h2h.columns:
            num_locais = df_resultado_h2h.shape[0]
            vitorias = (df_resultado_h2h["Diferença (sc/ha)"] > 1).sum()
            max_diff = df_resultado_h2h.loc[df_resultado_h2h["Diferença (sc/ha)"]
                                            > 1, "Diferença (sc/ha)"].max()
            if pd.isna(max_diff):
                max_diff = 0
            media_diff_vitorias = df_resultado_h2h.loc[df_resultado_h2h[
                "Diferença (sc/ha)"] > 1, "Diferença (sc/ha)"].mean()
            if pd.isna(media_diff_vitorias):
                media_diff_vitorias = 0
            empates = ((df_resultado_h2h["Diferença (sc/ha)"] >= -1)
                       & (df_resultado_h2h["Diferença (sc/ha)"] <= 1)).sum()
            derrotas = (df_resultado_h2h["Diferença (sc/ha)"] < -1).sum()
            min_diff = df_resultado_h2h.loc[df_resultado_h2h["Diferença (sc/ha)"]
                                            < -1, "Diferença (sc/ha)"].min()
            if pd.isna(min_diff):
                min_diff = 0
            media_diff_derrotas = df_resultado_h2h.loc[df_resultado_h2h[
                "Diferença (sc/ha)"] < -1, "Diferença (sc/ha)"].mean()
            if pd.isna(media_diff_derrotas):
                media_diff_derrotas = 0

            col4, col5, col6, col7 = st.columns(4)
            # 📍 Locais
            with col4:
                st.markdown(f"""
                    <div style=\"background-color:#f2f2f2; padding:15px; border-radius:10px; text-align:center;\">
                        <h5 style=\"font-weight:bold; color:#333;\">📍 Número de Locais</h5>
                        <div style=\"font-size: 20px; font-weight:bold; color:#f2f2f2;\">&nbsp;</div>
                        <h2 style=\"margin: 10px 0; color:#333; font-weight:bold; font-size: 4em;\">{num_locais}</h2>
                        <div style=\"font-size: 20px; font-weight:bold; color:#f2f2f2;\">&nbsp;</div>
                    </div>
                """, unsafe_allow_html=True)
            # ✅ Vitórias
            with col5:
                st.markdown(f"""
                    <div style=\"background-color:#01B8AA80; padding:15px; border-radius:10px; text-align:center;\">
                        <h5 style=\"font-weight:bold; color:#004d47;\">✅ Vitórias</h5>
                        <div style=\"font-size: 20px; font-weight:bold; color:#004d47;\">Max: {max_diff:.1f} sc/ha</div>
                        <h2 style=\"margin: 10px 0; color:#004d47; font-weight:bold; font-size: 4em;\">{vitorias}</h2>
                        <div style=\"font-size: 20px; font-weight:bold; color:#004d47;\">Média: {media_diff_vitorias:.1f} sc/ha</div>
                    </div>
                """, unsafe_allow_html=True)
            # ➖ Empates
            with col6:
                st.markdown(f"""
                    <div style=\"background-color:#F2C80F80; padding:15px; border-radius:10px; text-align:center;\">
                        <h5 style=\"font-weight:bold; color:#8a7600;\">➖ Empates</h5>
                        <div style=\"font-size: 20px; font-weight:bold; color:#8a7600;\">Entre -1 e 1 sc/ha</div>
                        <h2 style=\"margin: 10px 0; color:#8a7600; font-weight:bold; font-size: 4em;\">{empates}</h2>
                        <div style=\"font-size: 20px; font-weight:bold; color:#F2C80F80;\">&nbsp;</div>
                    </div>
                """, unsafe_allow_html=True)
            # ❌ Derrotas
            with col7:
                st.markdown(f"""
                    <div style=\"background-color:#FD625E80; padding:15px; border-radius:10px; text-align:center;\">
                        <h5 style=\"font-weight:bold; color:#7c1f1c;\">❌ Derrotas</h5>
                        <div style=\"font-size: 20px; font-weight:bold; color:#7c1f1c;\">Min: {min_diff:.1f} sc/ha</div>
                        <h2 style=\"margin: 10px 0; color:#7c1f1c; font-weight:bold; font-size: 4em;\">{derrotas}</h2>
                        <div style=\"font-size: 20px; font-weight:bold; color:#7c1f1c;\">Média: {media_diff_derrotas:.1f} sc/ha</div>
                    </div>
                """, unsafe_allow_html=True)
        st.markdown("")
        # ====== GRÁFICO DE PIZZA ======
        col7g, col8g, col9g = st.columns([1, 2, 1])
        with col8g:
            st.markdown("""
                <div style=\"background-color: #f9f9f9; padding: 10px; border-radius: 12px; \
                            box-shadow: 0px 2px 5px rgba(0,0,0,0.1); text-align: center;\">
                    <h4 style=\"margin-bottom: 0.5rem;\">Resultado Geral do Head</h4>
            """, unsafe_allow_html=True)
            fig = go.Figure(data=[go.Pie(
                labels=["Vitórias", "Empates", "Derrotas"],
                values=[vitorias, empates, derrotas],
                marker=dict(colors=["#01B8AA", "#F2C80F", "#FD625E"]),
                hole=0.6,
                textinfo='label+percent',
                textposition='outside',
                textfont=dict(size=16, color="black", family="Arial Black"),
                pull=[0.04, 0.04, 0.04],
            )])
            fig.update_layout(
                margin=dict(t=10, b=80, l=10, r=10),
                height=370,
                showlegend=False
            )
            fig.update_traces(automargin=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        # ====== GRÁFICO DE BARRAS HORIZONTAL DIFERENÇA POR LOCAL ======
        # Só plota se houver dados válidos
        if not df_resultado_h2h.empty and 'Diferença (sc/ha)' in df_resultado_h2h.columns and 'Head prod@13.5% (sc/ha)' in df_resultado_h2h.columns and 'Check prod@13.5% (sc/ha)' in df_resultado_h2h.columns:
            df_graf = df_resultado_h2h.copy()
            df_graf = df_graf[(df_graf["Head prod@13.5% (sc/ha)"] > 0)
                              & (df_graf["Check prod@13.5% (sc/ha)"] > 0)]
            if not df_graf.empty:
                df_graf_sorted = df_graf.sort_values(by=["Diferença (sc/ha)"])
                cores_local = df_graf_sorted["Diferença (sc/ha)"].apply(
                    lambda x: "#01B8AA" if x > 1 else "#FD625E" if x < -1 else "#F2C80F"
                )
                # Se tiver coluna 'Local', usa, senão usa o índice
                nome_col_local = 'Local'
                if nome_col_local not in df_graf_sorted.columns:
                    df_graf_sorted[nome_col_local] = df_graf_sorted.index.astype(
                        str)
                st.markdown(f"""
                    <div style='background-color: #e7f0fa; border-left: 6px solid #0070C0; padding: 10px 18px; margin-bottom: 8px; border-radius: 6px; font-size: 1.1em; color: #22223b; font-weight: 600;'>
                        Diferença de Produtividade por Local — <b>{head_selected} × {check_selected}</b>
                    </div>
                """, unsafe_allow_html=True)
                fig_diff_local = go.Figure()
                fig_diff_local.add_trace(go.Bar(
                    y=df_graf_sorted[nome_col_local],
                    x=df_graf_sorted["Diferença (sc/ha)"],
                    orientation='h',
                    text=df_graf_sorted["Diferença (sc/ha)"].round(1),
                    textposition="outside",
                    textfont=dict(size=13, family="Arial Black",
                                  color="black"),
                    marker_color=cores_local
                ))
                fig_diff_local.update_layout(
                    title=dict(
                        text=f"Diferença de Produtividade por Local — {head_selected} × {check_selected}",
                        font=dict(size=20, color="black")
                    ),
                    xaxis=dict(
                        title=dict(text="<b>Diferença (sc/ha)</b>",
                                   font=dict(size=14, family="Arial Black", color="black")),
                        tickfont=dict(
                            size=13, family="Arial Black", color="black")
                    ),
                    yaxis=dict(
                        title=dict(text="<b>Local</b>", font=dict(size=14,
                                   family="Arial Black", color="black")),
                        tickfont=dict(
                            size=13, family="Arial Black", color="black")
                    ),
                    margin=dict(t=30, b=30, l=90, r=30),
                    height=700,
                    showlegend=False
                )
                st.plotly_chart(fig_diff_local, use_container_width=True)
    # Reset flag para não rodar de novo até clicar
    st.session_state['run_h2h'] = False

    # (Removido: bloco de Análise MultiCheck)

# =========================
# GARANTIR FORMATO DE DATA BRASILEIRO EM data_plantio E data_colheita
# =========================


def formatar_datas_br(df):
    for col in ["data_plantio", "data_colheita"]:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col], errors='coerce').dt.strftime('%d/%m/%Y')
    return df


for _df in [gd_milho_2025, gd_milho_2024, gd_milho_2023, gd_milho_2025_tratado, gd_milho_2024_tratado, gd_milho_2023_tratado, df_comercial]:
    if _df is not None and not _df.empty:
        formatar_datas_br(_df)

# --- DEBUG: SHAPES DOS DATAFRAMES ANTES E DEPOIS DOS FILTROS E OUTLIERS ---
# (Removido)

# --- DEBUG: VALORES ÚNICOS DA COLUNA SAFRA ---
# (Removido)

# E dentro da função preparar_df_comercial, remova todos os st.write de debug antes e depois do merge.
# --- FIM DEBUG ---
