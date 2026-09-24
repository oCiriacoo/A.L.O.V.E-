import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import altair as alt
import json
import requests
import csv
from io import StringIO

st.set_page_config(
    page_title="A.L.O.V.E. Mobile",
    page_icon="🚛",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# 🎨 IDENTIDADE VISUAL NAVY BLUE (ESTILO CARDS INTERATIVOS)
# ==============================================================================
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
        /* Card Mestre Topo */
        .master-metric-box {
            background-color: #111c2e;
            border-radius: 12px;
            padding: 14px 18px;
            margin-bottom: 4px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            border-left: 6px solid #3498DB;
        }
        .master-metric-title { color: #94a3b8; font-size: 0.82rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }
        .master-metric-val { color: #ffffff; font-size: 1.8rem; font-weight: 900; line-height: 1.2; margin: 2px 0; }
        .master-metric-sub { font-size: 0.82rem; font-weight: 700; }

        /* Grid do Pátio Retrátil */
        .patio-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-top: 10px; }
        .card-patio-sub { background-color: #0a101d; border-radius: 8px; padding: 10px; border-left: 4px solid; border: 1px solid #1c2b42; }
        .card-patio-title { font-weight: 800; font-size: 0.9rem; margin-bottom: 2px; }
        .card-patio-qtd { font-size: 1.3rem; font-weight: 900; color: #ffffff; }
        .card-patio-ton { font-size: 0.8rem; color: #94a3b8; font-weight: 600; }

        /* Estilização dos Expanders nativos */
        div[data-testid="stExpander"] { border: 1px solid #1c2b42 !important; background-color: #111c2e !important; border-radius: 10px !important; margin-bottom: 16px !important; }
        div[data-testid="stExpander"] details summary { padding: 8px 12px !important; font-weight: bold !important; color: #38bdf8 !important; }

        /* Tags Frota */
        .tag-box { display: inline-block; padding: 6px 12px; margin: 4px; border-radius: 8px; font-weight: 800; font-size: 0.85rem; text-align: center; }
        .tag-op { background-color: #00D672; color: #0a101d; }
        .tag-standby { background-color: #E74C3C; color: #ffffff; }
        .tag-talha { background-color: #F39C12; color: #0a101d; }
    </style>
""", unsafe_allow_html=True)

SHEET_ID = "10FluiIwlynIlPDA74QI8mpHSIrAc-62H1hZNRBsvfCA"

@st.cache_data(ttl=30)
def carregar_dados_nuvem(worksheet_name: str, cabecalho=0):
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
    try: return float(str(val).strip().replace(".", "").replace(",", "."))
    except: return 0.0

def descobrir_letras_turnos(data_alvo):
    data_referencia = datetime(2026, 9, 22).date()
    dias_passados = (data_alvo - data_referencia).days
    turnos = {"08_16": "C", "16_00": "B", "madrugada": "D"}
    for letra, dia in [("C", (0 + dias_passados) % 6), ("B", (2 + dias_passados) % 6), ("A", (4 + dias_passados) % 6)]:
        if dia in [0, 1]: turnos["08_16"] = letra
        elif dia in [2, 3]: turnos["16_00"] = letra
    return turnos

@st.cache_data(ttl=60)
def buscar_dados_turnos_direto():
    """ O Mobile calcula os turnos autônomamente sem depender do Core! """
    agora_br = datetime.utcnow() - timedelta(hours=3)
    hoje_date = agora_br.date()
    turno_d_ativo = agora_br.weekday() not in (0, 6)
    letras = descobrir_letras_turnos(hoje_date)
    
    if agora_br.hour < 8: ativo_key = "t1" if turno_d_ativo else None
    elif agora_br.hour < 16: ativo_key = "t2"
    else: ativo_key = "t3"

    try:
        url_csv = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
        resp = requests.get(url_csv, timeout=8)
        resp.encoding = 'utf-8'
        linhas = list(csv.reader(StringIO(resp.text)))

        corte_08 = 0.0
        corte_16 = 0.0
        vol_atual = 0.0
        hora_08 = agora_br.replace(hour=8, minute=0, second=0, microsecond=0)
        hora_16 = agora_br.replace(hour=16, minute=0, second=0, microsecond=0)

        for row in reversed(linhas[1:]):
            if len(row) > 3:
                try:
                    dt_row = datetime.strptime(row[0].strip(), "%d/%m/%Y %H:%M:%S")
                    vol_linha = float(str(row[3]).replace(".", "").replace(",", "."))
                    if vol_atual == 0.0:
                        vol_atual = vol_linha
                    if corte_16 == 0.0 and dt_row <= hora_16 and dt_row.date() == hoje_date:
                        corte_16 = vol_linha
                    if corte_08 == 0.0 and dt_row <= hora_08 and dt_row.date() == hoje_date:
                        corte_08 = vol_linha
                except: continue

        vol_t1 = corte_08 if (corte_08 > 0 and turno_d_ativo) else 0.0
        vol_t2 = max(0.0, corte_16 - corte_08) if agora_br.hour >= 16 else (max(0.0, vol_atual - corte_08) if agora_br.hour >= 8 else 0.0)
        vol_t3 = max(0.0, vol_atual - corte_16) if agora_br.hour >= 16 else 0.0

        turnos_exibir = []
        if turno_d_ativo: turnos_exibir.append({"key": "t1", "letra": f"Turno {letras['madrugada']}", "vol": vol_t1, "horario": "00h - 08h"})
        turnos_exibir.append({"key": "t2", "letra": f"Turno {letras['08_16']}", "vol": vol_t2, "horario": "08h - 16h"})
        turnos_exibir.append({"key": "t3", "letra": f"Turno {letras['16_00']}", "vol": vol_t3, "horario": "16h - 00h"})
        return {"ativo_key": ativo_key, "turnos": turnos_exibir}
    except Exception: return None

# ==============================================================================
# 🔥 RESGATE DOS DADOS DA NUVEM & CÁLCULOS
# ==============================================================================
df_cache = carregar_dados_nuvem("Cache_Painel", cabecalho=0)
cache_dict = {str(row.iloc[0]).strip(): str(row.iloc[1]).strip() for _, row in df_cache.iterrows()} if not df_cache.empty else {}

dados_patio = json.loads(cache_dict.get("dados_patio", "{}")) if cache_dict.get("dados_patio") else {}
qualidade = json.loads(cache_dict.get("qualidade", "{}")) if cache_dict.get("qualidade") else {}
dados_turnos = buscar_dados_turnos_direto()

vol_hoje = safe_to_numeric(cache_dict.get("vol_hoje", 0))
estoque_total = safe_to_numeric(cache_dict.get("estoque_total", 0))
ultima_att = cache_dict.get("ultima_atualizacao", "Desconhecida")
observacoes = cache_dict.get("observacoes", "")

prod_ms1 = safe_to_numeric(qualidade.get("MS1", {}).get("producao", 0))
prod_ms2 = safe_to_numeric(qualidade.get("MS2", {}).get("producao", 0))
prod_hoje = prod_ms1 + prod_ms2

agora = datetime.utcnow() - timedelta(hours=3)
horas_passadas_prod = max(0.1, agora.hour + (agora.minute / 60.0))
prev_prod = (prod_hoje / horas_passadas_prod) * 24

horas_produtivas = sum((1.0 if h > agora.hour else (1.0 - (agora.minute / 60.0))) * (0.0 if 0 <= h < 8 and agora.weekday() in (0, 6) else (6.25 / 8.0)) for h in range(agora.hour, 24))
cap_maxima_restante = horas_produtivas * 500.0

# Regras do Pátio (PR fica de fora dos disponíveis e do físico)
vol_patio_disponivel = sum(dados_patio.get(k, {}).get("peso", 0.0) for k in ["00", "01", "FC"]) if dados_patio else 0.0
total_veiculos_fisicos = sum(dados_patio.get(k, {}).get("veiculos", 0) for k in ["00", "01", "FC", "TR"]) if dados_patio else 0
prev_carr = vol_hoje + min(cap_maxima_restante, vol_patio_disponivel)

# Carga de Equipamentos (Frota)
df_frota = carregar_dados_nuvem("Rodizio_Frota")
equip_em_uso = 0
equip_standby = 0
df_f_atual = pd.DataFrame()

if not df_frota.empty:
    col_turno = "TURNO_JANELA" if "TURNO_JANELA" in df_frota.columns else df_frota.columns[0]
    turnos = df_frota[col_turno].dropna().unique().tolist()
    hora_atual = agora.hour
    idx_sug = next((i for i, t in enumerate(turnos) if ("00:00" in str(t) and 0 <= hora_atual < 8) or ("08:00" in str(t) and 8 <= hora_atual < 16) or ("16:00" in str(t) and 16 <= hora_atual <= 23)), 0)
    turno_atual_str = turnos[idx_sug] if turnos else ""
    df_f_atual = df_frota[df_frota[col_turno] == turno_atual_str]
    equip_em_uso = len(df_f_atual[df_f_atual["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False)])
    equip_standby = len(df_f_atual[df_f_atual["STATUS_RODIZIO"].astype(str).str.contains("STAND", case=False)])

# ==============================================================================
# CABEÇALHO SUPERIOR
# ==============================================================================
col_title, col_ref = st.columns([3, 1])
with col_title:
    st.markdown("<h3 style='margin:0; color:#3498DB;'>🚛 A.L.O.V.E. Mobile</h3>", unsafe_allow_html=True)
    st.caption(f"Sincronizado: **{ultima_att}**")
with col_ref:
    st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Atualizar"):
        st.cache_data.clear()
        st.rerun()

if observacoes and observacoes.strip() not in ["", "None"]:
    cor_bg, cor_border, cor_txt = ("#0d2417", "#00D672", "#00D672") if "Normal" in observacoes else ("#2b1111", "#E74C3C", "#ff9999")
    st.markdown(f"""
        <div style="background-color: {cor_bg}; border-left: 4px solid {cor_border}; padding: 10px 14px; margin: 10px 0; border-radius: 6px;">
            <div style="color: {cor_border}; font-size: 11px; font-weight: 800; text-transform: uppercase;">📋 Observação Operacional</div>
            <div style="color: {cor_txt}; font-size: 12px; font-weight: 600; white-space: pre-wrap;">{observacoes}</div>
        </div>
    """, unsafe_allow_html=True)

st.write("")

# ==============================================================================
# 📦 BLOCO 1: PÁTIO DE VEÍCULOS & CARGA DISPONÍVEL (CLICÁVEL)
# ==============================================================================
st.markdown(f"""
    <div class="master-metric-box" style="border-left-color: #38bdf8;">
        <div class="master-metric-title">🚛 Pátio da Fábrica (Tempo Real)</div>
        <div class="master-metric-val">{total_veiculos_fisicos} <span style="font-size:1.1rem; color:#94a3b8;">Veículos Físicos</span></div>
        <div class="master-metric-sub" style="color: #38bdf8;">Disponível p/ Carregar: {vol_patio_disponivel:,.0f} t</div>
    </div>
""", unsafe_allow_html=True)

with st.expander("🔍 Toque para ver o Pátio detalhado por Status"):
    if dados_patio:
        blocos_patio = [
            ("🚙 Programado", "PR", "#94A3B8"),
            ("📋 Checklist", "00", "#E5B800"),
            ("🚛 Apoio", "01", "#E67E22"),
            ("✅ Fila", "FC", "#00D672"),
            ("📄 Termo SAP", "TR", "#3498DB"),
        ]
        # Correção definitiva para o HTML (evita a fuga de formatação de código no Streamlit)
        html_p = '<div class="patio-grid">'
        for tit, chv, cor in blocos_patio:
            v_qtd = dados_patio.get(chv, {}).get("veiculos", 0)
            v_ton = dados_patio.get(chv, {}).get("peso", 0.0)
            html_p += f'<div class="card-patio-sub" style="border-left: 4px solid {cor};">'
            html_p += f'<div class="card-patio-title" style="color: {cor};">{tit}</div>'
            html_p += f'<div class="card-patio-qtd">{int(v_qtd)} <span style="font-size:0.75rem; color:#94a3b8;">veíc</span></div>'
            html_p += f'<div class="card-patio-ton">{v_ton:,.0f} t</div>'
            html_p += '</div>'
        html_p += '</div>'
        st.markdown(html_p, unsafe_allow_html=True)
    else:
        st.caption("Sem dados de pátio disponíveis.")

# ==============================================================================
# 🏭 BLOCO 2: PRODUÇÃO DO DIA & QUALIDADE (CLICÁVEL)
# ==============================================================================
st.markdown(f"""
    <div class="master-metric-box" style="border-left-color: #E5B800;">
        <div class="master-metric-title">🏭 Produção de Celulose (Hoje)</div>
        <div class="master-metric-val">{prod_hoje:,.0f} <span style="font-size:1.1rem; color:#94a3b8;">TON</span></div>
        <div class="master-metric-sub" style="color: #E5B800;">Previsão de Fechamento: {prev_prod:,.0f} t</div>
    </div>
""", unsafe_allow_html=True)

with st.expander("🔍 Toque para ver Produção por Máquina & Qualidade"):
    if qualidade:
        for maq in ["MS1", "MS2"]:
            p_maq = safe_to_numeric(qualidade.get(maq, {}).get("producao", 0))
            mat_maq = qualidade.get(maq, {}).get("material", "--")
            q_suj = qualidade.get(maq, {}).get('sujidade', 0.0)
            q_visc = qualidade.get(maq, {}).get('viscosidade', 0.0)
            q_teor = qualidade.get(maq, {}).get('teor', 0.0)
            
            st.markdown(f"""
                <div style="background-color: #0a101d; border: 1px solid #1c2b42; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="color:#ffffff; font-weight:800; font-size:1rem;">⚙️ {maq}</span>
                        <span style="color:#FF9F1C; font-weight:800; font-size:0.85rem;">📦 MAT: {mat_maq}</span>
                        <span style="color:#3498DB; font-weight:900; font-size:1rem;">{p_maq:,.0f} t</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; text-align: center; border-top: 1px solid #1c2b42; padding-top: 8px;">
                        <div>
                            <div style="font-size:0.75rem; color:#94a3b8;">Sujidade (≤2.5)</div>
                            <div style="font-size:1.05rem; font-weight:bold; color:{'#00D672' if q_suj<=2.5 else '#E74C3C'};">{q_suj:.2f}</div>
                        </div>
                        <div>
                            <div style="font-size:0.75rem; color:#94a3b8;">Viscosidade (≥650)</div>
                            <div style="font-size:1.05rem; font-weight:bold; color:{'#00D672' if q_visc>=650 else '#E74C3C'};">{q_visc:,.0f}</div>
                        </div>
                        <div>
                            <div style="font-size:0.75rem; color:#94a3b8;">Teor Seco (≥88.5)</div>
                            <div style="font-size:1.05rem; font-weight:bold; color:{'#00D672' if q_teor>=88.5 else '#E74C3C'};">{q_teor:.2f}%</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("Sem dados de máquinas disponíveis.")

# ==============================================================================
# 🚚 BLOCO 3: EXPEDIÇÃO DO DIA & TURNOS (CLICÁVEL)
# ==============================================================================
st.markdown(f"""
    <div class="master-metric-box" style="border-left-color: #00D672;">
        <div class="master-metric-title">🚛 Expedição Realizada (Hoje)</div>
        <div class="master-metric-val">{vol_hoje:,.0f} <span style="font-size:1.1rem; color:#94a3b8;">TON</span></div>
        <div class="master-metric-sub" style="color: #00D672;">Previsão de Fechamento: {prev_carr:,.0f} t</div>
    </div>
""", unsafe_allow_html=True)

with st.expander("🔍 Toque para ver Expedição Separada por Turno"):
    if dados_turnos and "turnos" in dados_turnos:
        turnos_list = dados_turnos["turnos"]
        ativo_key = dados_turnos.get("ativo_key")

        # HTML seguro e em linha para evitar a fuga do interpretador Markdown
        html_t_cards = '<div style="display:flex; gap:6px; margin-bottom:12px;">'
        for t in turnos_list:
            is_atv = (t["key"] == ativo_key)
            cor_b = "#FF9F1C" if is_atv else "#1c2b42"
            cor_txt = "#FF9F1C" if is_atv else "#ffffff"
            sub_txt = f"{t['horario']} (ATIVO)" if is_atv else t['horario']
            html_t_cards += f'<div style="flex:1; background-color:#0a101d; border:1.5px solid {cor_b}; border-radius:8px; padding:8px; text-align:center;">'
            html_t_cards += f'<div style="font-size:0.75rem; font-weight:800; color:{cor_txt};">{t["letra"]}</div>'
            html_t_cards += f'<div style="font-size:1.1rem; font-weight:900; color:#ffffff;">{t["vol"]:,.0f} t</div>'
            html_t_cards += f'<div style="font-size:0.65rem; color:#94a3b8;">{sub_txt}</div>'
            html_t_cards += '</div>'
        html_t_cards += '</div>'
        st.markdown(html_t_cards, unsafe_allow_html=True)

        # Gráfico
        data_grafico = [{"Turno": t['letra'], "Toneladas": t["vol"], "Cor": "#FF9F1C" if t["key"] == ativo_key else "#3498DB"} for t in turnos_list]
        df_vol = pd.DataFrame(data_grafico)
        max_vol = max(df_vol["Toneladas"]) if not df_vol.empty and max(df_vol["Toneladas"]) > 0 else 100
        bars = alt.Chart(df_vol).mark_bar(cornerRadius=6).encode(
            x=alt.X("Turno:N", sort=None, axis=alt.Axis(labelAngle=0, labelColor="#ffffff", title=None)),
            y=alt.Y("Toneladas:Q", scale=alt.Scale(domain=[0, max_vol * 1.3]), axis=None),
            color=alt.Color("Cor:N", scale=None) 
        )
        text = bars.mark_text(align='center', baseline='bottom', dy=-5, color='white', fontSize=13, fontWeight='bold').encode(text=alt.Text('Toneladas:Q', format=',.0f'))
        chart_vol = (bars + text).properties(height=180, background="transparent")
        st.altair_chart(chart_vol, use_container_width=True)
    else:
        st.caption("Aguardando carregamento da escala de turnos.")

# ==============================================================================
# 🚜 BLOCO 4: ALOCAÇÃO DE EQUIPAMENTOS (CLICÁVEL)
# ==============================================================================
st.markdown(f"""
    <div class="master-metric-box" style="border-left-color: #E67E22;">
        <div class="master-metric-title">🚜 Máquinas e Equipamentos</div>
        <div class="master-metric-val">{equip_em_uso} <span style="font-size:1.1rem; color:#94a3b8;">Em Operação</span></div>
        <div class="master-metric-sub" style="color: #E67E22;">Stand-by / Parados: {equip_standby}</div>
    </div>
""", unsafe_allow_html=True)

with st.expander("🔍 Toque para ver Frota e Talhas"):
    if not df_frota.empty and not df_f_atual.empty:
        # Separa a carga das empilhadeiras e talhas
        carr_op = df_f_atual[(df_f_atual["POSTO"].astype(str).str.contains("CARREG", case=False)) & (df_f_atual["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]["EQUIPAMENTO"].tolist()
        linha_op = df_f_atual[(df_f_atual["POSTO"].astype(str).str.contains("LINHA", case=False)) & (df_f_atual["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]["EQUIPAMENTO"].tolist()
        
        # Filtra Talhas (Tanto no nome quanto no posto)
        talhas_op = df_f_atual[(df_f_atual["POSTO"].astype(str).str.contains("TALHA", case=False) | df_f_atual["EQUIPAMENTO"].astype(str).str.contains("TALHA", case=False)) & (df_f_atual["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]["EQUIPAMENTO"].tolist()
        
        paradas = df_f_atual[df_f_atual["STATUS_RODIZIO"].astype(str).str.contains("STAND", case=False)]["EQUIPAMENTO"].tolist()

        st.markdown("**🟢 Empilhadeiras - Carregamento:**")
        st.markdown(" ".join([f'<span class="tag-box tag-op">{t}</span>' for t in carr_op]) if carr_op else "<span style='color:gray; font-size:0.85rem;'>Nenhum</span>", unsafe_allow_html=True)

        st.markdown("<br>**🟢 Empilhadeiras - Linha:**", unsafe_allow_html=True)
        st.markdown(" ".join([f'<span class="tag-box tag-op">{t}</span>' for t in linha_op]) if linha_op else "<span style='color:gray; font-size:0.85rem;'>Nenhum</span>", unsafe_allow_html=True)

        st.markdown("<br>**🏗️ Ponte Rolante / Talhas:**", unsafe_allow_html=True)
        st.markdown(" ".join([f'<span class="tag-box tag-talha">{t}</span>' for t in talhas_op]) if talhas_op else "<span style='color:gray; font-size:0.85rem;'>Nenhuma Talha operando</span>", unsafe_allow_html=True)

        st.markdown("<br>**🔴 Stand-by / Paradas:**", unsafe_allow_html=True)
        st.markdown(" ".join([f'<span class="tag-box tag-standby">{t}</span>' for t in paradas]) if paradas else "<span style='color:gray; font-size:0.85rem;'>Nenhum</span>", unsafe_allow_html=True)
    else:
        st.caption("Planilha Rodizio_Frota indisponível.")

st.markdown("<br><center><span style='color:#94a3b8; font-size: 0.75rem;'>Logística MI | A.L.O.V.E Core Mobile Dashboard</span></center>", unsafe_allow_html=True)
