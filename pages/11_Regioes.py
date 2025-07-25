import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Mapa Municípios GeoJSON - Macrorregiões Milho",
    page_icon="🌽",
    layout="wide"
)

# Cache para carregar dados


@st.cache_data
def load_data():
    """Carrega os dados do arquivo Excel"""
    try:
        df = pd.read_excel('datasets/base_municipios_regioes_soja_milho.xlsx')
        df = df.dropna(subset=['macroRegiaoMilho'])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        return None


@st.cache_data
def load_geojson_file(file_path):
    """Carrega arquivo GeoJSON local"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar GeoJSON: {e}")
        return None


def get_color_map():
    """Cores das macrorregiões"""
    return {
        'Tropical Baixa': '#8B4B9C',           # Roxo
        'Tropical de Transição': '#FF8C00',    # Laranja
        'Tropical Alta': '#228B22',            # Verde
        'Sub Tropical Alta': '#1E90FF',        # Azul
        'Sub Tropical Baixa': '#4169E1'        # Azul royal
    }


def create_geojson_from_data(df):
    """Cria um GeoJSON simplificado usando coordenadas dos municípios"""

    features = []

    for _, row in df.iterrows():
        # Criar um polígono maior ao redor de cada coordenada
        lat, lon = row['latitude'], row['longitude']
        offset = 0.3  # ~30km aproximadamente, para visualização clara

        coordinates = [[
            [lon - offset, lat - offset],
            [lon + offset, lat - offset],
            [lon + offset, lat + offset],
            [lon - offset, lat + offset],
            [lon - offset, lat - offset]
        ]]

        feature = {
            "type": "Feature",
            "properties": {
                "GEOCODE": str(row['ibge']),
                "NAME": row['cidade'],
                "STATE": row['estado'],
                "MACRO_REGIAO": row['macroRegiaoMilho']
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": coordinates
            }
        }

        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    return geojson


def main():
    st.title("🌽 Mapa das Macrorregiões do Milho")
    st.markdown("### Usando GeoJSON para delimitar municípios")
    st.markdown("---")

    # Carregar dados
    df = load_data()
    if df is None:
        st.stop()
    st.sidebar.header("🗺️ Configuração do GeoJSON")
    opcao_geojson = st.sidebar.selectbox(
        "Escolha a fonte do GeoJSON:",
        [
            "GeoJSON oficial dos municípios (recomendado)",
            "Gerar automaticamente (aproximado)",
            "Upload de arquivo GeoJSON",
            "URL online",
            "Arquivo local no servidor"
        ]
    )
    geojson = None
    if opcao_geojson == "GeoJSON oficial dos municípios (recomendado)":
        geojson_path = "datasets/municipios_br.json"
        if Path(geojson_path).exists():
            geojson = load_geojson_file(geojson_path)
            st.sidebar.success("✅ GeoJSON oficial carregado!")
        else:
            st.sidebar.error(f"GeoJSON não encontrado em {geojson_path}")
    elif opcao_geojson == "Upload de arquivo GeoJSON":
        uploaded_file = st.sidebar.file_uploader(
            "Faça upload do arquivo GeoJSON dos municípios:",
            type=['json', 'geojson']
        )
        if uploaded_file is not None:
            try:
                geojson = json.load(uploaded_file)
                st.sidebar.success("✅ GeoJSON carregado com sucesso!")
            except Exception as e:
                st.sidebar.error(f"Erro ao carregar arquivo: {e}")
    elif opcao_geojson == "URL online":
        url = st.sidebar.text_input(
            "URL do GeoJSON:",
            placeholder="https://exemplo.com/municipios.geojson"
        )
        if url:
            try:
                import requests
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    geojson = response.json()
                    st.sidebar.success("✅ GeoJSON baixado com sucesso!")
                else:
                    st.sidebar.error("❌ Erro ao baixar GeoJSON")
            except Exception as e:
                st.sidebar.error(f"Erro: {e}")
    elif opcao_geojson == "Arquivo local no servidor":
        arquivo_local = st.sidebar.text_input(
            "Caminho do arquivo GeoJSON:",
            value="datasets/municipios_br.json"
        )
        if arquivo_local and Path(arquivo_local).exists():
            geojson = load_geojson_file(arquivo_local)
            if geojson:
                st.sidebar.success("✅ Arquivo local carregado!")
    elif opcao_geojson == "Gerar automaticamente (aproximado)":
        st.sidebar.info(
            "💡 Gerando polígonos aproximados baseados nas coordenadas")
        geojson = create_geojson_from_data(df)
        st.sidebar.success("✅ GeoJSON gerado automaticamente!")
    st.sidebar.header("🎛️ Filtros")
    macro_selecionadas = st.sidebar.multiselect(
        "Macrorregiões:",
        df['macroRegiaoMilho'].unique(),
        default=df['macroRegiaoMilho'].unique()
    )
    estado_selecionado = st.sidebar.selectbox(
        "Estado:",
        ['Todos'] + sorted(df['estado'].unique().tolist())
    )
    df_filtered = df[df['macroRegiaoMilho'].isin(macro_selecionadas)]
    if estado_selecionado != 'Todos':
        df_filtered = df_filtered[df_filtered['estado'] == estado_selecionado]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Municípios", f"{len(df_filtered):,}")
    with col2:
        st.metric("Estados", df_filtered['estado'].nunique())
    with col3:
        st.metric("Macrorregiões", df_filtered['macroRegiaoMilho'].nunique())
    with col4:
        pct = len(df_filtered) / len(df) * 100
        st.metric("% do Total", f"{pct:.1f}%")
    if geojson:
        try:
            if opcao_geojson == "GeoJSON oficial dos municípios (recomendado)" or opcao_geojson == "Arquivo local no servidor":
                df_filtered['ibge_str'] = df_filtered['ibge'].astype(str)
                featureidkey = 'properties.cod_mun'
                locations = 'ibge_str'
            else:
                featureidkey = 'properties.GEOCODE'
                locations = 'ibge_str' if 'ibge_str' in df_filtered.columns else 'ibge'
            fig = px.choropleth_mapbox(
                df_filtered,
                geojson=geojson,
                locations=locations,
                featureidkey=featureidkey,
                color='macroRegiaoMilho',
                color_discrete_map=get_color_map(),
                mapbox_style="carto-positron",
                zoom=3.5,
                center={"lat": -14.2, "lon": -53.0},
                opacity=0.8,
                title="Macrorregiões do Milho - Municípios Brasileiros",
                labels={'macroRegiaoMilho': 'Macrorregião'},
                hover_data={
                    'cidade': True,
                    'estado': True,
                    'macroRegiaoMilho': True,
                    'ibge': True
                }
            )
            fig.update_layout(height=700)
            st.plotly_chart(fig, use_container_width=True)
            st.success(
                "🎯 **Mapa com limites reais dos municípios criado com sucesso!**")
        except Exception as e:
            st.error(f"Erro ao criar mapa: {e}")
            st.info("Tentando mapa alternativo...")
            colors = get_color_map()
            fig = px.scatter_mapbox(
                df_filtered,
                lat="latitude",
                lon="longitude",
                color="macroRegiaoMilho",
                color_discrete_map=colors,
                zoom=3.5,
                center={"lat": -14.2, "lon": -53.0},
                mapbox_style="carto-positron",
                title="Mapa de Pontos - Macrorregiões do Milho",
                hover_data=['cidade', 'estado']
            )
            fig.update_layout(height=700)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(
            "⚠️ Configure um GeoJSON na barra lateral para ver o mapa com delimitações municipais.")
        colors = get_color_map()
        fig = px.scatter_mapbox(
            df_filtered,
            lat="latitude",
            lon="longitude",
            color="macroRegiaoMilho",
            color_discrete_map=colors,
            zoom=3.5,
            center={"lat": -14.2, "lon": -53.0},
            mapbox_style="carto-positron",
            title="Mapa de Pontos - Macrorregiões do Milho",
            hover_data=['cidade', 'estado']
        )
        fig.update_layout(height=700)
        st.plotly_chart(fig, use_container_width=True)


main()
