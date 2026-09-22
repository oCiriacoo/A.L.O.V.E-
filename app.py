import streamlit as st
import pandas as pd
import urllib.parse

SHEET_ID = "10FluiIwlynIlPDA74QI8mpHSIrAc-62H1hZNRBsvfCA"

def ver_colunas(aba):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(aba)}"
    try:
        df = pd.read_csv(url)
        st.write(f"**Aba: {aba}**")
        st.write(df.columns.tolist())
    except Exception as e:
        st.write(f"Erro na aba {aba}: {e}")

st.markdown("### Diagnóstico ALOV Core")
ver_colunas("Patio_Programacao")
ver_colunas("Expedicao_Producao")
ver_colunas("Qualidade_MS")
ver_colunas("Abastecimentos_GLP")
