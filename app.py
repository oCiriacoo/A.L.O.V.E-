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

# ==============================================================================
# 🎨 IDENTIDADE VISUAL (NAVY BLUE - PÁGINA ÚNICA)
# ==============================================================================
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
        /* Divisórias Customizadas */
        hr {
            border: 0;
            height: 1px;
            background: #1c2b42;
            margin: 25px 0;
        }
        /* Cards de Métrica Customizados */
        .metric-card {
            background-color: #111c2e;
            border: 1px solid #1c2b42;
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            margin-bottom: 10px;
        }
        .metric-title { color: #94a3b8; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
        .metric-value { color: #ffffff; font-size: 1.8rem; font-weight: 900; line-height: 1.2; }
        .metric-sub { color: #3498DB; font-size: 0.75rem; font-weight: 700; }
        
        /* Grid do Pátio */
        .patio-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
        .card-patio {
            background-color: #111c2e;
            border-radius: 10px;
            padding: 12px;
            border-left: 4px solid;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .card-patio-title { font-weight: 800; font-size: 1rem; color: #ffffff; margin-bottom: 4px; }
        .card-patio-qtd { font-size: 1.4rem; font-weight: 900; }
        .card-patio-ton { font-size: 0.85rem; color: #94a3b8; font-weight: 600; }
        
        /* Tags Frota */
        .tag-box {
            display: inline-block;
            padding: 6px 12px;
            margin: 4px;
            border-radius: 8px;
            font-weight: 800;
            font-size: 0.85rem;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .tag-op { background-color: #00D672; color: #0a101d; }
        .tag-standby { background-color: #E74C3C; color: #ffffff; }
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
            s_val = s_val.replace(".", "").replace(",", ".")
        return float(s_val)
    except Exception:
        return 0.0

# ==============================================================================
# 🔥 LEITURA DOS DADOS DA NUVEM (CACHE_PAINEL)
# ==============================================================================
df_cache = carregar_dados("Cache_Painel", cabecalho=0)
cache_dict = {str(row.iloc[0]).strip(): str(row.iloc[1]).strip() for _, row in df_cache.iterrows()} if not df_cache.empty else {}

dados_patio = {}
qualidade = {}
dados_turnos = {}

try: dados_patio = json.loads(cache_dict.get("dados_patio", "{}"))
except: pass
try: qualidade = json.loads(cache_dict.get("qualidade", "{}"))
except: pass
try: dados_turnos = json.loads(cache_dict.get("dados_turnos", "{}"))
except: pass

vol_hoje = safe_to_numeric(cache_dict.get("vol_hoje", 0))
estoque_total = safe_to_numeric(cache_dict.get("estoque_total", 0))
ultima_att = cache_dict.get("ultima_atualizacao", "Desconhecida")
observacoes = cache_dict.get("observacoes", "")

prod_ms1 = safe_to_numeric(qualidade.get("MS1", {}).get("producao", 0))
prod_ms2 = safe_to_numeric(qualidade.get("MS2", {}).get("producao", 0))
prod_hoje = prod_ms1 + prod_ms2

# ==============================================================================
# 🧠 CÁLCULO DINÂMICO DE PREVISÃO (UTC-3)
# ==============================================================================
agora = datetime.utcnow() - timedelta(hours=3)
horas_passadas_prod = max(0.1, agora.hour + (agora.minute / 60.0))
prev_prod = (prod_hoje / horas_passadas_prod) * 24

horas_produtivas = sum((1.0 if h > agora.hour else (1.0 - (agora.minute / 60.0))) * (0.0 if 0 <= h < 8 and agora.weekday() in (0, 6) else (6.25 / 8.0)) for h in range(agora.hour, 24))
cap_maxima_restante = horas_produtivas * 500.0
vol_patio = sum(dados_patio.get(k, {}).get("peso", 0.0) for k in ["PR", "00", "01", "FC"]) if dados_patio else 0.0
prev_carr = vol_hoje + min(cap_maxima_restante, vol_patio)

# ==============================================================================
# CABEÇALHO COM ÚLTIMA ATUALIZAÇÃO E OBSERVAÇÕES
# ==============================================================================
col_title, col_ref = st.columns([3, 1])
with col_title:
    st.markdown("<h3 style='margin:0; color:#3498DB;'>🚛 A.L.O.V.E. Mobile</h3>", unsafe_allow_html=True)
    st.caption(f"Atualizado: **{ultima_att}**")
with col_ref:
    st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Atualizar"):
        st.cache_data.clear()
        st.rerun()

if observacoes and observacoes.strip() not in ["", "None"]:
    cor_bg, cor_border, cor_txt = ("#0d2417", "#00D672", "#00D672") if "Normal" in observacoes else ("#2b1111", "#E74C3C", "#ff9999")
    st.markdown(f"""
        <div style="background-color: {cor_bg}; border-left: 4px solid {cor_border}; padding: 12px; margin: 10px 0; border-radius: 6px;">
            <h4 style="color: {cor_border}; margin: 0 0 6px 0; font-size: 13px;">📋 Observações Operacionais</h4>
            <div style="color: {cor_txt}; font-size: 12px; font-weight: 600; white-space: pre-wrap;">{observacoes}</div>
        </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# SESSÃO 1: CARRETAS (PÁTIO)
# ==============================================================================
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<h4 style='color:#3498DB; margin-bottom: 15px;'>🚚 Status do Pátio</h4>", unsafe_allow_html=True)

if dados_patio:
    blocos = [
        ("🚙 Programado", "PR", "#94A3B8"),
        ("📋 Checklist", "00", "#E5B800"),
        ("🚛 Apoio", "01", "#E67E22"),
        ("✅ Fila", "FC", "#00D672"),
        ("📄 Termo", "TR", "#3498DB"),
    ]
    
    html_cards = '<div class="patio-grid">'
    for titulo, chave, cor in blocos:
        qtd = dados_patio.get(chave, {}).get("veiculos", 0)
        peso = dados_patio.get(chave, {}).get("peso", 0.0)
        html_cards += f'<div class="card-patio" style="border-color: {cor};">'
        html_cards += f'<div class="card-patio-title" style="color: {cor};">{titulo}</div>'
        html_cards += f'<div class="card-patio-qtd" style="color: #ffffff;">{int(qtd)} <span style="font-size:0.9rem; color:#94a3b8; font-weight:600;">Veíc</span></div>'
        html_cards += f'<div class="card-patio-ton">{peso:,.0f} t</div>'
        html_cards += '</div>'
    html_cards += '</div>'
    st.markdown(html_cards, unsafe_allow_html=True)
else:
    st.info("Dados do pátio indisponíveis na nuvem.")

# ==============================================================================
# SESSÃO 2: LOGÍSTICA E PRODUÇÃO
# ==============================================================================
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<h4 style='color:#3498DB; margin-bottom: 15px;'>🏭 Logística & Produção</h4>", unsafe_allow_html=True)

# 1. Cards Superiores
st.markdown(f"""
    <div style="display: flex; gap: 10px; margin-bottom: 10px;">
        <div class="metric-card" style="flex: 1; border-bottom: 3px solid #00D672;">
            <div class="metric-title">🚛 Expedição</div>
            <div class="metric-value">{vol_hoje:,.0f} <span style="font-size:1rem;">t</span></div>
            <div class="metric-sub">Prev: {prev_carr:,.0f} t</div>
        </div>
        <div class="metric-card" style="flex: 1; border-bottom: 3px solid #3498DB;">
            <div class="metric-title">🏭 Produção</div>
            <div class="metric-value">{prod_hoje:,.0f} <span style="font-size:1rem;">t</span></div>
            <div class="metric-sub">Prev: {prev_prod:,.0f} t</div>
        </div>
    </div>
    <div class="metric-card" style="border-bottom: 3px solid #E5B800; margin-bottom: 5px;">
        <div class="metric-title">📦 Estoque Total</div>
        <div class="metric-value">{estoque_total:,.0f} <span style="font-size:1rem;">t</span></div>
    </div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# 🔥 GRÁFICO DE TURNOS (AGORA É CLICÁVEL / EXPANSÍVEL)
# -------------------------------------------------------------------------
if dados_turnos and "turnos" in dados_turnos:
    # Cria a aba clicável (Expander)
    with st.expander("👉 CLIQUE AQUI: DETALHAMENTO DE EXPEDIÇÃO POR TURNO"):
        turnos_list = dados_turnos["turnos"]
        ativo_key = dados_turnos.get("ativo_key")
        
        data_grafico = []
        for t in turnos_list:
            data_grafico.append({
                "Turno": f"{t['letra']} ({t['horario'].split('-')[0].strip()})",
                "Toneladas": t["vol"],
                "Cor": "#FF9F1C" if t["key"] == ativo_key else "#3498DB"
            })
            
        df_vol = pd.DataFrame(data_grafico)
        max_vol = max(df_vol["Toneladas"]) if not df_vol.empty and max(df_vol["Toneladas"]) > 0 else 100
        
        bars = alt.Chart(df_vol).mark_bar(cornerRadius=6).encode(
            x=alt.X("Turno:N", sort=None, axis=alt.Axis(labelAngle=0, labelColor="#94a3b8", title=None)),
            y=alt.Y("Toneladas:Q", scale=alt.Scale(domain=[0, max_vol * 1.3]), axis=None),
            color=alt.Color("Cor:N", scale=None) 
        )
        
        text = bars.mark_text(align='center', baseline='bottom', dy=-5, color='white', fontSize=14, fontWeight='bold').encode(
            text=alt.Text('Toneladas:Q', format=',.0f')
        )
        
        chart_vol = (bars + text).properties(height=220, background="transparent")
        st.altair_chart(chart_vol, use_container_width=True)
else:
    st.info("Aguardando o A.L.O.V.E Core calcular e enviar a escala de turnos.")

# -------------------------------------------------------------------------
# 3. Qualidade
# -------------------------------------------------------------------------
st.markdown("<h5 style='color:#ffffff; margin-top:20px; margin-bottom:10px;'>⚙️ Qualidade MS1 & MS2</h5>", unsafe_allow_html=True)
if qualidade:
    for maq in ["MS1", "MS2"]:
        q_suj = qualidade.get(maq, {}).get('sujidade', 0.0)
        q_visc = qualidade.get(maq, {}).get('viscosidade', 0.0)
        q_teor = qualidade.get(maq, {}).get('teor', 0.0)
        
        st.markdown(f"""
            <div style="background-color: #111c2e; border: 1px solid #1c2b42; border-radius: 8px; padding: 10px; margin-bottom: 10px;">
                <div style="color:#3498DB; font-weight:800; margin-bottom: 8px;">{maq} <span style="color:#FF9F1C; font-size:0.85rem; float:right;">MAT: {qualidade.get(maq, {}).get('material', '--')}</span></div>
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div>
                        <div style="font-size:0.75rem; color:#94a3b8;">Sujidade</div>
                        <div style="font-size:1.1rem; font-weight:bold; color:#00D672;">{q_suj:.2f}</div>
                    </div>
                    <div>
                        <div style="font-size:0.75rem; color:#94a3b8;">Viscosidade</div>
                        <div style="font-size:1.1rem; font-weight:bold; color:#00D672;">{q_visc:,.0f}</div>
                    </div>
                    <div>
                        <div style="font-size:0.75rem; color:#94a3b8;">Teor Seco</div>
                        <div style="font-size:1.1rem; font-weight:bold; color:#00D672;">{q_teor:.2f}%</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# SESSÃO 3: FROTA E GLP
# ==============================================================================
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<h4 style='color:#3498DB; margin-bottom: 15px;'>🚜 Alocação de Equipamentos</h4>", unsafe_allow_html=True)

df_frota = carregar_dados("Rodizio_Frota")

if not df_frota.empty:
    col_turno = "TURNO_JANELA" if "TURNO_JANELA" in df_frota.columns else df_frota.columns[0]
    turnos = df_frota[col_turno].dropna().unique().tolist()
    hora_atual = datetime.now().hour
    idx_sug = next((i for i, t in enumerate(turnos) if ("00:00" in str(t) and 0 <= hora_atual < 8) or ("08:00" in str(t) and 8 <= hora_atual < 16) or ("16:00" in str(t) and 16 <= hora_atual <= 23)), 0)
    
    turno_sel = st.selectbox("Selecione o Turno:", turnos, index=idx_sug)
    df_f = df_frota[df_frota[col_turno] == turno_sel]

    carr_op = df_f[(df_f["POSTO"].astype(str).str.contains("CARREG", case=False)) & (df_f["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]["EQUIPAMENTO"].tolist()
    linha_op = df_f[(df_f["POSTO"].astype(str).str.contains("LINHA", case=False)) & (df_f["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]["EQUIPAMENTO"].tolist()
    paradas = df_f[df_f["STATUS_RODIZIO"].astype(str).str.contains("STAND", case=False)]["EQUIPAMENTO"].tolist()

    st.markdown("**🟢 Carregamento:**")
    st.markdown(" ".join([f'<span class="tag-box tag-op">{t}</span>' for t in carr_op]) if carr_op else "<span style='color:gray; font-size:0.85rem;'>Nenhum</span>", unsafe_allow_html=True)

    st.markdown("<br>**🟢 Abastecimento de Linha:**", unsafe_allow_html=True)
    st.markdown(" ".join([f'<span class="tag-box tag-op">{t}</span>' for t in linha_op]) if linha_op else "<span style='color:gray; font-size:0.85rem;'>Nenhum</span>", unsafe_allow_html=True)

    st.markdown("<br>**🔴 Stand-by / Paradas:**", unsafe_allow_html=True)
    st.markdown(" ".join([f'<span class="tag-box tag-standby">{t}</span>' for t in paradas]) if paradas else "<span style='color:gray; font-size:0.85rem;'>Nenhum</span>", unsafe_allow_html=True)
else:
    st.info("Planilha Rodizio_Frota indisponível.")

st.markdown("<br><center><span style='color:#94a3b8; font-size: 0.8rem;'>Logística MI | A.L.O.V.E Core Dashboard</span></center>", unsafe_allow_html=True)
