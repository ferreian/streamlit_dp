import streamlit as st
import pandas as pd
import numpy as np
import io
from st_aggrid import AgGrid, GridOptionsBuilder


st.title("📊 Resultados AV1 Milho")
st.markdown(
    "Nesta página, você pode visualizar os resultados da AV1 dos ensaios de DP milho."
)

# Carregar e exibir o DataFrame do session_state
if "merged_dataframes" in st.session_state:
    df = st.session_state["merged_dataframes"].get(
        "av4TratamentoMilho_Avaliacao_Fazenda_Users_Cidade_Estado"
    )
    if df is not None:
        df_visualizacao = df  # Aqui você pode aplicar filtros se quiser

        # CSS customizado para cabeçalho e células
        custom_css = {
            ".ag-header-cell-label": {
                "color": "black !important",
                "font-weight": "bold !important"
            },
            ".ag-cell": {
                "color": "black !important",
                "font-weight": "bold !important"
            }
        }

        # Visualização interativa com AgGrid
        gb = GridOptionsBuilder.from_dataframe(df_visualizacao)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_side_bar()
        gb.configure_default_column(
            groupable=True, value=True, enableRowGroup=True, editable=False)
        grid_options = gb.build()

        AgGrid(
            df_visualizacao,
            gridOptions=grid_options,
            enable_enterprise_modules=False,
            fit_columns_on_grid_load=True,
            theme="streamlit",
            height=500,
            width='100%',
            custom_css=custom_css
        )

        # Botão para exportar em Excel apenas as colunas selecionadas
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:  # type: ignore
            df_visualizacao.to_excel(
                writer, index=False, sheet_name="AV1_Milho")
        output.seek(0)
        st.download_button(
            label="📥 Baixar Excel",
            data=output.getvalue(),
            file_name="av1TratamentoMilho_Selecionado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning(
            "DataFrame 'av1TratamentoMilho_Avaliacao_Fazenda_Users_Cidade_Estado' não encontrado no session_state.")
else:
    st.warning("Os dados ainda não foram carregados na sessão.")
