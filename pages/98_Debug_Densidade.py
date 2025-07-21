import streamlit as st
import pandas as pd
import numpy as np

st.title("🛠️ Debug de Densidade - DataFrames e Variáveis")

# DataFrame final do processamento de densidade
st.header("DataFrame Final (Tratado) - Densidade")
df_final = st.session_state.get("df_avTratamentoMilhoDensidade")
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
        label="⬇️ Baixar Excel do DataFrame Final (Densidade)",
        data=buffer,
        file_name="df_avTratamentoMilhoDensidade_debug.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("DataFrame final de densidade não carregado.")

# DataFrames intermediários


def debug_intermediario(nome, label):
    st.header(label)
    df = st.session_state.get(nome)
    if df is not None:
        st.write(f"Shape: {df.shape}")
        st.dataframe(df.head(20), use_container_width=True)
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        st.download_button(
            label=f"⬇️ Baixar Excel do {label}",
            data=buffer,
            file_name=f"{nome}_debug.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning(f"{label} não carregado.")


for nome, label in [
    ("df_av2TratamentoMilho_merged_densidade", "DataFrame Intermediário AV2"),
    ("df_av3TratamentoMilho_merged_densidade", "DataFrame Intermediário AV3"),
    ("df_av4TratamentoMilho_merged_densidade", "DataFrame Intermediário AV4"),
]:
    debug_intermediario(nome, label)
