import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import altair as alt
import json

st.set_page_config(
    page_title="A.L.O.V.E. Mobile",
    page_icon="🚛",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        .block-container {
            padding-top: 3.5rem;
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
    if pd.isna(val): return 0.0
    if isinstance(val, (int, float)): return float(val)
    try:
        s_val = str(val).strip()
        if not s_val: return 0.0
        if "," in s_val:
            s_val = s_val.replace(".", "")
            s_val = s_val.replace(",", ".")
        return float(s_val)
    except Exception:
        return 0.0

# ==============================================================================
# 🔥 LEITURA DOS DADOS DA NUVEM (CACHE_PAINEL)
# ==============================================================================
df_cache = carregar_dados("Cache_Painel", cabecalho=0)
cache_dict = {}
if not df_cache.empty:
    for _, row in df_cache.iterrows():
        chave = str(row.iloc[0]).strip()
        valor = str(row.iloc[1]).strip()
        cache_dict[chave] = valor

dados_patio = {}
qualidade = {}
try: dados_patio = json.loads(cache_dict.get("dados_patio", "{}"))
except: pass
try: qualidade = json.loads(cache_dict.get("qualidade", "{}"))
except: pass

vol_hoje = safe_to_numeric(cache_dict.get("vol_hoje", 0))
estoque_total = safe_to_numeric(cache_dict.get("estoque_total", 0))
ultima_att = cache_dict.get("ultima_atualizacao", "Desconhecida")
observacoes = cache_dict.get("observacoes", "")

prod_ms1 = safe_to_numeric(qualidade.get("MS1", {}).get("producao", 0))
prod_ms2 = safe_to_numeric(qualidade.get("MS2", {}).get("producao", 0))
prod_hoje = prod_ms1 + prod_ms2

# ==============================================================================
# 🧠 CÁLCULO DINÂMICO DE PREVISÃO (AJUSTADO PARA O FUSO DO BRASIL UTC-3)
# ==============================================================================
# Subtrai 3 horas do relógio do servidor para igualar à hora do Brasil
agora = datetime.utcnow() - timedelta(hours=3)

# 1. Previsão de Produção
horas_passadas_prod = max(0.1, agora.hour + (agora.minute / 60.0))
prev_prod = (prod_hoje / horas_passadas_prod) * 24

# 2. Previsão de Expedição
dia_semana = agora.weekday()
horas_produtivas = 0.0
for h in range(agora.hour, 24):
    fracao = 1.0 if h > agora.hour else (1.0 - (agora.minute / 60.0))
    fator = 6.25 / 8.0
    if 0 <= h < 8 and dia_semana in (0, 6): # Regra FDS
        fator = 0.0
    horas_produtivas += fracao * fator

cap_maxima_restante = horas_produtivas * 500.0
vol_patio = 0.0
if dados_patio:
    vol_patio += dados_patio.get("PR", {}).get("peso", 0.0)
    vol_patio += dados_patio.get("00", {}).get("peso", 0.0)
    vol_patio += dados_patio.get("01", {}).get("peso", 0.0)
    vol_patio += dados_patio.get("FC", {}).get("peso", 0.0)

projecao_real = min(cap_maxima_restante, vol_patio)
prev_carr = vol_hoje + projecao_real

# ==============================================================================
# CABEÇALHO COM ÚLTIMA ATUALIZAÇÃO E OBSERVAÇÕES
# ==============================================================================
col_title, col_ref = st.columns([2.5, 1])
with col_title:
    st.markdown("### 🚛 A.L.O.V.E. Mobile")
    st.caption(f"Última Atualização: **{ultima_att}**")
with col_ref:
    st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Atualizar"):
        st.cache_data.clear()
        st.rerun()

# Lógica das Cores da Observação
if observacoes and observacoes.strip() != "" and observacoes.strip() != "None":
    if "Normal" in observacoes:
        cor_bg, cor_border, cor_txt = "#0d2417", "#00D672", "#00D672"
    else:
        cor_bg, cor_border, cor_txt = "#2b1111", "#E74C3C", "#ff9999"
        
    st.markdown(f"""
        <div style="background-color: {cor_bg}; border-left: 4px solid {cor_border}; padding: 12px; margin-bottom: 15px; border-radius: 4px;">
            <h4 style="color: {cor_border}; margin: 0 0 6px 0; font-size: 14px;">📋 Observações Operacionais</h4>
            <div style="color: {cor_txt}; font-size: 13px; font-weight: 500; white-space: pre-wrap;">{observacoes}</div>
        </div>
    """, unsafe_allow_html=True)

st.write("") 

tab_carretas, tab_prod_exp, tab_frota_glp = st.tabs([
    "🚚 Carretas",
    "🏭 Prod & Exp",
    "⛽ Frota & GLP"
])

# ==============================================================================
# ABA 1: CARRETAS
# ==============================================================================
with tab_carretas:
    st.subheader("Blocos do Pátio")
    if dados_patio:
        blocos = [
            ("Programado", dados_patio.get('PR', {}).get('veiculos', 0), dados_patio.get('PR', {}).get('peso', 0.0), "#6c757d"),
            ("Checklist", dados_patio.get('00', {}).get('veiculos', 0), dados_patio.get('00', {}).get('peso', 0.0), "#ffc107"),
            ("Apoio", dados_patio.get('01', {}).get('veiculos', 0), dados_patio.get('01', {}).get('peso', 0.0), "#dc3545"),
            ("Fila", dados_patio.get('FC', {}).get('veiculos', 0), dados_patio.get('FC', {}).get('peso', 0.0), "#0d6efd"),
            ("Termo", dados_patio.get('TR', {}).get('veiculos', 0), dados_patio.get('TR', {}).get('peso', 0.0), "#198754"),
        ]
        for nome, qtd, ton_real, cor in blocos:
            st.markdown(f"""
                <div class="card-status" style="border-left-color: {cor};">
                    <div style="font-weight:bold; font-size:1.1rem; color: #fff; margin-bottom: 8px;">
                        {nome}
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size: 1.0rem;">
                        <span style="color: #a0a0a0;">Qtd: <b style="color: {cor};">{int(qtd)}</b></span>
                        <span style="color: #a0a0a0;">Ton: <b style="color: {cor};">{ton_real:,.1f} t</b></span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Aba Cache_Painel (dados_patio) indisponível.")

# ==============================================================================
# ABA 2: PRODUÇÃO, EXPEDIÇÃO E QUALIDADE
# ==============================================================================
with tab_prod_exp:
    st.subheader("Expedição & Produção Diária (t)")
    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Produção Hoje", f"{prod_hoje:,.1f} t")
        st.markdown(f"<div style='color: #3498DB; font-weight: 600; font-size: 0.95rem; margin-top: -15px;'>Prev: {prev_prod:,.1f} t</div>", unsafe_allow_html=True)
    with c2:
        st.metric("Volume Expedido", f"{vol_hoje:,.1f} t")
        st.markdown(f"<div style='color: #3498DB; font-weight: 600; font-size: 0.95rem; margin-top: -15px;'>Prev: {prev_carr:,.1f} t</div>", unsafe_allow_html=True)
        
    st.write("")
    st.metric("Estoque Total", f"{estoque_total:,.1f} t")
    
    df_comp = pd.DataFrame({
        "Métrica": ["Produção", "Expedição", "Estoque Total"],
        "Toneladas": [prod_hoje, vol_hoje, estoque_total]
    })
    
    max_ton = max(df_comp["Toneladas"]) if not df_comp.empty else 100
    bars = alt.Chart(df_comp).mark_bar(cornerRadius=4).encode(
        x=alt.X("Métrica:N", sort=None, title=""),
        y=alt.Y("Toneladas:Q", title="Toneladas", scale=alt.Scale(domain=[0, max_ton * 1.25])),
        color=alt.Color("Métrica:N", scale=alt.Scale(range=["#20c997", "#0d6efd", "#ffc107"]), legend=None)
    )
    text = bars.mark_text(align='center', baseline='bottom', dy=-5, color='white').encode(
        text=alt.Text('Toneladas:Q', format=',.1f')
    )
    chart_comp = (bars + text).properties(height=280)
    st.altair_chart(chart_comp, use_container_width=True)

    st.write("---")
    st.subheader("Indicadores de Qualidade")
    if qualidade:
        for maq in ["MS1", "MS2"]:
            st.markdown(f"**{maq}** (MAT: {qualidade.get(maq, {}).get('material', '--')})")
            q_suj = qualidade.get(maq, {}).get('sujidade', 0.0)
            q_visc = qualidade.get(maq, {}).get('viscosidade', 0.0)
            q_teor = qualidade.get(maq, {}).get('teor', 0.0)
            
            c_q1, c_q2, c_q3 = st.columns(3)
            with c_q1:
                st.markdown(f"<div style='font-size: 1rem; color: #a0a0a0;'>Sujidade</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 1.4rem;'>{q_suj:.2f}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 0.75rem; color: #6c757d; margin-top: -5px;'>Máx: 2.5</div>", unsafe_allow_html=True)
            with c_q2:
                st.markdown(f"<div style='font-size: 1rem; color: #a0a0a0;'>Viscosidade</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 1.4rem;'>{q_visc:,.0f}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 0.75rem; color: #6c757d; margin-top: -5px;'>Mín: 650</div>", unsafe_allow_html=True)
            with c_q3:
                st.markdown(f"<div style='font-size: 1rem; color: #a0a0a0;'>Teor Seco</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 1.4rem;'>{q_teor:.2f}%</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 0.75rem; color: #6c757d; margin-top: -5px;'>Mín: 88.5%</div>", unsafe_allow_html=True)
            st.write("")
    else:
        st.info("Aba Cache_Painel (qualidade) indisponível.")

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
