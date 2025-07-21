import streamlit as st
import pandas as pd
import numpy as np

st.title("🛠️ Página de Debug de DataFrames e Variáveis")

# DataFrames principais do processamento
st.header("DataFrame Final (Tratado)")
df_final = st.session_state.get("df_avTratamentoMilho")
if df_final is not None:
    st.write(f"Shape: {df_final.shape}")
    st.dataframe(df_final.head(20), use_container_width=True)
    st.write("Colunas:", df_final.columns.tolist())
    # Botão para exportar para Excel
    import io
    buffer = io.BytesIO()
    df_final.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel do DataFrame Final",
        data=buffer,
        file_name="df_avTratamentoMilho_debug.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("DataFrame final não carregado.")

st.header("DataFrame Intermediário AV2")
df_av2 = st.session_state.get("df_av2TratamentoMilho_merged")
if df_av2 is not None:
    st.write(f"Shape: {df_av2.shape}")
    st.dataframe(df_av2.head(20), use_container_width=True)
    # Botão para exportar para Excel
    import io
    buffer_av2 = io.BytesIO()
    df_av2.to_excel(buffer_av2, index=False)
    buffer_av2.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel do DataFrame AV2",
        data=buffer_av2,
        file_name="df_av2TratamentoMilho_merged_debug.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("DataFrame AV2 não carregado.")

st.header("DataFrame Intermediário AV3")
df_av3 = st.session_state.get("df_av3TratamentoMilho_merged")
if df_av3 is not None:
    st.write(f"Shape: {df_av3.shape}")
    st.dataframe(df_av3.head(20), use_container_width=True)
    # Botão para exportar para Excel
    import io
    buffer_av3 = io.BytesIO()
    df_av3.to_excel(buffer_av3, index=False)
    buffer_av3.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel do DataFrame AV3",
        data=buffer_av3,
        file_name="df_av3TratamentoMilho_merged_debug.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("DataFrame AV3 não carregado.")

st.header("DataFrame Intermediário AV4")
df_av4 = st.session_state.get("df_av4TratamentoMilho_merged")
if df_av4 is not None:
    st.write(f"Shape: {df_av4.shape}")
    st.dataframe(df_av4.head(20), use_container_width=True)
    # Botão para exportar para Excel
    import io
    buffer_av4 = io.BytesIO()
    df_av4.to_excel(buffer_av4, index=False)
    buffer_av4.seek(0)
    st.download_button(
        label="⬇️ Baixar Excel do DataFrame AV4",
        data=buffer_av4,
        file_name="df_av4TratamentoMilho_merged_debug.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("DataFrame AV4 não carregado.")


st.divider()
st.header("Debug dos Cálculos de Médias (colunas envolvidas e resultado)")

# Dicionário igual ao do processamento para debug
colunas_medias = {
    "media_NumPlantas10metros": [
        "planta1NumPlantas10metros",
        "planta2NumPlantas10metros",
        "planta3NumPlantas10metros",
        "planta4NumPlantas10metros",
        "planta5NumPlantas10metros"
    ],
    "media_NumPlantasAcamadas": [
        "planta1NumPlantasAcamadas",
        "planta2NumPlantasAcamadas",
        "planta3NumPlantasAcamadas",
        "planta4NumPlantasAcamadas",
        "planta5NumPlantasAcamadas"
    ],
    "media_NumPlantasQuebradas": [
        "planta1NumPlantasQuebradas",
        "planta2NumPlantasQuebradas",
        "planta3NumPlantasQuebradas",
        "planta4NumPlantasQuebradas",
        "planta5NumPlantasQuebradas"
    ],
    "media_NumPlantasDominadas": [
        "planta1NumPlantasDominadas",
        "planta2NumPlantasDominadas",
        "planta3NumPlantasDominadas",
        "planta4NumPlantasDominadas",
        "planta5NumPlantasDominadas"
    ],
    "media_ColmoPodre": [
        "planta1ColmoPodre",
        "planta2ColmoPodre",
        "planta3ColmoPodre",
        "planta4ColmoPodre",
        "planta5ColmoPodre"
    ],
    "media_NumFileiras": [
        "planta1NumFileiras",
        "planta2NumFileiras",
        "planta3NumFileiras",
        "planta4NumFileiras",
        "planta5NumFileiras"
    ],
    "media_NumGraosPorFileira": [
        "planta1NumGraosPorFileira",
        "planta2NumGraosPorFileira",
        "planta3NumGraosPorFileira",
        "planta4NumGraosPorFileira",
        "planta5NumGraosPorFileira"
    ],
    "media_PMG": [
        "planta1PesoMilGraos",
        "planta2PesoMilGraos",
        "planta3PesoMilGraos",
        "planta4PesoMilGraos",
        "planta5PesoMilGraos"
    ],
    "media_umd_PMG": [
        "planta1UmidadeAmostraMilGraos",
        "planta2UmidadeAmostraMilGraos",
        "planta3UmidadeAmostraMilGraos",
        "planta4UmidadeAmostraMilGraos",
        "planta5UmidadeAmostraMilGraos"
    ],
    "media_ALT": [
        "planta1AlturaPlanta",
        "planta2AlturaPlanta",
        "planta3AlturaPlanta",
        "planta4AlturaPlanta",
        "planta5AlturaPlanta"
    ],
    "media_AIE": [
        "planta1AlturaEspiga",
        "planta2AlturaEspiga",
        "planta3AlturaEspiga",
        "planta4AlturaEspiga",
        "planta5AlturaEspiga"
    ]
}

if df_final is not None:
    for nome_media, colunas in colunas_medias.items():
        st.subheader(f"{nome_media}")
        st.write(f"Colunas envolvidas: {colunas}")
        # Mostra as primeiras linhas das colunas envolvidas
        if all(col in df_final.columns for col in colunas):
            st.dataframe(df_final[colunas].head(50))
        else:
            st.warning("Alguma coluna não encontrada no DataFrame.")
        # Mostra a coluna de média resultante
        if nome_media in df_final.columns:
            st.write(f"Coluna de média '{nome_media}':")
            st.dataframe(df_final[[nome_media]].head(50))
        else:
            st.warning(
                f"Coluna de média '{nome_media}' não encontrada no DataFrame.")

st.divider()
st.header("Debug do Cálculo de PMG Corrigido para Umidade Padrão (corr_PMG)")

if df_final is not None:
    colunas_corr_pmg = ["media_PMG", "media_umd_PMG", "corr_PMG"]
    st.write(f"Valor de umidade padrão utilizado: 13.5%")
    colunas_existentes = [
        col for col in colunas_corr_pmg if col in df_final.columns]
    if colunas_existentes:
        st.write("Colunas envolvidas e resultado:")
        st.dataframe(df_final[colunas_existentes].head(50))
    else:
        st.warning(
            "Colunas necessárias para o cálculo de corr_PMG não encontradas no DataFrame.")

st.divider()
st.header("Debug do Cálculo da Área da Parcela (area_parcela_m2)")

if df_final is not None:
    colunas_area = ["numeroLinhas", "comprimentoLinha",
                    "espacamento", "area_parcela_m2"]
    colunas_existentes = [
        col for col in colunas_area if col in df_final.columns]
    if all(col in df_final.columns for col in ["numeroLinhas", "comprimentoLinha", "espacamento"]):
        st.write("Colunas envolvidas:")
        st.dataframe(
            df_final[["numeroLinhas", "comprimentoLinha", "espacamento"]].head(50))
        # Exibe a condição booleana usada no cálculo
        cond = (
            df_final["numeroLinhas"].notnull() &
            df_final["comprimentoLinha"].notnull() &
            df_final["espacamento"].notnull() &
            (df_final["numeroLinhas"] > 0) &
            (df_final["comprimentoLinha"] > 0) &
            (df_final["espacamento"] > 0)
        )
        st.write("Condição booleana (True = linha válida para cálculo):")
        st.dataframe(cond.head(50))
        if "area_parcela_m2" in df_final.columns:
            st.write("Coluna de resultado 'area_parcela_m2':")
            st.dataframe(df_final[["area_parcela_m2"]].head(50))
        else:
            st.warning("Coluna 'area_parcela_m2' não encontrada no DataFrame.")
    else:
        st.warning(
            "Colunas necessárias para o cálculo da área da parcela não encontradas no DataFrame.")

st.divider()
st.header("Debug do Cálculo da Produtividade (prod_kg_ha)")

if df_final is not None:
    colunas_prod = ["pesoParcela", "area_parcela_m2", "prod_kg_ha"]
    if all(col in df_final.columns for col in ["pesoParcela", "area_parcela_m2"]):
        st.write("Colunas envolvidas:")
        st.dataframe(df_final[["pesoParcela", "area_parcela_m2"]].head(50))
        # Exibe a condição booleana usada no cálculo
        cond = (
            df_final["pesoParcela"].notnull() &
            df_final["area_parcela_m2"].notnull() &
            (df_final["pesoParcela"] > 0) &
            (df_final["area_parcela_m2"] > 0)
        )
        st.write("Condição booleana (True = linha válida para cálculo):")
        st.dataframe(cond.head(50))
        if "prod_kg_ha" in df_final.columns:
            st.write("Coluna de resultado 'prod_kg_ha':")
            st.dataframe(df_final[["prod_kg_ha"]].head(50))
        else:
            st.warning("Coluna 'prod_kg_ha' não encontrada no DataFrame.")
    else:
        st.warning(
            "Colunas necessárias para o cálculo da produtividade não encontradas no DataFrame.")

st.divider()
st.header(
    "Debug do Cálculo da Produtividade Corrigida para Umidade Padrão (prod_kg_ha_corr)")

if df_final is not None:
    colunas_corr = ["prod_kg_ha", "humidade", "prod_kg_ha_corr"]
    if all(col in df_final.columns for col in ["prod_kg_ha", "humidade"]):
        st.write("Colunas envolvidas:")
        st.dataframe(df_final[["prod_kg_ha", "humidade"]].head(50))
        cond = (
            df_final["prod_kg_ha"].notnull() &
            df_final["humidade"].notnull() &
            (df_final["prod_kg_ha"] > 0) &
            (df_final["humidade"] > 0)
        )
        st.write("Condição booleana (True = linha válida para cálculo):")
        st.dataframe(cond.head(50))
        if "prod_kg_ha_corr" in df_final.columns:
            st.write("Coluna de resultado 'prod_kg_ha_corr':")
            st.dataframe(df_final[["prod_kg_ha_corr"]].head(50))
        else:
            st.warning("Coluna 'prod_kg_ha_corr' não encontrada no DataFrame.")
    else:
        st.warning(
            "Colunas necessárias para o cálculo da produtividade corrigida não encontradas no DataFrame.")

st.divider()
st.header("Debug do Cálculo da Produtividade Corrigida em Sacas/ha (prod_sc_ha_corr)")

if df_final is not None:
    if "prod_kg_ha_corr" in df_final.columns:
        cond = (
            df_final["prod_kg_ha_corr"].notnull() &
            (df_final["prod_kg_ha_corr"] > 0)
        )
        st.write("Coluna envolvida: 'prod_kg_ha_corr'")
        st.dataframe(df_final[["prod_kg_ha_corr"]].head(50))
        st.write("Condição booleana (True = linha válida para cálculo):")
        st.dataframe(cond.head(50))
        if "prod_sc_ha_corr" in df_final.columns:
            st.write("Coluna de resultado 'prod_sc_ha_corr':")
            st.dataframe(df_final[["prod_sc_ha_corr"]].head(50))
        else:
            st.warning("Coluna 'prod_sc_ha_corr' não encontrada no DataFrame.")
    else:
        st.warning("Coluna 'prod_kg_ha_corr' não encontrada no DataFrame.")

st.divider()
st.header("Debug do Cálculo do Número de Plantas por Hectare (numPlantas_ha)")

if df_final is not None:
    if all(col in df_final.columns for col in ["media_NumPlantas10metros", "espacamento"]):
        st.write("Colunas envolvidas:")
        st.dataframe(
            df_final[["media_NumPlantas10metros", "espacamento"]].head(50))
        cond = (
            df_final["media_NumPlantas10metros"].notnull() &
            df_final["espacamento"].notnull() &
            (df_final["media_NumPlantas10metros"] > 0) &
            (df_final["espacamento"] > 0)
        )
        st.write("Condição booleana (True = linha válida para cálculo):")
        st.dataframe(cond.head(50))
        if "numPlantas_ha" in df_final.columns:
            st.write("Coluna de resultado 'numPlantas_ha':")
            st.dataframe(df_final[["numPlantas_ha"]].head(50))
        else:
            st.warning("Coluna 'numPlantas_ha' não encontrada no DataFrame.")
    else:
        st.warning(
            "Colunas necessárias para o cálculo de numPlantas_ha não encontradas no DataFrame.")


st.divider()
st.header("Debug do Percentual de Plantas Acamadas (perc_Acamadas)")

if df_final is not None:
    if all(col in df_final.columns for col in ["media_NumPlantasAcamadas", "media_NumPlantas10metros"]):
        st.write("Colunas envolvidas:")
        st.dataframe(df_final[["media_NumPlantasAcamadas",
                     "media_NumPlantas10metros"]].head(50))
        cond = (
            df_final["media_NumPlantasAcamadas"].notnull() &
            df_final["media_NumPlantas10metros"].notnull() &
            (df_final["media_NumPlantas10metros"] > 0)
        )
        st.write("Condição booleana (True = linha válida para cálculo):")
        st.dataframe(cond.head(50))
        if "perc_Acamadas" in df_final.columns:
            st.write("Coluna de resultado 'perc_Acamadas':")
            st.dataframe(df_final[["perc_Acamadas"]].head(50))
        else:
            st.warning("Coluna 'perc_Acamadas' não encontrada no DataFrame.")
    else:
        st.warning(
            "Colunas necessárias para o cálculo do percentual de acamadas não encontradas no DataFrame.")

st.divider()
st.header("Debug do Percentual de Plantas Quebradas (perc_Quebradas)")

if df_final is not None:
    if all(col in df_final.columns for col in ["media_NumPlantasQuebradas", "media_NumPlantas10metros"]):
        st.write("Colunas envolvidas:")
        st.dataframe(
            df_final[["media_NumPlantasQuebradas", "media_NumPlantas10metros"]].head(50))
        cond = (
            df_final["media_NumPlantasQuebradas"].notnull() &
            df_final["media_NumPlantas10metros"].notnull() &
            (df_final["media_NumPlantas10metros"] > 0)
        )
        st.write("Condição booleana (True = linha válida para cálculo):")
        st.dataframe(cond.head(50))
        if "perc_Quebradas" in df_final.columns:
            st.write("Coluna de resultado 'perc_Quebradas':")
            st.dataframe(df_final[["perc_Quebradas"]].head(50))
        else:
            st.warning("Coluna 'perc_Quebradas' não encontrada no DataFrame.")
    else:
        st.warning(
            "Colunas necessárias para o cálculo do percentual de quebradas não encontradas no DataFrame.")

st.divider()
st.header("Debug do Percentual de Plantas Dominadas (perc_Dominadas)")

if df_final is not None:
    if all(col in df_final.columns for col in ["media_NumPlantasDominadas", "media_NumPlantas10metros"]):
        st.write("Colunas envolvidas:")
        st.dataframe(
            df_final[["media_NumPlantasDominadas", "media_NumPlantas10metros"]].head(50))
        cond = (
            df_final["media_NumPlantasDominadas"].notnull() &
            df_final["media_NumPlantas10metros"].notnull() &
            (df_final["media_NumPlantas10metros"] > 0)
        )
        st.write("Condição booleana (True = linha válida para cálculo):")
        st.dataframe(cond.head(50))
        if "perc_Dominadas" in df_final.columns:
            st.write("Coluna de resultado 'perc_Dominadas':")
            st.dataframe(df_final[["perc_Dominadas"]].head(50))
        else:
            st.warning("Coluna 'perc_Dominadas' não encontrada no DataFrame.")
    else:
        st.warning(
            "Colunas necessárias para o cálculo do percentual de dominadas não encontradas no DataFrame.")

st.divider()
st.header("Debug do Percentual Total (perc_Total)")

if df_final is not None:
    cols_perc = ["perc_Acamadas", "perc_Quebradas",
                 "perc_Dominadas", "perc_Total"]
    cols_exist = [col for col in cols_perc if col in df_final.columns]
    if len(cols_exist) == 4:
        st.write("Colunas envolvidas e resultado:")
        st.dataframe(df_final[cols_perc].head(50))
    else:
        st.warning(
            "Alguma das colunas necessárias para o cálculo de perc_Total não foi encontrada no DataFrame.")

st.divider()
st.header("Debug da Padronização de Altura para Metros (media_ALT_m, media_AIE_m)")

if df_final is not None:
    alt_cols = ["media_ALT", "media_ALT_m"]
    aie_cols = ["media_AIE", "media_AIE_m"]
    if all(col in df_final.columns for col in alt_cols):
        st.write("Colunas envolvidas na padronização de ALT:")
        st.dataframe(df_final[alt_cols].head(50))
    else:
        st.warning("Colunas de ALT não encontradas no DataFrame.")
    if all(col in df_final.columns for col in aie_cols):
        st.write("Colunas envolvidas na padronização de AIE:")
        st.dataframe(df_final[aie_cols].head(50))
    else:
        st.warning("Colunas de AIE não encontradas no DataFrame.")

st.divider()
st.header("Debug da Conversão de Datas e Diferença de Dias")

if df_final is not None:
    # Conversão de datas
    data_cols = ["dataPlantioMilho", "dataColheitaMilho", "dataFlorescimentoFeminina", "dataFlorescimentoMasculina",
                 "plantio", "colheita", "dataFlorFem", "dataFlorMasc"]
    cols_exist = [col for col in data_cols if col in df_final.columns]
    if cols_exist:
        st.write("Colunas de datas (originais e convertidas):")
        st.dataframe(df_final[cols_exist].head(50))
    else:
        st.warning("Colunas de datas não encontradas no DataFrame.")
    # Diferença de datas
    diff_cols = [
        ("ciclo_dias", ["colheita", "plantio"]),
        ("flor_fem_dias", ["dataFlorFem", "plantio"]),
        ("flor_masc_dias", ["dataFlorMasc", "plantio"])
    ]
    for diff_col, base_cols in diff_cols:
        st.subheader(f"Cálculo de {diff_col}")
        if all(col in df_final.columns for col in [diff_col] + base_cols):
            st.write(
                f"Colunas envolvidas: {base_cols} e resultado: {diff_col}")
            st.dataframe(df_final[base_cols + [diff_col]].head(50))
        else:
            st.warning(
                f"Colunas necessárias para o cálculo de {diff_col} não encontradas no DataFrame.")
