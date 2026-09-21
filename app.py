import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse

# Configuração de ecrã móvel
st.set_page_config(
    page_title="A.L.O.V.E. Mobile",
    page_icon="🚛",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilização compacta para smartphone
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
    </style>
""", unsafe_allow_html=True)

# ID da folha ALOV_Core_DB
SHEET_ID = "10FluiIwlynIlPDA74QI8mpHSIrAc-62H1hZNRBsvfCA"

@st.cache_data(ttl=30)
def carregar_dados(worksheet_name: str):
    """Lê a aba da folha pública diretamente via exportação CSV."""
    sheet_encoded = urllib.parse.quote(worksheet_name)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_encoded}"
    try:
        df = pd.read_csv(url)
        # Remove colunas totalmente vazias originadas pelo Sheets
        df = df.dropna(how="all", axis=1)
        df = df.dropna(how="all", axis=0)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar '{worksheet_name}': {e}")
        return pd.DataFrame()

# Cabeçalho Móvel
col_title, col_ref = st.columns([3, 1])
with col_title:
    st.markdown("### 🚛 A.L.O.V.E. Mobile")
    st.caption("Ecossistema Operacional da Expedição")
with col_ref:
    if st.button("🔄 Atualizar"):
        st.cache_data.clear()
        st.rerun()

# Três Abas Operacionais
tab_carretas, tab_producao, tab_frota_glp = st.tabs([
    "🚚 Carretas",
    "🏭 Produção",
    "⛽ Frota & GLP"
])

# ==============================================================================
# ABA 1: CARRETAS (Pátio & Programação)
# ==============================================================================
with tab_carretas:
    st.subheader("Fluxo de Pátio & Carretas")
    df_carretas = carregar_dados("Patio_Programacao")
    
    if not df_carretas.empty:
        cols_norm = {c: str(c).strip().upper() for c in df_carretas.columns}
        df_c = df_carretas.rename(columns=cols_norm)
        
        col_status = next((c for c in df_c.columns if any(k in c for k in ["STATUS", "ETAPA", "FASE"])), None)
        col_tipo = next((c for c in df_c.columns if any(k in c for k in ["TIPO", "OPERACAO", "PRODUTO"])), None)
        
        if col_tipo:
            tipos = ["TODOS"] + [str(x) for x in df_c[col_tipo].dropna().unique().tolist()]
            tipo_sel = st.selectbox("Tipo de Operação:", tipos)
            if tipo_sel != "TODOS":
                df_c = df_c[df_c[col_tipo].astype(str) == tipo_sel]
                
        if col_status:
            st.markdown("##### Status das Carretas")
            contagem = df_c[col_status].value_counts()
            grid = st.columns(min(len(contagem), 3) if len(contagem) > 0 else 1)
            for idx, (st_nome, val) in enumerate(contagem.items()):
                grid[idx % len(grid)].metric(str(st_nome), f"{val}")
        
        st.write("---")
        st.dataframe(df_c, use_container_width=True, hide_index=True)
    else:
        st.info("Aba 'Patio_Programacao' vazia ou sem registos.")

# ==============================================================================
# ABA 2: PRODUÇÃO & QUALIDADE
# ==============================================================================
with tab_producao:
    st.subheader("Produção & Qualidade")
    df_prod = carregar_dados("Expedicao_Producao")
    df_qual = carregar_dados("Qualidade_MS")
    
    if not df_prod.empty:
        cols_norm = {c: str(c).strip().upper() for c in df_prod.columns}
        df_p = df_prod.rename(columns=cols_norm)
        
        col_maq = next((c for c in df_p.columns if any(k in c for k in ["MAQUINA", "LINHA", "EQUIPAMENTO"])), None)
        col_vol = next((c for c in df_p.columns if any(k in c for k in ["PRODUCAO", "TON", "PESO", "QTD", "VOLUME"])), None)
        
        if col_vol:
            try:
                prod_total = pd.to_numeric(df_p[col_vol], errors='coerce').sum()
                st.metric("🏭 Produção Total", f"{prod_total:,.1f} t")
            except Exception:
                st.metric("Total de Registos", len(df_p))
                
        if col_maq and col_vol:
            st.markdown("##### ⚙️ Produção por Máquina")
            try:
                prod_m = df_p.groupby(col_maq)[col_vol].sum().reset_index()
                st.dataframe(prod_m, use_container_width=True, hide_index=True)
            except Exception:
                st.dataframe(df_p[[col_maq, col_vol]], use_container_width=True, hide_index=True)
                
        st.write("---")
        st.markdown("**Apontamentos de Produção:**")
        st.dataframe(df_prod, use_container_width=True, hide_index=True)
    else:
        st.info("Aba 'Expedicao_Producao' indisponível ou vazia.")
        
    if not df_qual.empty:
        st.write("---")
        st.markdown("##### 🏷️ Indicadores de Qualidade")
        st.dataframe(df_qual, use_container_width=True, hide_index=True)

# ==============================================================================
# ABA 3: FROTA POR PERÍODO & CONSUMO GLP
# ==============================================================================
with tab_frota_glp:
    st.subheader("Gestão de Máquinas & GLP")
    
    st.markdown("#### 🚜 Máquinas por Período / Turno")
    df_frota = carregar_dados("Rodizio_Frota")
    
    if not df_frota.empty:
        cols_f = {c: str(c).strip().upper() for c in df_frota.columns}
        df_f = df_frota.rename(columns=cols_f)
        
        col_turno = next((c for c in df_f.columns if any(k in c for k in ["TURNO", "JANELA", "PERIODO", "HORARIO"])), None)
        
        if col_turno:
            turnos = ["TODOS"] + [str(x) for x in df_f[col_turno].dropna().unique().tolist()]
            hora_atual = datetime.now().hour
            idx_sugerido = 0
            for i, t in enumerate(turnos):
                if "00:00" in t and (0 <= hora_atual < 8):
                    idx_sugerido = i
                elif "08:00" in t and (8 <= hora_atual < 16):
                    idx_sugerido = i
                elif "16:00" in t and (16 <= hora_atual <= 23):
                    idx_sugerido = i
            
            turno_escolhido = st.selectbox("Selecione o Período / Horário:", turnos, index=idx_sugerido)
            if turno_escolhido != "TODOS":
                df_f = df_f[df_f[col_turno].astype(str) == turno_escolhido]
        
        col_status_maq = next((c for c in df_f.columns if any(k in c for k in ["STATUS"])), None)
        if col_status_maq:
            m1, m2 = st.columns(2)
            em_op = len(df_f[df_f[col_status_maq].astype(str).str.contains("OPERAÇÃO|OPERACAO", case=False, na=False)])
            em_sb = len(df_f[df_f[col_status_maq].astype(str).str.contains("STAND-BY|STANDBY", case=False, na=False)])
            m1.metric("Em Operação", f"{em_op} un")
            m2.metric("Stand-by", f"{em_sb} un")
            
        st.dataframe(df_f, use_container_width=True, hide_index=True)
    else:
        st.info("Aba 'Rodizio_Frota' sem dados.")
        
    st.write("---")
    st.markdown("#### ⛽ Abastecimento de GLP")
    df_glp = carregar_dados("Abastecimentos_GLP")
    
    if not df_glp.empty:
        cols_g = {c: str(c).strip().upper() for c in df_glp.columns}
        df_g = df_glp.rename(columns=cols_g)
        
        col_maq_glp = next((c for c in df_g.columns if any(k in c for k in ["EQUIPAMENTO", "MAQUINA", "TAG", "EMPILHADEIRA"])), None)
        col_qtd_glp = next((c for c in df_g.columns if any(k in c for k in ["QTD", "QUANTIDADE", "VOLUME", "LITROS", "KG", "TOTAL"])), None)
        
        if col_qtd_glp:
            try:
                glp_total = pd.to_numeric(df_g[col_qtd_glp], errors='coerce').sum()
                st.metric("🔥 Total Geral de GLP", f"{glp_total:,.1f}")
            except Exception:
                st.metric("Total de Abastecimentos", len(df_g))
        else:
            st.metric("Total de Registos", f"{len(df_g)} un")
            
        if col_maq_glp:
            st.markdown("##### 🚜 GLP por Máquina")
            if col_qtd_glp:
                try:
                    glp_por_maq = df_g.groupby(col_maq_glp)[col_qtd_glp].sum().reset_index()
                    glp_por_maq = glp_por_maq.sort_values(by=col_qtd_glp, ascending=False)
                    st.dataframe(glp_por_maq, use_container_width=True, hide_index=True)
                except Exception:
                    st.dataframe(df_g[[col_maq_glp, col_qtd_glp]], use_container_width=True, hide_index=True)
            else:
                trocas_maq = df_g[col_maq_glp].value_counts().reset_index()
                trocas_maq.columns = ["Equipamento", "Contagem"]
                st.dataframe(trocas_maq, use_container_width=True, hide_index=True)
                
        st.markdown("**Detalhamento de Abastecimentos:**")
        st.dataframe(df_glp, use_container_width=True, hide_index=True)
    else:
        st.info("Aba 'Abastecimentos_GLP' sem registos.")

st.caption("A.L.O.V.E. Mobile Dashboard")
