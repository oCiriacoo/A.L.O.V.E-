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
        div[data-testid="stMetricValue"] { font-size: 1.4rem; }
        .card-status {
            background-color: #1e2229;
            border-radius: 8px;
            padding: 14px;
            margin-bottom: 10px;
            border-left: 5px solid #0d6efd;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
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
    </style>
""", unsafe_allow_html=True)

SHEET_ID = "10FluiIwlynIlPDA74QI8mpHSIrAc-62H1hZNRBsvfCA"

@st.cache_data(ttl=30)
def carregar_dados(worksheet_name: str, cabecalho=0):
    sheet_encoded = urllib.parse.quote(worksheet_name)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_encoded}"
    try:
        df = pd.read_csv(url, header=cabecalho)
        df = df.dropna(how="all", axis=1).dropna(how="all", axis=0)
        return df
    except Exception:
        return pd.DataFrame()

def safe_to_numeric(val):
    try:
        v = str(val).replace(".", "").replace(",", ".")
        return float(v)
    except:
        return 0.0

col_title, col_ref = st.columns([3, 1])
with col_title:
    st.markdown("### 🚛 A.L.O.V.E. Mobile")
with col_ref:
    if st.button("🔄 Atualizar"):
        st.cache_data.clear()
        st.rerun()

tab_carretas, tab_prod_exp, tab_frota_glp = st.tabs([
    "🚚 Carretas",
    "🏭 Prod & Exp",
    "⛽ Frota & GLP"
])

# ==============================================================================
# ABA 1: CARRETAS (Blocos Renomeados com Qtd)
# ==============================================================================
with tab_carretas:
    st.subheader("Blocos do Pátio (Qtd)")
    df_c = carregar_dados("Patio_Programacao")
    
    if not df_c.empty:
        ultima_linha = df_c.iloc[-1]
        
        # Mapeamento com os nomes exatos solicitados e a métrica correspondente
        blocos = [
            ("Programado (Pátio Total)", ultima_linha.get('PATIO_TOTAL', 0), "#6c757d"),
            ("Checklist (Fila Triagem)", ultima_linha.get('FILA_TRIAGEM', 0), "#ffc107"),
            ("Apoio (Bloqueados)", ultima_linha.get('BLOQUEADOS', 0), "#dc3545"),
            ("Fila (Em Carregamento)", ultima_linha.get('EM_CARREGAMENTO', 0), "#0d6efd"),
            ("Termo (Liberados)", ultima_linha.get('LIBERADOS_EXPEDICAO', 0), "#198754"),
        ]
        
        for nome, valor, cor in blocos:
            st.markdown(f"""
                <div class="card-status" style="border-left-color: {cor};">
                    <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:1.1rem; color: #fff;">
                        <span>{nome}</span>
                        <span style="color: {cor};">{valor} </span>
                    </div>
                    <div style="color:#a0a0a0; font-size:0.85rem; margin-top:3px;">
                        *Soma em Toneladas indisponível nesta aba do Core.
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
    else:
        st.info("Aba Patio_Programacao indisponível.")

# ==============================================================================
# ABA 2: PRODUÇÃO, EXPEDIÇÃO E QUALIDADE
# ==============================================================================
with tab_prod_exp:
    st.subheader("Expedição & Produção Diária (t)")
    df_p = carregar_dados("Expedicao_Producao")
    
    if not df_p.empty:
        ultima_p = df_p.iloc[-1]
        
        prod_hj = safe_to_numeric(ultima_p.get('PROD_HOJE', 0))
        vol_hj = safe_to_numeric(ultima_p.get('VOL_HOJE', 0))
        est_tot = safe_to_numeric(ultima_p.get('ESTOQUE_TOTAL', 0))
        
        c1, c2 = st.columns(2)
        c1.metric("Produção Hoje", f"{prod_hj:,.1f} t")
        c2.metric("Volume Expedido", f"{vol_hj:,.1f} t")
        
        st.metric("Estoque Total", f"{est_tot:,.1f} t")
        
        # Gráfico triplo: Produção, Expedição e Estoque Total
        df_comp = pd.DataFrame({
            "Métrica": ["Produção", "Expedição", "Estoque Total"],
            "Toneladas": [prod_hj, vol_hj, est_tot]
        })
        chart_comp = alt.Chart(df_comp).mark_bar(cornerRadius=4).encode(
            x=alt.X("Métrica:N", sort=None, title=""),
            y=alt.Y("Toneladas:Q", title="Toneladas"),
            color=alt.Color("Métrica:N", scale=alt.Scale(range=["#20c997", "#0d6efd", "#ffc107"]), legend=None),
            tooltip=["Métrica", "Toneladas"]
        ).properties(height=260)
        st.altair_chart(chart_comp, use_container_width=True)
    else:
        st.info("Aba Expedicao_Producao indisponível.")

    st.write("---")
    st.subheader("Indicadores de Qualidade (Humidade)")
    df_q = carregar_dados("Qualidade_MS")
    if not df_q.empty:
        ultima_q = df_q.iloc[-1]
        
        q1, q2 = st.columns(2)
        umid_l1 = safe_to_numeric(ultima_q.get('UMIDADE_L1', 0))
        umid_l2 = safe_to_numeric(ultima_q.get('UMIDADE_L2', 0))
        
        q1.metric("Umidade L1", f"{umid_l1:.2f}%" if umid_l1 else "-")
        q2.metric("Umidade L2", f"{umid_l2:.2f}%" if umid_l2 else "-")
    else:
        st.info("Aba Qualidade_MS indisponível.")

# ==============================================================================
# ABA 3: FROTA & GLP
# ==============================================================================
with tab_frota_glp:
    st.subheader("Alocação de Equipamentos")
    df_frota = carregar_dados("Rodizio_Frota")

    if not df_frota.empty:
        col_turno = "TURNO_JANELA" if "TURNO_JANELA" in df_frota.columns else df_frota.columns[0]
        if col_turno in df_frota.columns:
            turnos = df_frota[col_turno].dropna().unique().tolist()
            hora_atual = datetime.now().hour
            idx_sug = 0
            for i, t in enumerate(turnos):
                if "00:00" in str(t) and (0 <= hora_atual < 8): idx_sug = i
                elif "08:00" in str(t) and (8 <= hora_atual < 16): idx_sug = i
                elif "16:00" in str(t) and (16 <= hora_atual <= 23): idx_sug = i
            turno_sel = st.selectbox("Turno / Janela:", turnos, index=idx_sug)
            df_f = df_frota[df_frota[col_turno] == turno_sel]

            carr_op = df_f[(df_f["POSTO"].astype(str).str.contains("CARREG", case=False)) & (df_f["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]["EQUIPAMENTO"].tolist()
            linha_op = df_f[(df_f["POSTO"].astype(str).str.contains("LINHA", case=False)) & (df_f["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]["EQUIPAMENTO"].tolist()
            paradas = df_f[df_f["STATUS_RODIZIO"].astype(str).str.contains("STAND", case=False)]["EQUIPAMENTO"].tolist()

            st.markdown("🟢 **Em Operação — CARREGAMENTO:**")
            if carr_op: st.markdown(" ".join([f'<span class="tag-box tag-op">{tag}</span>' for tag in carr_op]), unsafe_allow_html=True)
            else: st.caption("Nenhum.")

            st.markdown("<br>🟢 **Em Operação — LINHA:**", unsafe_allow_html=True)
            if linha_op: st.markdown(" ".join([f'<span class="tag-box tag-op">{tag}</span>' for tag in linha_op]), unsafe_allow_html=True)
            else: st.caption("Nenhum.")

            st.markdown("<br>🔴 **Stand-by / Paradas:**", unsafe_allow_html=True)
            if paradas: st.markdown(" ".join([f'<span class="tag-box tag-standby">{tag}</span>' for tag in paradas]), unsafe_allow_html=True)
            else: st.caption("Nenhum.")
            
    st.write("---")
    st.subheader("⛽ Consumo Mensal de GLP")
    
    df_glp = carregar_dados("Abastecimentos_GLP", cabecalho=None)
    
    if not df_glp.empty:
        try:
            df_g = pd.DataFrame()
            df_g["DATA_DT"] = pd.to_datetime(df_glp.iloc[:, 2].astype(str).str.strip(), format="%d/%m/%Y", errors="coerce")
            df_g["MES_ANO"] = df_g["DATA_DT"].dt.strftime("%m/%Y")
            df_g["MAQUINA"] = df_glp.iloc[:, 5].astype(str).str.strip()
            df_g["KG_NUM"] = df_glp.iloc[:, 7].apply(safe_to_numeric)
            
            meses_disp = df_g["MES_ANO"].dropna().unique().tolist()
            if meses_disp:
                meses_disp.sort(key=lambda x: datetime.strptime(x, "%m/%Y"))
                mes_sel = st.selectbox("Mês Referência:", meses_disp, index=len(meses_disp)-1)
                
                df_mes = df_g[df_g["MES_ANO"] == mes_sel]
                total_kg = df_mes["KG_NUM"].sum()
                
                st.metric(f"Total Abastecido ({mes_sel})", f"{total_kg:,.1f} kg")
                
                st.markdown("##### Consumo por Máquina (kg)")
                df_maq = df_mes.groupby("MAQUINA")["KG_NUM"].sum().reset_index()
                df_maq.columns = ["Máquina", "Consumo (kg)"]
                
                chart_glp = alt.Chart(df_maq).mark_bar(color="#fd7e14", cornerRadius=4).encode(
                    x=alt.X("Máquina:N", sort="-y", title="Máquina"),
                    y=alt.Y("Consumo (kg):Q", title="Quilos"),
                    tooltip=["Máquina", "Consumo (kg)"]
                ).properties(height=260)
                st.altair_chart(chart_glp, use_container_width=True)
            else:
                st.info("Não foi possível processar as datas do GLP.")
        except Exception as e:
            st.error(f"Erro no processamento do GLP: {e}")
    else:
        st.info("Aba Abastecimentos_GLP indisponível.")

st.caption("A.L.O.V.E. Mobile Dashboard")
