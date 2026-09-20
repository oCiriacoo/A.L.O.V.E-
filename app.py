import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(
    page_title="A.L.O.V.E. Mobile",
    page_icon="🚛",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.5rem;
        }
    </style>
""", unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def carregar_dados(worksheet_name: str):
    try:
        return conn.read(worksheet=worksheet_name)
    except Exception as e:
        return pd.DataFrame()

st.markdown("### 🚛 A.L.O.V.E. Mobile")
st.caption("Acompanhamento Operacional da Expedição em Tempo Real")

col_btn1, col_btn2 = st.columns([3, 1])
with col_btn2:
    if st.button("🔄 Atualizar"):
        st.cache_data.clear()
        st.rerun()

tab_frota, tab_patio, tab_escala = st.tabs([
    "🚜 Rodízio Frota",
    "📋 Pátio / Carga",
    "👷 Escala"
])

with tab_frota:
    df_frota = carregar_dados("Rodizio_Frota")
    if not df_frota.empty:
        turnos = df_frota["TURNO_JANELA"].dropna().unique().tolist()
        turno_sel = st.selectbox("Turno / Janela:", turnos, index=0)
        df_filtrado = df_frota[df_frota["TURNO_JANELA"] == turno_sel]
        
        col1, col2 = st.columns(2)
        op_count = len(df_filtrado[df_filtrado["STATUS_RODIZIO"] == "OPERAÇÃO"])
        sb_count = len(df_filtrado[df_filtrado["STATUS_RODIZIO"] == "STAND-BY"])
        col1.metric("Em Operação", f"{op_count} un")
        col2.metric("Stand-by", f"{sb_count} un")
        
        st.write("---")
        for _, row in df_filtrado.iterrows():
            status = row.get("STATUS_RODIZIO", "-")
            cor = "#198754" if status == "OPERAÇÃO" else "#ffc107"
            st.markdown(f"""
                <div style="border-left: 5px solid {cor}; background: #ffffff; padding: 10px; border-radius: 6px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); color: #111;">
                    <div style="display: flex; justify-content: space-between; font-weight: bold;">
                        <span>{row.get('EQUIPAMENTO', '-')}</span>
                        <span style="color: {cor};">{status}</span>
                    </div>
                    <div style="color: #6c757d; font-size: 0.85rem; margin-top: 4px;">
                        Posto: {row.get('POSTO', '-')}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Aba 'Rodizio_Frota' vazia ou sem acesso.")

with tab_patio:
    df_patio = carregar_dados("Patio_Programacao")
    if not df_patio.empty:
        st.write(f"Total de registros: **{len(df_patio)}**")
        st.dataframe(df_patio, use_container_width=True, hide_index=True)
    else:
        st.info("Aba 'Patio_Programacao' vazia ou indisponível.")

with tab_escala:
    df_escala = carregar_dados("Escala")
    if not df_escala.empty:
        busca = st.text_input("🔍 Buscar operador/posto:")
        if busca:
            df_escala = df_escala[df_escala.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)]
        st.dataframe(df_escala, use_container_width=True, hide_index=True)
    else:
        st.info("Aba 'Escala' vazia ou indisponível.")

st.caption("A.L.O.V.E. Core Ecosystem")
