import pandas as pd
import numpy as np
from datetime import datetime

# =========================
# Função utilitária para gerar o DataFrame tratado
# =========================


def gerar_df_avTratamentoMilho(session_state):
    # Carrega os DataFrames do session_state
    df_av2TratamentoMilho = session_state.get("df_av2TratamentoMilho")
    df_av3TratamentoMilho = session_state.get("df_av3TratamentoMilho")
    df_av4TratamentoMilho = session_state.get("df_av4TratamentoMilho")
    df_fazenda = session_state.get("df_fazenda")
    df_cidade = session_state.get("df_cidade")
    df_estado = session_state.get("df_estado")
    df_avaliacao = session_state.get("df_avaliacao")
    df_base_municipios_regioes_soja_milho = session_state.get(
        "df_base_municipios_regioes_soja_milho")
    df_users = session_state.get("df_users")

    # Filtra apenas linhas onde tipoTeste == 'Faixa'
    def filtrar_faixa(df):
        if df is not None and 'tipoTeste' in df.columns:
            return df[df['tipoTeste'] == 'Faixa']
        return pd.DataFrame()

    df_av2TratamentoMilho_faixa = filtrar_faixa(df_av2TratamentoMilho)
    df_av3TratamentoMilho_faixa = filtrar_faixa(df_av3TratamentoMilho)
    df_av4TratamentoMilho_faixa = filtrar_faixa(df_av4TratamentoMilho)

    # Reduz o df_avaliacao para as colunas necessárias para merge
    df_avaliacao_reduzido = None
    if df_avaliacao is not None and not df_avaliacao.empty:
        df_avaliacao_reduzido = df_avaliacao[["uuid", "fazendaRef"]].rename(
            columns={"uuid": "avaliacaoRef"})

    # Função para merge entre tratamento e avaliação
    def merge_tratamento(df_tratamento, df_avaliacao_reduzido):
        if df_tratamento is not None and not df_tratamento.empty and df_avaliacao_reduzido is not None:
            return df_tratamento.merge(
                df_avaliacao_reduzido,
                on="avaliacaoRef",
                how="left"
            )
        return pd.DataFrame()

    # Realiza os merges iniciais
    df_av2TratamentoMilho_merged = merge_tratamento(
        df_av2TratamentoMilho_faixa, df_avaliacao_reduzido)
    df_av3TratamentoMilho_merged = merge_tratamento(
        df_av3TratamentoMilho_faixa, df_avaliacao_reduzido)
    df_av4TratamentoMilho_merged = merge_tratamento(
        df_av4TratamentoMilho_faixa, df_avaliacao_reduzido)

    # Cria coluna 'key' para identificar tratamentos únicos
    def criar_coluna_key(df):
        if not df.empty:
            df["key"] = (
                df["fazendaRef"].astype(str) + "_" +
                df["nome"].astype(str) + "_" +
                df["indexTratamento"].astype(str)
            )
        return df

    # Remove colunas indesejadas
    def remover_colunas(df, colunas):
        if not df.empty:
            return df.drop(columns=[c for c in colunas if c in df.columns])
        return df

    # Aplica a criação da coluna 'key' nos DataFrames de tratamento
    if not df_av4TratamentoMilho_merged.empty:
        df_av4TratamentoMilho_merged = criar_coluna_key(
            df_av4TratamentoMilho_merged)
    if not df_av3TratamentoMilho_merged.empty:
        df_av3TratamentoMilho_merged = criar_coluna_key(
            df_av3TratamentoMilho_merged)
    if not df_av2TratamentoMilho_merged.empty:
        df_av2TratamentoMilho_merged = criar_coluna_key(
            df_av2TratamentoMilho_merged)

    # Remove colunas que não serão usadas
    colunas_remover = [
        "uuid", "dataSync", "acao", "cultivar", "tipoTeste", "nome",
        "populacao", "indexTratamento", "avaliacaoRef", "idBaseRef", "fazendaRef"
    ]
    df_av2TratamentoMilho_merged = remover_colunas(
        df_av2TratamentoMilho_merged, colunas_remover)
    df_av3TratamentoMilho_merged = remover_colunas(
        df_av3TratamentoMilho_merged, colunas_remover)

    # Realiza merges entre os DataFrames de tratamento
    df_avTratamentoMilho = pd.DataFrame()
    if not df_av4TratamentoMilho_merged.empty and not df_av3TratamentoMilho_merged.empty:
        df_avTratamentoMilho = df_av4TratamentoMilho_merged.merge(
            df_av3TratamentoMilho_merged,
            on="key",
            how="left",
            suffixes=("_av4", "_av3")
        )
    if not df_avTratamentoMilho.empty and not df_av2TratamentoMilho_merged.empty:
        df_avTratamentoMilho = df_avTratamentoMilho.merge(
            df_av2TratamentoMilho_merged,
            on="key",
            how="left",
            suffixes=("", "_av2")
        )

    # Remove colunas desnecessárias do DataFrame de fazenda
    colunas_remover_fazenda = [
        "dataSync", "acao", "isMilho", "isSoja", "latitude", "longitude", "altitude",
        "safra", "criadoEm", "modificadoEm", "epoca", "rcResponsavel", "dataPlantio",
        "dataColheita", "hide", "firebase"
    ]
    if df_fazenda is not None and not df_fazenda.empty:
        df_fazenda = df_fazenda.drop(
            columns=[c for c in colunas_remover_fazenda if c in df_fazenda.columns])
    # Renomeia uuid para fazendaRef
    if df_fazenda is not None and not df_fazenda.empty and 'uuid' in df_fazenda.columns:
        df_fazenda = df_fazenda.rename(columns={'uuid': 'fazendaRef'})
    # Merge com fazenda
    if not df_avTratamentoMilho.empty and df_fazenda is not None and not df_fazenda.empty:
        df_avTratamentoMilho = df_avTratamentoMilho.merge(
            df_fazenda,
            on='fazendaRef',
            how='left',
            suffixes=('', '_fazenda')
        )

    # Remove colunas desnecessárias do DataFrame de cidade
    colunas_remover_cidade = ["dataSync", "acao", "codigoCidade", "firebase"]
    if df_cidade is not None and not df_cidade.empty:
        df_cidade = df_cidade.drop(
            columns=[c for c in colunas_remover_cidade if c in df_cidade.columns])
    # Renomeia uuid para cidadeRef
    if df_cidade is not None and not df_cidade.empty and 'uuid' in df_cidade.columns:
        df_cidade = df_cidade.rename(columns={'uuid': 'cidadeRef'})
    # Merge com cidade
    if not df_avTratamentoMilho.empty and df_cidade is not None and not df_cidade.empty:
        df_avTratamentoMilho = df_avTratamentoMilho.merge(
            df_cidade,
            on='cidadeRef',
            how='left',
            suffixes=('', '_cidade')
        )
    # Cria coluna cidade_siglaEstado para facilitar merges posteriores
    if not df_avTratamentoMilho.empty and 'nomeCidade' in df_avTratamentoMilho.columns and 'siglaEstado' in df_avTratamentoMilho.columns:
        df_avTratamentoMilho['cidade_siglaEstado'] = (
            df_avTratamentoMilho['nomeCidade'].astype(
                str) + '_' + df_avTratamentoMilho['siglaEstado'].astype(str)
        )

    # Remove colunas desnecessárias do DataFrame de estado
    colunas_remover_estado = ["dataSync", "acao", "paisRef", "firebase"]
    if df_estado is not None and not df_estado.empty:
        df_estado = df_estado.drop(
            columns=[c for c in colunas_remover_estado if c in df_estado.columns])
    # Renomeia colunas para facilitar merge
    df_estado_renomeado = df_estado
    if df_estado_renomeado is not None and not df_estado_renomeado.empty:
        df_estado_renomeado = df_estado_renomeado.rename(columns={
            'uuid': 'estadoRef',
            'codigoEstado': 'estado',
            'nomeEstado': 'siglaEstado'
        })
    # Merge com estado
    if not df_avTratamentoMilho.empty and df_estado_renomeado is not None and not df_estado_renomeado.empty:
        df_avTratamentoMilho = df_avTratamentoMilho.merge(
            df_estado_renomeado,
            on='estadoRef',
            how='left',
            suffixes=('', '_estado')
        )
    # Atualiza cidade_siglaEstado após merge
    if not df_avTratamentoMilho.empty and 'nomeCidade' in df_avTratamentoMilho.columns and 'siglaEstado' in df_avTratamentoMilho.columns:
        df_avTratamentoMilho['cidade_siglaEstado'] = (
            df_avTratamentoMilho['nomeCidade'].astype(
                str) + '_' + df_avTratamentoMilho['siglaEstado'].astype(str)
        )

    # Remove colunas desnecessárias do DataFrame de municípios
    colunas_remover_base_municipios = [
        'ibge', 'macroSoja', 'recSoja', 'regiaoEconomica', 'mesoRegiaoSoja', 'microRegiaoSoja'
    ]
    if df_base_municipios_regioes_soja_milho is not None and not df_base_municipios_regioes_soja_milho.empty:
        df_base_municipios_regioes_soja_milho = df_base_municipios_regioes_soja_milho.drop(
            columns=[
                c for c in colunas_remover_base_municipios if c in df_base_municipios_regioes_soja_milho.columns]
        )
    # Merge com base de municípios
    if not df_avTratamentoMilho.empty and df_base_municipios_regioes_soja_milho is not None and not df_base_municipios_regioes_soja_milho.empty:
        df_avTratamentoMilho = df_avTratamentoMilho.merge(
            df_base_municipios_regioes_soja_milho,
            on='cidade_siglaEstado',
            how='left',
            suffixes=('', '_base_municipios')
        )

    # Prepara df_users para merge
    if isinstance(df_users, pd.DataFrame) and not df_users.empty:
        cols = [col for col in ['uuid', 'displayName']
                if col in df_users.columns]
        if cols:
            df_users = df_users.loc[:, cols]
            if 'uuid' in df_users.columns:
                df_users = df_users.rename(
                    columns={'uuid': 'dtcResponsavelRef'})
    # Merge com usuários
    if not df_avTratamentoMilho.empty and isinstance(df_users, pd.DataFrame) and not df_users.empty:
        df_avTratamentoMilho = df_avTratamentoMilho.merge(
            df_users,
            on='dtcResponsavelRef',
            how='left',
            suffixes=('', '_user')
        )

    # Colunas calculadas

    # Dicionário de colunas para cálculo de médias
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
    # Calcula as médias para cada grupo de colunas
    for nome_media, colunas in colunas_medias.items():
        if all(col in df_avTratamentoMilho.columns for col in colunas):
            temp = df_avTratamentoMilho[colunas].replace(0, np.nan)
            df_avTratamentoMilho[nome_media] = temp.mean(axis=1, skipna=True)

    # Cálculo de colunas agronômicas e percentuais
    umidade_padrao = 13.5
    # Corrige PMG para umidade padrão
    if "media_PMG" in df_avTratamentoMilho.columns and "media_umd_PMG" in df_avTratamentoMilho.columns:
        df_avTratamentoMilho["corr_PMG"] = df_avTratamentoMilho.apply(
            lambda row: (
                row["media_PMG"] * (100 - row["media_umd_PMG"]
                                    ) / (100 - umidade_padrao)
                if pd.notnull(row["media_PMG"]) and pd.notnull(row["media_umd_PMG"]) and row["media_PMG"] != 0 and row["media_umd_PMG"] != 0
                else np.nan
            ),
            axis=1
        )
    # Área da parcela
    if all(col in df_avTratamentoMilho.columns for col in ["numeroLinhas", "comprimentoLinha", "espacamento"]):
        cond = (
            df_avTratamentoMilho["numeroLinhas"].notnull() &
            df_avTratamentoMilho["comprimentoLinha"].notnull() &
            df_avTratamentoMilho["espacamento"].notnull() &
            (df_avTratamentoMilho["numeroLinhas"] > 0) &
            (df_avTratamentoMilho["comprimentoLinha"] > 0) &
            (df_avTratamentoMilho["espacamento"] > 0)
        )
        df_avTratamentoMilho["area_parcela_m2"] = np.where(
            cond,
            df_avTratamentoMilho["numeroLinhas"] *
            df_avTratamentoMilho["comprimentoLinha"] *
            df_avTratamentoMilho["espacamento"],
            np.nan
        )
    # Produtividade kg/ha
    if all(col in df_avTratamentoMilho.columns for col in ["pesoParcela", "area_parcela_m2"]):
        cond = (
            df_avTratamentoMilho["pesoParcela"].notnull() &
            df_avTratamentoMilho["area_parcela_m2"].notnull() &
            (df_avTratamentoMilho["pesoParcela"] > 0) &
            (df_avTratamentoMilho["area_parcela_m2"] > 0)
        )
        df_avTratamentoMilho["prod_kg_ha"] = np.where(
            cond,
            (df_avTratamentoMilho["pesoParcela"] /
             df_avTratamentoMilho["area_parcela_m2"]) * 10000,
            np.nan
        )
    # Produtividade corrigida para umidade padrão
    if all(col in df_avTratamentoMilho.columns for col in ["prod_kg_ha", "humidade"]):
        cond = (
            df_avTratamentoMilho["prod_kg_ha"].notnull() &
            df_avTratamentoMilho["humidade"].notnull() &
            (df_avTratamentoMilho["prod_kg_ha"] > 0) &
            (df_avTratamentoMilho["humidade"] > 0)
        )
        df_avTratamentoMilho["prod_kg_ha_corr"] = np.where(
            cond,
            df_avTratamentoMilho["prod_kg_ha"] *
            (100 - df_avTratamentoMilho["humidade"]) / (100 - umidade_padrao),
            np.nan
        )
    # Produtividade em sacas/ha corrigida
    if "prod_kg_ha_corr" in df_avTratamentoMilho.columns:
        cond = (
            df_avTratamentoMilho["prod_kg_ha_corr"].notnull() &
            (df_avTratamentoMilho["prod_kg_ha_corr"] > 0)
        )
        df_avTratamentoMilho["prod_sc_ha_corr"] = np.where(
            cond,
            df_avTratamentoMilho["prod_kg_ha_corr"] / 60,
            np.nan
        )

    # Cálculo de número de plantas por hectare

    if all(col in df_avTratamentoMilho.columns for col in ["media_NumPlantas10metros", "espacamento"]):
        cond = (
            df_avTratamentoMilho["media_NumPlantas10metros"].notnull() &
            df_avTratamentoMilho["espacamento"].notnull() &
            (df_avTratamentoMilho["media_NumPlantas10metros"] > 0) &
            (df_avTratamentoMilho["espacamento"] > 0)
        )
        df_avTratamentoMilho["numPlantas_ha"] = np.where(
            cond,
            df_avTratamentoMilho["media_NumPlantas10metros"] *
            1000 / df_avTratamentoMilho["espacamento"],
            np.nan
        )

    # Percentual de plantas acamadas
    if all(col in df_avTratamentoMilho.columns for col in ["media_NumPlantasAcamadas", "media_NumPlantas10metros"]):
        cond = (
            df_avTratamentoMilho["media_NumPlantasAcamadas"].notnull() &
            df_avTratamentoMilho["media_NumPlantas10metros"].notnull() &
            (df_avTratamentoMilho["media_NumPlantas10metros"] > 0)
        )
        df_avTratamentoMilho["perc_Acamadas"] = np.where(
            cond,
            (df_avTratamentoMilho["media_NumPlantasAcamadas"] /
             df_avTratamentoMilho["media_NumPlantas10metros"]) * 100,
            0
        )
    # Percentual de plantas quebradas
    if all(col in df_avTratamentoMilho.columns for col in ["media_NumPlantasQuebradas", "media_NumPlantas10metros"]):
        cond = (
            df_avTratamentoMilho["media_NumPlantasQuebradas"].notnull() &
            df_avTratamentoMilho["media_NumPlantas10metros"].notnull() &
            (df_avTratamentoMilho["media_NumPlantas10metros"] > 0)
        )
        df_avTratamentoMilho["perc_Quebradas"] = np.where(
            cond,
            (df_avTratamentoMilho["media_NumPlantasQuebradas"] /
             df_avTratamentoMilho["media_NumPlantas10metros"]) * 100,
            0
        )
    # Percentual de plantas dominadas
    if all(col in df_avTratamentoMilho.columns for col in ["media_NumPlantasDominadas", "media_NumPlantas10metros"]):
        cond = (
            df_avTratamentoMilho["media_NumPlantasDominadas"].notnull() &
            df_avTratamentoMilho["media_NumPlantas10metros"].notnull() &
            (df_avTratamentoMilho["media_NumPlantas10metros"] > 0)
        )
        df_avTratamentoMilho["perc_Dominadas"] = np.where(
            cond,
            (df_avTratamentoMilho["media_NumPlantasDominadas"] /
             df_avTratamentoMilho["media_NumPlantas10metros"]) * 100,
            0
        )

    # Percentual de plantas com colmo podre
    if all(col in df_avTratamentoMilho.columns for col in ["media_ColmoPodre", "media_NumPlantas10metros"]):
        cond = (
            df_avTratamentoMilho["media_ColmoPodre"].notnull() &
            df_avTratamentoMilho["media_NumPlantas10metros"].notnull() &
            (df_avTratamentoMilho["media_NumPlantas10metros"] > 0)
        )
        df_avTratamentoMilho["perc_ColmoPodre"] = np.where(
            cond,
            (df_avTratamentoMilho["media_ColmoPodre"] /
             df_avTratamentoMilho["media_NumPlantas10metros"]) * 100,
            0
        )

    # Percentual Total# Cálculo do percentual total (soma dos percentuais de acamadas, quebradas, dominadas e colmo podre)
    if all(col in df_avTratamentoMilho.columns for col in ["perc_Acamadas", "perc_Quebradas", "perc_Dominadas", "perc_ColmoPodre"]):
        df_avTratamentoMilho["perc_Total"] = (
            df_avTratamentoMilho["perc_Acamadas"].fillna(0) +
            df_avTratamentoMilho["perc_Quebradas"].fillna(0) +
            df_avTratamentoMilho["perc_Dominadas"].fillna(0) +
            df_avTratamentoMilho["perc_ColmoPodre"].fillna(0)
        )
    # Função para padronizar altura para metros

    def padronizar_altura_para_metros(valor):
        try:
            if pd.isnull(valor):
                return np.nan
            if isinstance(valor, str):
                valor = valor.replace(',', '.').strip()
            valor = float(valor)
            if valor > 10:
                return valor / 100
            return valor
        except Exception:
            return np.nan

    # Aplica padronização de altura para metros
    if "media_ALT" in df_avTratamentoMilho.columns:
        df_avTratamentoMilho["media_ALT_m"] = df_avTratamentoMilho["media_ALT"].apply(
            padronizar_altura_para_metros)
    if "media_AIE" in df_avTratamentoMilho.columns:
        df_avTratamentoMilho["media_AIE_m"] = df_avTratamentoMilho["media_AIE"].apply(
            padronizar_altura_para_metros)

    # Função para converter timestamp para data no formato brasileiro
    def timestamp_para_data_br(valor):
        try:
            if pd.notnull(valor) and valor != 0:
                return pd.to_datetime(valor, unit='s').strftime('%d/%m/%Y')
            else:
                return ""
        except Exception:
            return ""

    # Mapeamento de colunas de data para nomes amigáveis
    col_map = {
        "dataPlantioMilho": "plantio",
        "dataColheitaMilho": "colheita",
        "dataFlorescimentoFeminina": "dataFlorFem",
        "dataFlorescimentoMasculina": "dataFlorMasc"
    }
    # Aplica conversão de timestamp para data
    for col_orig, col_novo in col_map.items():
        if col_orig in df_avTratamentoMilho.columns:
            df_avTratamentoMilho[col_novo] = df_avTratamentoMilho[col_orig].apply(
                timestamp_para_data_br)

    # Função para calcular diferença de datas em dias
    def diff_dias(data_fim, data_ini):
        try:
            if pd.isnull(data_fim) or pd.isnull(data_ini) or data_fim == '' or data_ini == '':
                return np.nan
            d1 = datetime.strptime(str(data_fim), '%d/%m/%Y')
            d2 = datetime.strptime(str(data_ini), '%d/%m/%Y')
            return (d1 - d2).days
        except Exception:
            return np.nan

    # Calcula colunas de diferença de datas em dias
    if all(col in df_avTratamentoMilho.columns for col in ["colheita", "plantio"]):
        df_avTratamentoMilho["ciclo_dias"] = df_avTratamentoMilho.apply(
            lambda row: diff_dias(row["colheita"], row["plantio"]), axis=1)
    if all(col in df_avTratamentoMilho.columns for col in ["dataFlorFem", "plantio"]):
        df_avTratamentoMilho["flor_fem_dias"] = df_avTratamentoMilho.apply(
            lambda row: diff_dias(row["dataFlorFem"], row["plantio"]), axis=1)
    if all(col in df_avTratamentoMilho.columns for col in ["dataFlorMasc", "plantio"]):
        df_avTratamentoMilho["flor_masc_dias"] = df_avTratamentoMilho.apply(
            lambda row: diff_dias(row["dataFlorMasc"], row["plantio"]), axis=1)

    # Cálculo de número de plantas por hectare
    if all(col in df_avTratamentoMilho.columns for col in ["media_NumPlantas10metros", "espacamento"]):
        cond = (
            df_avTratamentoMilho["media_NumPlantas10metros"].notnull() &
            df_avTratamentoMilho["espacamento"].notnull() &
            (df_avTratamentoMilho["media_NumPlantas10metros"] > 0) &
            (df_avTratamentoMilho["espacamento"] > 0)
        )
        df_avTratamentoMilho["numPlantas_ha"] = np.where(
            cond,
            df_avTratamentoMilho["media_NumPlantas10metros"] *
            1000 / df_avTratamentoMilho["espacamento"],
            np.nan
        )

    # Remove usuário de teste específico do DataFrame final
    if "displayName" in df_avTratamentoMilho.columns:
        df_avTratamentoMilho = df_avTratamentoMilho[df_avTratamentoMilho["displayName"] != "raullanconi"]

    # Converte nomeFazenda e nomeProdutor para caixa alta, se existirem
    for col in ["nomeFazenda", "nomeProdutor"]:
        if col in df_avTratamentoMilho.columns:
            df_avTratamentoMilho[col] = pd.Series(
                df_avTratamentoMilho[col], index=df_avTratamentoMilho.index).astype(str).str.upper()

    # Retorna o DataFrame final já tratado e os intermediários
    return df_avTratamentoMilho, df_av2TratamentoMilho_merged, df_av3TratamentoMilho_merged, df_av4TratamentoMilho_merged
