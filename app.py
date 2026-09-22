import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import altair as alt

st.set_page_config(
    page_title="A.L.O.V.E. Mobile",
    page_icon="🚛",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.4rem;
        }
        .tag-box {
            display: inline-block;
            padding: 6px 12px;
            margin: 4px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 0.95rem;
            text-align: center;
        }
        .tag-op {
            background-color: #198754;
            color: #ffffff;
        }
        .tag-standby {
            background-color: #dc3545;
            color: #ffffff;
        }
    </style>
""", unsafe_allow_html=True)

SHEET_ID = "10FluiIwlynIlPDA74QI8mpHSIrAc-62H1hZNRBsvfCA"

@st.cache_data(ttl=30)
def carregar_dados(worksheet_name: str):
    sheet_encoded = urllib.parse.quote(worksheet_name)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_encoded}"
    try:
        df = pd.read_csv(url)
        df = df.dropna(how="all", axis=1).dropna(how="all", axis=0)
        return df
    except Exception:
        return pd.DataFrame()

# Cabeçalho Mobile
col_title, col_ref = st.columns([3, 1])
with col_title:
    st.markdown("### 🚛 A.L.O.V.E. Mobile")
    st.caption("Indicadores Operacionais em Tempo Real")
with col_ref:
    if st.button("🔄 Atualizar"):
        st.cache_data.clear()
        st.rerun()

tab_carretas, tab_producao, tab_frota_glp = st.tabs([
    "🚚 Carretas",
    "🏭 Produção",
    "⛽ Frota & GLP"
])

# ==============================================================================
# ABA 1: CARRETAS (Apenas Gráficos)
# ==============================================================================
with tab_carretas:
    st.subheader("Fluxo de Pátio & Carregamento")
    df_carretas = carregar_dados("Patio_Programacao")
    
    if not df_carretas.empty:
        cols_norm = {c: str(c).strip().upper() for c in df_carretas.columns}
        df_c = df_carretas.rename(columns=cols_norm)
        
        # Último apontamento registrado
        col_patio = next((c for c in df_c.columns if "PATIO_TOTAL" in c or "TOTAL" in c), None)
        col_carr = next((c for c in df_c.columns if "CARREGAMENTO" in c), None)
        
        m1, m2 = st.columns(2)
        if col_patio:
            val_p = pd.to_numeric(df_c[col_patio], errors="coerce").dropna().iloc[-1]
            m1.metric("Pátio Total Atual", f"{val_p:,.0f}")
        if col_carr:
            val_c = pd.to_numeric(df_c[col_carr], errors="coerce").dropna().iloc[-1]
            m2.metric("Em Carregamento", f"{val_c:,.0f}")
            
        st.write("---")
        
        # Gráfico Temporal da evolução do Pátio e Carregamento
        col_time = next((c for c in df_c.columns if "TIME" in c or "DATA" in c or "HORA" in c), df_c.columns[0])
        col_vars = [c for c in [col_patio, col_carr] if c is not None]
        
        if col_vars:
            df_plot = df_c[[col_time] + col_vars].copy()
            for col in col_vars:
                df_plot[col] = pd.to_numeric(df_plot[col], errors="coerce")
            
            df_melted = df_plot.melt(id_vars=[col_time], value_vars=col_vars, var_name="Métrica", value_name="Volume")
            chart_patio = alt.Chart(df_melted).mark_line(point=True).encode(
                x=alt.X(f"{col_time}:N", sort=None, title="Horário"),
                y=alt.Y("Volume:Q", title="Volume / Quantidade"),
                color=alt.Color("Métrica:N", legend=alt.Legend(orient="bottom"))
            ).properties(height=280)
            st.altair_chart(chart_patio, use_container_width=True)
    else:
        st.info("Aba 'Patio_Programacao' sem dados.")

# ==============================================================================
# ABA 2: PRODUÇÃO (Apenas Gráficos)
# ==============================================================================
with tab_producao:
    st.subheader("Produção Industrial")
    df_prod = carregar_dados("Expedicao_Producao")
    
    if not df_prod.empty:
        cols_norm = {c: str(c).strip().upper() for c in df_prod.columns}
        df_p = df_prod.rename(columns=cols_norm)
        
        col_maq = next((c for c in df_p.columns if any(k in c for k in ["MAQUINA", "LINHA", "EQUIPAMENTO"])), None)
        col_vol = next((c for c in df_p.columns if any(k in c for k in ["PRODUCAO", "TON", "PESO", "QTD", "VOLUME"])), None)
        
        if col_vol:
            prod_num = pd.to_numeric(df_p[col_vol], errors='coerce').fillna(0)
            st.metric("🏭 Produção Total Acumulada", f"{prod_num.sum():,.1f} t")
            
            if col_maq:
                st.markdown("##### Produção por Linha / Máquina")
                df_m = df_p.groupby(col_maq)[col_vol].apply(lambda x: pd.to_numeric(x, errors='coerce').sum()).reset_index()
                df_m.columns = ["Máquina", "Toneladas"]
                
                chart_maq = alt.Chart(df_m).mark_bar(cornerRadius=4).encode(
                    x=alt.X("Máquina:N", sort="-y", title="Máquina"),
                    y=alt.Y("Toneladas:Q", title="Produção (t)"),
                    color=alt.Color("Máquina:N", legend=None)
                ).properties(height=260)
                st.altair_chart(chart_maq, use_container_width=True)
    else:
        st.info("Aba 'Expedicao_Producao' indisponível.")

# ==============================================================================
# ABA 3: MÁQUINAS (Tags por Posto) & GLP (Total + Gráfico)
# ==============================================================================
with tab_frota_glp:
    st.subheader("Máquinas por Período")
    df_frota = carregar_dados("Rodizio_Frota")
    
    if not df_frota.empty:
        cols_f = {c: str(c).strip().upper() for c in df_frota.columns}
        df_f = df_frota.rename(columns=cols_f)
        
        col_turno = next((c for c in df_f.columns if any(k in c for k in ["TURNO", "JANELA", "PERIODO"])), None)
        col_posto = next((c for c in df_f.columns if any(k in c for k in ["POSTO", "AREA", "SETOR"])), None)
        col_status = next((c for c in df_f.columns if any(k in c for k in ["STATUS"])), None)
        col_tag = next((c for c in df_f.columns if any(k in c for k in ["EQUIPAMENTO", "TAG", "MAQUINA"])), None)
        
        if col_turno:
            turnos = df_f[col_turno].dropna().unique().tolist()
            hora_atual = datetime.now().hour
            idx_sug = 0
            for i, t in enumerate(turnos):
                if "00:00" in t and (0 <= hora_atual < 8):
                    idx_sug = i
                elif "08:00" in t and (8 <= hora_atual < 16):
                    idx_sug = i
                elif "16:00" in t and (16 <= hora_atual <= 23):
                    idx_sug = i
                    
            turno_sel = st.selectbox("Turno / Janela:", turnos, index=idx_sug)
            df_f = df_f[df_f[col_turno] == turno_sel]
            
        if col_tag and col_status and col_posto:
            # 1. Carregamento em Operação
            carr_op = df_f[(df_f[col_posto].astype(str).str.contains("CARREG", case=False, na=False)) & 
                           (df_f[col_status].astype(str).str.contains("OPERA", case=False, na=False))][col_tag].tolist()
            
            # 2. Linha em Operação
            linha_op = df_f[(df_f[col_posto].astype(str).str.contains("LINHA", case=False, na=False)) & 
                            (df_f[col_status].astype(str).str.contains("OPERA", case=False, na=False))][col_tag].tolist()
            
            # 3. Equipamentos Parados / Stand-by
            paradas = df_f[df_f[col_status].astype(str).str.contains("STAND|PARAD|OFF", case=False, na=False)][col_tag].tolist()
            
            st.markdown("🟢 **Em Operação — CARREGAMENTO:**")
            if carr_op:
                tags_html = " ".join([f'<span class="tag-box tag-op">{tag}</span>' for tag in carr_op])
                st.markdown(tags_html, unsafe_allow_html=True)
            else:
                st.caption("Nenhum equipamento alocado.")
                
            st.markdown("<br>🟢 **Em Operação — LINHA:**", unsafe_allow_html=True)
            if linha_op:
                tags_html = " ".join([f'<span class="tag-box tag-op">{tag}</span>' for tag in linha_op])
                st.markdown(tags_html, unsafe_allow_html=True)
            else:
                st.caption("Nenhum equipamento alocado.")
                
            st.markdown("<br>🔴 **Equipamentos Parados / Stand-by:**", unsafe_allow_html=True)
            if paradas:
                tags_html = " ".join([f'<span class="tag-box tag-standby">{tag}</span>' for tag in paradas])
                st.markdown(tags_html, unsafe_allow_html=True)
            else:
                st.caption("Nenhuma máquina parada.")
    else:
        st.info("Aba 'Rodizio_Frota' sem dados.")
        
    st.write("---")
    
    # -------------------------------------------------------------------------
    # CONSUMO GLP (Apenas Total Geral + Gráfico por Máquina)
    # -------------------------------------------------------------------------
    st.subheader("⛽ Abastecimento de GLP")
    df_glp = carregar_dados("Abastecimentos_GLP")
    
    if not df_glp.empty:
        cols_g = {c: str(c).strip().upper() for c in df_glp.columns}
        df_g = df_glp.rename(columns=cols_g)
        
        col_maq_glp = next((c for c in df_g.columns if any(k in c for k in ["EQUIPAMENTO", "MAQUINA", "TAG", "EMPILHADEIRA"])), None)
        col_qtd_glp = next((c for c in df_g.columns if any(k in c for k in ["QTD", "QUANTIDADE", "VOLUME", "LITROS", "KG", "TOTAL"])), None)
        
        if col_qtd_glp:
            total_glp = pd.to_numeric(df_g[col_qtd_glp], errors='coerce').sum()
            st.metric("Total Geral de GLP Abastecido", f"{total_glp:,.1f}")
        else:
            st.metric("Total Geral de Trocas de GLP", f"{len(df_g)} un")
            
        if col_maq_glp:
            st.markdown("##### Consumo de GLP por Máquina")
            if col_qtd_glp:
                df_glp_group = df_g.groupby(col_maq_glp)[col_qtd_glp].apply(lambda x: pd.to_numeric(x, errors='coerce').sum()).reset_index()
                df_glp_group.columns = ["Equipamento", "Consumo"]
            else:
                df_glp_group = df_g[col_maq_glp].value_counts().reset_index()
                df_glp_group.columns = ["Equipamento", "Consumo"]
                
            chart_glp = alt.Chart(df_glp_group).mark_bar(color="#fd7e14", cornerRadius=4).encode(
                x=alt.X("Equipamento:N", sort="-y", title="Equipamento"),
                y=alt.Y("Consumo:Q", title="Total de GLP / Trocas"),
                tooltip=["Equipamento", "Consumo"]
            ).properties(height=260)
            
            st.altair_chart(chart_glp, use_container_width=True)
    else:
        st.info("Aba 'Abastecimentos_GLP' sem registros.")

st.caption("A.L.O.V.E. Mobile Dashboard")
