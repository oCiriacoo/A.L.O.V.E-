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
            padding-top: 0.8rem;
            padding-bottom: 2rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.3rem;
        }
        .tag-box {
            display: inline-block;
            padding: 5px 10px;
            margin: 3px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 0.9rem;
            text-align: center;
        }
        .tag-op { background-color: #198754; color: #ffffff; }
        .tag-standby { background-color: #dc3545; color: #ffffff; }
        .card-status {
            background-color: #1e2229;
            border-radius: 8px;
            padding: 10px 14px;
            margin-bottom: 8px;
            border-left: 5px solid #0d6efd;
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

col_title, col_ref = st.columns([3, 1])
with col_title:
    st.markdown("### 🚛 A.L.O.V.E. Mobile")
with col_ref:
    if st.button("🔄 Atualizar"):
        st.cache_data.clear()
        st.rerun()

tab_carretas, tab_prod_exp, tab_frota_glp = st.tabs([
    "🚚 Carretas",
    "🏭 Produção & Expedição",
    "⛽ Frota & GLP"
])

# ==============================================================================
# ABA 1: CARRETAS (Programado, Checklist, Apoio, Fila, Termo)
# ==============================================================================
with tab_carretas:
    st.subheader("Carretas por Status & Toneladas")
    df_carretas = carregar_dados("Patio_Programacao")
    
    if not df_carretas.empty:
        cols_c = {c: str(c).strip().upper() for c in df_carretas.columns}
        df_c = df_carretas.rename(columns=cols_c)
        
        col_status = next((c for c in df_c.columns if any(k in c for k in ["STATUS", "ETAPA", "FASE"])), None)
        col_ton = next((c for c in df_c.columns if any(k in c for k in ["TON", "PESO", "CARGA", "SALDO", "VOLUME"])), None)
        
        status_ordem = ["PROGRAMADO", "CHECKLIST", "APOIO", "FILA", "TERMO"]
        
        def categorizar_status(val):
            v = str(val).upper()
            if "PROG" in v: return "Programado"
            if "CHECK" in v or "VIST" in v: return "Checklist"
            if "APOIO" in v: return "Apoio"
            if "FILA" in v or "CARREG" in v: return "Fila de Carregamento"
            if "TERM" in v or "CONCLU" in v or "FIM" in v or "LIBER" in v: return "Termo"
            return "Outros"

        if col_status:
            df_c["STATUS_PADRAO"] = df_c[col_status].apply(categorizar_status)
        else:
            df_c["STATUS_PADRAO"] = "Outros"
            
        if col_ton:
            df_c["TON_NUM"] = pd.to_numeric(df_c[col_ton], errors="coerce").fillna(0)
        else:
            df_c["TON_NUM"] = 0.0

        # Agrupamento por Status
        resumo = df_c.groupby("STATUS_PADRAO").agg(
            QTD_CARROS=("STATUS_PADRAO", "count"),
            TOTAL_TON=("TON_NUM", "sum")
        ).reset_index()

        ordem_exibicao = ["Programado", "Checklist", "Apoio", "Fila de Carregamento", "Termo"]
        resumo["STATUS_PADRAO"] = pd.Categorical(resumo["STATUS_PADRAO"], categories=ordem_exibicao, ordered=True)
        resumo = resumo.dropna().sort_values("STATUS_PADRAO")

        # Cartões informativos de cada etapa
        for _, row in resumo.iterrows():
            st.markdown(f"""
                <div class="card-status">
                    <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:1.05rem;">
                        <span>{row['STATUS_PADRAO']}</span>
                        <span style="color:#0d6efd;">{row['QTD_CARROS']} carretas</span>
                    </div>
                    <div style="color:#a0a0a0; font-size:0.9rem; margin-top:3px;">
                        Peso Total: <b>{row['TOTAL_TON']:,.1f} t</b>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.write("---")
        
        # Gráfico 1: Carretas por Status
        chart_qtd = alt.Chart(resumo).mark_bar(color="#0d6efd", cornerRadius=4).encode(
            x=alt.X("STATUS_PADRAO:N", sort=ordem_exibicao, title="Status"),
            y=alt.Y("QTD_CARROS:Q", title="Qtd Carretas"),
            tooltip=["STATUS_PADRAO", "QTD_CARROS"]
        ).properties(title="Total de Carretas por Status", height=230)
        st.altair_chart(chart_qtd, use_container_width=True)

        # Gráfico 2: Toneladas por Status
        chart_ton = alt.Chart(resumo).mark_bar(color="#198754", cornerRadius=4).encode(
            x=alt.X("STATUS_PADRAO:N", sort=ordem_exibicao, title="Status"),
            y=alt.Y("TOTAL_TON:Q", title="Toneladas (t)"),
            tooltip=["STATUS_PADRAO", "TOTAL_TON"]
        ).properties(title="Total em Toneladas (t) por Status", height=230)
        st.altair_chart(chart_ton, use_container_width=True)

    else:
        st.info("Aba 'Patio_Programacao' sem dados.")

# ==============================================================================
# ABA 2: PRODUÇÃO & EXPEDIÇÃO (Produzido vs Carregado + Qualidade)
# ==============================================================================
with tab_prod_exp:
    st.subheader("Produção & Expedição (t)")
    df_prod = carregar_dados("Expedicao_Producao")
    df_qual = carregar_dados("Qualidade_MS")

    if not df_prod.empty:
        cols_p = {c: str(c).strip().upper() for c in df_prod.columns}
        df_p = df_prod.rename(columns=cols_p)

        col_prod_t = next((c for c in df_p.columns if "PROD" in c and any(x in c for x in ["TON", "PESO", "T", "QTD"])), None)
        col_carr_t = next((c for c in df_p.columns if any(x in c for x in ["CARR", "EXP"]) and any(x in c for x in ["TON", "PESO", "T", "QTD"])), None)

        val_prod = pd.to_numeric(df_p[col_prod_t], errors="coerce").sum() if col_prod_t else 0.0
        val_carr = pd.to_numeric(df_p[col_carr_t], errors="coerce").sum() if col_carr_t else 0.0

        c1, c2 = st.columns(2)
        c1.metric("Produzido Total", f"{val_prod:,.1f} t")
        c2.metric("Carregado Total", f"{val_carr:,.1f} t")

        # Gráfico Comparativo Produzido vs Carregado
        df_comp = pd.DataFrame({
            "Operação": ["Produzido", "Carregado"],
            "Toneladas": [val_prod, val_carr]
        })
        chart_comp = alt.Chart(df_comp).mark_bar(cornerRadius=4).encode(
            x=alt.X("Operação:N", title=""),
            y=alt.Y("Toneladas:Q", title="Toneladas (t)"),
            color=alt.Color("Operação:N", scale=alt.Scale(range=["#0d6efd", "#20c997"]), legend=None),
            tooltip=["Operação", "Toneladas"]
        ).properties(height=230)
        st.altair_chart(chart_comp, use_container_width=True)

    else:
        st.info("Aba 'Expedicao_Producao' indisponível.")

    st.write("---")
    st.subheader("Indicadores de Qualidade")
    if not df_qual.empty:
        cols_q = {c: str(c).strip().upper() for c in df_qual.columns}
        df_q = df_qual.rename(columns=cols_q)

        col_suj = next((c for c in df_q.columns if "SUJ" in c), None)
        col_visc = next((c for c in df_q.columns if "VISC" in c), None)
        col_teor = next((c for c in df_q.columns if "TEOR" in c or "SEC" in c), None)

        q1, q2, q3 = st.columns(3)
        if col_suj:
            v_suj = pd.to_numeric(df_q[col_suj], errors="coerce").dropna().iloc[-1]
            q1.metric("Sujidade", f"{v_suj:.2f}")
        if col_visc:
            v_visc = pd.to_numeric(df_q[col_visc], errors="coerce").dropna().iloc[-1]
            q2.metric("Viscosidade", f"{v_visc:.1f}")
        if col_teor:
            v_teor = pd.to_numeric(df_q[col_teor], errors="coerce").dropna().iloc[-1]
            q3.metric("Teor Seco", f"{v_teor:.2f}%")
    else:
        st.info("Aba 'Qualidade_MS' sem registros.")

# ==============================================================================
# ABA 3: FROTA & GLP MENSAL (Quilos por Mês e por Máquina)
# ==============================================================================
with tab_frota_glp:
    st.subheader("Máquinas em Operação & Paradas")
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
                if "00:00" in t and (0 <= hora_atual < 8): idx_sug = i
                elif "08:00" in t and (8 <= hora_atual < 16): idx_sug = i
                elif "16:00" in t and (16 <= hora_atual <= 23): idx_sug = i
            turno_sel = st.selectbox("Turno / Janela:", turnos, index=idx_sug)
            df_f = df_f[df_f[col_turno] == turno_sel]

        if col_tag and col_status and col_posto:
            carr_op = df_f[(df_f[col_posto].astype(str).str.contains("CARREG", case=False, na=False)) & 
                           (df_f[col_status].astype(str).str.contains("OPERA", case=False, na=False))][col_tag].tolist()
            linha_op = df_f[(df_f[col_posto].astype(str).str.contains("LINHA", case=False, na=False)) & 
                            (df_f[col_status].astype(str).str.contains("OPERA", case=False, na=False))][col_tag].tolist()
            paradas = df_f[df_f[col_status].astype(str).str.contains("STAND|PARAD|OFF", case=False, na=False)][col_tag].tolist()

            st.markdown("🟢 **Em Operação — CARREGAMENTO:**")
            if carr_op:
                st.markdown(" ".join([f'<span class="tag-box tag-op">{tag}</span>' for tag in carr_op]), unsafe_allow_html=True)
            else:
                st.caption("Nenhuma alocada.")

            st.markdown("<br>🟢 **Em Operação — LINHA:**", unsafe_allow_html=True)
            if linha_op:
                st.markdown(" ".join([f'<span class="tag-box tag-op">{tag}</span>' for tag in linha_op]), unsafe_allow_html=True)
            else:
                st.caption("Nenhuma alocada.")

            st.markdown("<br>🔴 **Equipamentos Parados / Stand-by:**", unsafe_allow_html=True)
            if paradas:
                st.markdown(" ".join([f'<span class="tag-box tag-standby">{tag}</span>' for tag in paradas]), unsafe_allow_html=True)
            else:
                st.caption("Nenhuma parada.")
    else:
        st.info("Aba 'Rodizio_Frota' sem dados.")

    st.write("---")
    st.subheader("⛽ Consumo Mensal de GLP (kg)")
    df_glp = carregar_dados("Abastecimentos_GLP")

    if not df_glp.empty:
        cols_g = {c: str(c).strip().upper() for c in df_glp.columns}
        df_g = df_glp.rename(columns=cols_g)

        col_data = next((c for c in df_g.columns if any(k in c for k in ["DATA", "TIMESTAMP", "HORA"])), None)
        col_maq_glp = next((c for c in df_g.columns if any(k in c for k in ["EQUIPAMENTO", "MAQUINA", "TAG", "EMPILHADEIRA"])), None)
        col_kg = next((c for c in df_g.columns if any(k in c for k in ["KG", "QUILO", "PESO", "QTD", "VOLUME", "LITROS"])), None)

        if col_data:
            df_g["DATA_DT"] = pd.to_datetime(df_g[col_data], errors="coerce", dayfirst=True)
            df_g["MES_ANO"] = df_g["DATA_DT"].dt.strftime("%m/%Y")
            meses_disp = df_g["MES_ANO"].dropna().unique().tolist()
            if meses_disp:
                mes_sel = st.selectbox("Mês de Referência:", meses_disp, index=len(meses_disp)-1)
                df_g = df_g[df_g["MES_ANO"] == mes_sel]

        if col_kg:
            # Multiplicador se a planilha contabilizar botijão P20 (20kg cada) ou quilos diretos
            df_g["KG_NUM"] = pd.to_numeric(df_g[col_kg], errors="coerce").fillna(0)
            total_kg = df_g["KG_NUM"].sum()
            st.metric(f"Total Abastecido no Mês ({mes_sel if col_data else ''})", f"{total_kg:,.1f} kg")

            if col_maq_glp:
                st.markdown("##### Consumo em Kg por Máquina")
                df_maq_glp = df_g.groupby(col_maq_glp)["KG_NUM"].sum().reset_index()
                df_maq_glp.columns = ["Máquina", "Quilos"]
                df_maq_glp = df_maq_glp.sort_values(by="Quilos", ascending=False)

                chart_glp = alt.Chart(df_maq_glp).mark_bar(color="#fd7e14", cornerRadius=4).encode(
                    x=alt.X("Máquina:N", sort="-y", title="Máquina"),
                    y=alt.Y("Quilos:Q", title="Consumo (kg)"),
                    tooltip=["Máquina", "Quilos"]
                ).properties(height=260)
                st.altair_chart(chart_glp, use_container_width=True)
    else:
        st.info("Aba 'Abastecimentos_GLP' sem registros.")

st.caption("A.L.O.V.E. Mobile Dashboard")
