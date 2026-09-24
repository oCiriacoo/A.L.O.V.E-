import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
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
# 🎨 CSS HÍBRIDO (CARD UNIFICADO COM EXPANDER E GRÁFICOS ALTAIR)
# ==============================================================================
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
        /* Remove o espaço entre o Card e o Expander para parecer um bloco só */
        div.stMarkdown { margin-bottom: 0 !important; }
        
        /* Card Mestre (Topo) */
        .master-metric-box {
            background-color: #111c2e;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            padding: 16px 20px;
            border-left: 6px solid;
            border-top: 1px solid #1c2b42;
            border-right: 1px solid #1c2b42;
            margin-bottom: 0px !important;
        }
        .master-metric-title { color: #94a3b8; font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
        .master-metric-val { color: #ffffff; font-size: 2rem; font-weight: 900; line-height: 1.1; margin-bottom: 4px; }
        .master-metric-sub { font-size: 0.85rem; font-weight: 700; }

        /* Expander Grudado (Base) */
        div[data-testid="stExpander"] {
            border: 1px solid #1c2b42 !important;
            border-top: none !important;
            border-radius: 0 0 12px 12px !important;
            background-color: #0a101d !important;
            margin-top: 0px !important;
            margin-bottom: 25px !important;
        }
        div[data-testid="stExpander"] details summary {
            background-color: #111c2e;
            color: #38bdf8;
            border-radius: 0 0 12px 12px;
            padding: 8px 15px;
        }
        div[data-testid="stExpander"] details[open] summary {
            border-bottom: 1px solid #1c2b42;
            border-radius: 0;
            background-color: #0a101d;
        }
        div[data-testid="stExpander"] details summary p {
            font-size: 0.85rem;
            font-weight: 600;
        }

        /* Sub-estilos */
        .patio-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
        .card-patio-sub { background-color: #111c2e; border-radius: 8px; padding: 10px; border-left: 4px solid; border: 1px solid #1c2b42;}
        .card-patio-title { font-weight: 800; font-size: 0.95rem; margin-bottom: 4px; }
        .card-patio-qtd { font-size: 1.4rem; font-weight: 900; color: #ffffff; }
        .card-patio-ton { font-size: 0.85rem; color: #94a3b8; font-weight: 600; }

        .tag-box { display: inline-block; padding: 4px 10px; margin: 3px; border-radius: 6px; font-weight: 800; font-size: 0.8rem; text-align: center; }
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
    except Exception: return pd.DataFrame()

# 🔥 PROTEÇÃO ANTIBUG DE TONELAGEM (ARRUMA VIRGULAS E PONTOS)
def safe_to_numeric(val):
    if pd.isna(val) or val == "" or val is None: return 0.0
    if isinstance(val, (int, float)): return float(val)
    val_str = str(val).strip()
    try: return float(val_str)
    except:
        try: return float(val_str.replace(".", "").replace(",", "."))
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

        corte_08, corte_16, vol_atual = 0.0, 0.0, 0.0
        hora_08 = agora_br.replace(hour=8, minute=0, second=0, microsecond=0)
        hora_16 = agora_br.replace(hour=16, minute=0, second=0, microsecond=0)

        for row in reversed(linhas[1:]):
            if len(row) > 3:
                try:
                    dt_row = datetime.strptime(row[0].strip(), "%d/%m/%Y %H:%M:%S")
                    vol_linha = safe_to_numeric(row[3])
                    if vol_atual == 0.0: vol_atual = vol_linha
                    if corte_16 == 0.0 and dt_row <= hora_16 and dt_row.date() == hoje_date: corte_16 = vol_linha
                    if corte_08 == 0.0 and dt_row <= hora_08 and dt_row.date() == hoje_date: corte_08 = vol_linha
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
# 🔥 RESGATE DOS DADOS DA NUVEM
# ==============================================================================
df_cache = carregar_dados_nuvem("Cache_Painel", cabecalho=0)
cache_dict = {str(row.iloc[0]).strip(): str(row.iloc[1]).strip() for _, row in df_cache.iterrows()} if not df_cache.empty else {}

dados_patio = json.loads(cache_dict.get("dados_patio", "{}")) if cache_dict.get("dados_patio") else {}
qualidade = json.loads(cache_dict.get("qualidade", "{}")) if cache_dict.get("qualidade") else {}
dados_segregados = json.loads(cache_dict.get("dados_segregados", "{}")) if cache_dict.get("dados_segregados") else {}
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

# Pátio: PR é ignorado da carga DISPONÍVEL, e da FÍSICA
vol_patio_disponivel = sum(dados_patio.get(k, {}).get("peso", 0.0) for k in ["00", "01", "FC"]) if dados_patio else 0.0
total_veiculos_fisicos = sum(dados_patio.get(k, {}).get("veiculos", 0) for k in ["00", "01", "FC", "TR"]) if dados_patio else 0
prev_carr = vol_hoje + min(cap_maxima_restante, vol_patio_disponivel)

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
    st.markdown(f'<div style="background-color: {cor_bg}; border-left: 4px solid {cor_border}; padding: 10px 14px; margin: 10px 0; border-radius: 6px;"><div style="color: {cor_border}; font-size: 11px; font-weight: 800; text-transform: uppercase;">📋 Observação Operacional</div><div style="color: {cor_txt}; font-size: 12px; font-weight: 600; white-space: pre-wrap;">{observacoes}</div></div>', unsafe_allow_html=True)

st.write("")

# ==============================================================================
# 📦 BLOCO 1: PÁTIO DE VEÍCULOS
# ==============================================================================
st.markdown(f"""
    <div class="master-metric-box" style="border-left-color: #38bdf8;">
        <div class="master-metric-title">🚛 Pátio da Fábrica (Físico)</div>
        <div class="master-metric-val">{total_veiculos_fisicos} <span style="font-size:1.1rem; color:#94a3b8;">Veículos</span></div>
        <div class="master-metric-sub" style="color: #38bdf8;">Carga Disponível p/ Carregar: {vol_patio_disponivel:,.0f} t</div>
    </div>
""", unsafe_allow_html=True)

with st.expander("👇 Ver detalhamento por Status"):
    if dados_patio:
        blocos_patio = [("🚙 Prog/Chegando", "PR", "#94A3B8"), ("📋 Checklist", "00", "#E5B800"), ("🚛 Apoio", "01", "#E67E22"), ("✅ Fila", "FC", "#00D672"), ("📄 Termo SAP", "TR", "#3498DB")]
        html_p = '<div class="patio-grid">'
        for tit, chv, cor in blocos_patio:
            v_qtd = dados_patio.get(chv, {}).get("veiculos", 0)
            v_ton = dados_patio.get(chv, {}).get("peso", 0.0)
            html_p += f"<div class='card-patio-sub' style='border-left-color: {cor};'><div class='card-patio-title' style='color: {cor};'>{tit}</div><div class='card-patio-qtd'>{int(v_qtd)} <span style='font-size:0.75rem; color:#94a3b8;'>veíc</span></div><div class='card-patio-ton'>{v_ton:,.0f} t</div></div>"
        html_p += "</div>"
        st.markdown(html_p, unsafe_allow_html=True)
    else:
        st.caption("Sem dados de pátio.")

# ==============================================================================
# 🏭 BLOCO 2: PRODUÇÃO DO DIA
# ==============================================================================
st.markdown(f"""
    <div class="master-metric-box" style="border-left-color: #E5B800;">
        <div class="master-metric-title">🏭 Produção de Celulose (Hoje)</div>
        <div class="master-metric-val">{prod_hoje:,.0f} <span style="font-size:1.1rem; color:#94a3b8;">TON</span></div>
        <div class="master-metric-sub" style="color: #E5B800;">Previsão de Fechamento: {prev_prod:,.0f} t</div>
    </div>
""", unsafe_allow_html=True)

with st.expander("👇 Ver Máquinas e Qualidade"):
    if qualidade:
        for maq in ["MS1", "MS2"]:
            p_maq = safe_to_numeric(qualidade.get(maq, {}).get("producao", 0))
            mat_maq = qualidade.get(maq, {}).get("material", "--")
            q_suj = qualidade.get(maq, {}).get('sujidade', 0.0)
            q_visc = qualidade.get(maq, {}).get('viscosidade', 0.0)
            q_teor = qualidade.get(maq, {}).get('teor', 0.0)
            c_suj = "#00D672" if q_suj <= 2.5 else "#E74C3C"
            c_vis = "#00D672" if q_visc >= 650 else "#E74C3C"
            c_teo = "#00D672" if q_teor >= 88.5 else "#E74C3C"

            st.markdown(f"""
                <div style="background-color: #111c2e; border: 1px solid #1c2b42; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="color:#ffffff; font-weight:800; font-size:1rem;">⚙️ {maq}</span>
                        <span style="color:#FF9F1C; font-weight:800; font-size:0.85rem;">📦 MAT: {mat_maq}</span>
                        <span style="color:#3498DB; font-weight:900; font-size:1rem;">{p_maq:,.0f} t</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; text-align: center; border-top: 1px solid #1c2b42; padding-top: 8px;">
                        <div><div style="font-size:0.75rem; color:#94a3b8;">Sujidade</div><div style="font-size:1.05rem; font-weight:bold; color:{c_suj};">{q_suj:.2f}</div></div>
                        <div><div style="font-size:0.75rem; color:#94a3b8;">Viscosidade</div><div style="font-size:1.05rem; font-weight:bold; color:{c_vis};">{q_visc:,.0f}</div></div>
                        <div><div style="font-size:0.75rem; color:#94a3b8;">Teor Seco</div><div style="font-size:1.05rem; font-weight:bold; color:{c_teo};">{q_teor:.2f}%</div></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# ==============================================================================
# 🚚 BLOCO 3: EXPEDIÇÃO DO DIA & GRÁFICO ALTAIR
# ==============================================================================
st.markdown(f"""
    <div class="master-metric-box" style="border-left-color: #00D672;">
        <div class="master-metric-title">🚛 Expedição Realizada (Hoje)</div>
        <div class="master-metric-val">{vol_hoje:,.0f} <span style="font-size:1.1rem; color:#94a3b8;">TON</span></div>
        <div class="master-metric-sub" style="color: #00D672;">Previsão de Fechamento: {prev_carr:,.0f} t</div>
    </div>
""", unsafe_allow_html=True)

with st.expander("👇 Ver Gráfico por Turno"):
    if dados_turnos and "turnos" in dados_turnos:
        turnos_list = dados_turnos["turnos"]
        ativo_key = dados_turnos.get("ativo_key")

        # Layout HTML dos 3 turnos
        html_t_cards = '<div style="display:flex; gap:6px; margin-bottom:12px;">'
        for t in turnos_list:
            is_atv = (t["key"] == ativo_key)
            cor_b = "#FF9F1C" if is_atv else "#1c2b42"
            cor_txt = "#FF9F1C" if is_atv else "#ffffff"
            sub_txt = f"{t['horario']} (ATIVO)" if is_atv else t['horario']
            html_t_cards += f"<div style='flex:1; background-color:#0a101d; border:1.5px solid {cor_b}; border-radius:8px; padding:8px; text-align:center;'><div style='font-size:0.75rem; font-weight:800; color:{cor_txt};'>{t['letra']}</div><div style='font-size:1.1rem; font-weight:900; color:#ffffff;'>{t['vol']:,.0f} t</div><div style='font-size:0.65rem; color:#94a3b8;'>{sub_txt}</div></div>"
        html_t_cards += '</div>'
        st.markdown(html_t_cards, unsafe_allow_html=True)

        # Gráfico Altair com verificação anti-quebra
        df_vol = pd.DataFrame([{"Turno": t['letra'], "Toneladas": t["vol"], "Cor": "#FF9F1C" if t["key"] == ativo_key else "#3498DB"} for t in turnos_list])
        if not df_vol.empty:
            max_vol = max(df_vol["Toneladas"]) if max(df_vol["Toneladas"]) > 0 else 100
            bars = alt.Chart(df_vol).mark_bar(cornerRadius=6).encode(x=alt.X("Turno:N", sort=None, axis=alt.Axis(labelAngle=0, labelColor="#ffffff", title=None)), y=alt.Y("Toneladas:Q", scale=alt.Scale(domain=[0, max_vol * 1.3]), axis=None), color=alt.Color("Cor:N", scale=None))
            text = bars.mark_text(align='center', baseline='bottom', dy=-5, color='white', fontSize=13, fontWeight='bold').encode(text=alt.Text('Toneladas:Q', format=',.0f'))
            st.altair_chart((bars + text).properties(height=180, background="transparent"), use_container_width=True)
    else:
        st.caption("Aguardando carregamento da escala de turnos.")

# ==============================================================================
# 📦 BLOCO 4: ESTOQUE TOTAL
# ==============================================================================
st.markdown(f"""
    <div class="master-metric-box" style="border-left-color: #9b59b6;">
        <div class="master-metric-title">📦 Estoque Físico no Armazém</div>
        <div class="master-metric-val">{estoque_total:,.0f} <span style="font-size:1.1rem; color:#94a3b8;">TON</span></div>
        <div class="master-metric-sub" style="color: #9b59b6;">Distribuição por Material</div>
    </div>
""", unsafe_allow_html=True)

with st.expander("👇 Ver Gráfico por Material"):
    if dados_segregados:
        df_seg = pd.DataFrame(list(dados_segregados.items()), columns=["Material", "Toneladas"]).sort_values(by="Toneladas", ascending=False)
        if not df_seg.empty:
            bars_seg = alt.Chart(df_seg).mark_bar(cornerRadius=4).encode(x=alt.X("Material:N", sort="-y", axis=alt.Axis(labelAngle=-45, labelColor="#94a3b8", title=None)), y=alt.Y("Toneladas:Q", axis=None), color=alt.value("#38bdf8"))
            text_seg = bars_seg.mark_text(align='center', baseline='bottom', dy=-3, color='white', fontSize=11, fontWeight='bold').encode(text=alt.Text('Toneladas:Q', format=',.0f'))
            st.altair_chart((bars_seg + text_seg).properties(height=200, background="transparent"), use_container_width=True)
    else:
        st.caption("Aguardando detalhamento de material...")

# ==============================================================================
# 🚜 BLOCO 5: FROTA (COM CAIXA DE SELEÇÃO)
# ==============================================================================
df_frota = carregar_dados_nuvem("Rodizio_Frota")
equip_em_uso_agora = 0

if not df_frota.empty:
    col_t = "TURNO_JANELA" if "TURNO_JANELA" in df_frota.columns else df_frota.columns[0]
    turnos_frota = df_frota[col_t].dropna().unique().tolist()
    idx_sug = next((i for i, t in enumerate(turnos_frota) if ("00:00" in str(t) and 0 <= agora.hour < 8) or ("08:00" in str(t) and 8 <= agora.hour < 16) or ("16:00" in str(t) and 16 <= agora.hour <= 23)), 0)
    turno_atual_str = turnos_frota[idx_sug] if turnos_frota else ""
    df_f_agora = df_frota[df_frota[col_t] == turno_atual_str]
    
    op1 = df_f_agora[(df_f_agora["POSTO"].astype(str).str.contains("CARREG", case=False)) & (df_f_agora["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]
    op2 = df_f_agora[(df_f_agora["POSTO"].astype(str).str.contains("LINHA", case=False)) & (df_f_agora["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]
    op3 = df_f_agora[(df_f_agora["POSTO"].astype(str).str.contains("TALHA", case=False) | df_f_agora["EQUIPAMENTO"].astype(str).str.contains("TALHA", case=False)) & (df_f_agora["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]
    equip_em_uso_agora = len(op1) + len(op2) + len(op3)

st.markdown(f"""
    <div class="master-metric-box" style="border-left-color: #E67E22;">
        <div class="master-metric-title">🚜 Equipamentos em Operação</div>
        <div class="master-metric-val">{equip_em_uso_agora} <span style="font-size:1.1rem; color:#94a3b8;">Neste Exato Momento</span></div>
        <div class="master-metric-sub" style="color: #E67E22;">Contempla Empilhadeiras e Talhas</div>
    </div>
""", unsafe_allow_html=True)

with st.expander("👇 Ver Turnos e Janelas da Frota"):
    if not df_frota.empty:
        # Traz de volta a caixa de seleção para escolher o horário
        turno_sel = st.selectbox("Selecione o Horário / Janela:", turnos_frota, index=idx_sug)
        df_t = df_frota[df_frota[col_t] == turno_sel]

        carr = df_t[(df_t["POSTO"].astype(str).str.contains("CARREG", case=False)) & (df_t["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]["EQUIPAMENTO"].tolist()
        linha = df_t[(df_t["POSTO"].astype(str).str.contains("LINHA", case=False)) & (df_t["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]["EQUIPAMENTO"].tolist()
        talhas = df_t[(df_t["POSTO"].astype(str).str.contains("TALHA", case=False) | df_t["EQUIPAMENTO"].astype(str).str.contains("TALHA", case=False)) & (df_t["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]["EQUIPAMENTO"].tolist()
        paradas = df_t[df_t["STATUS_RODIZIO"].astype(str).str.contains("STAND", case=False)]["EQUIPAMENTO"].tolist()

        st.markdown("**🟢 Empilhadeiras - Carregamento:**")
        st.markdown(" ".join([f'<span class="tag-box tag-op">{t}</span>' for t in carr]) if carr else "<span style='color:gray; font-size:0.85rem;'>Nenhum</span>", unsafe_allow_html=True)
        st.markdown("<br>**🟢 Empilhadeiras - Linha:**", unsafe_allow_html=True)
        st.markdown(" ".join([f'<span class="tag-box tag-op">{t}</span>' for t in linha]) if linha else "<span style='color:gray; font-size:0.85rem;'>Nenhum</span>", unsafe_allow_html=True)
        st.markdown("<br>**🏗️ Ponte Rolante / Talhas:**", unsafe_allow_html=True)
        st.markdown(" ".join([f'<span class="tag-box tag-talha">{t}</span>' for t in talhas]) if talhas else "<span style='color:gray; font-size:0.85rem;'>Nenhuma operando</span>", unsafe_allow_html=True)
        st.markdown("<br>**🔴 Stand-by / Paradas:**", unsafe_allow_html=True)
        st.markdown(" ".join([f'<span class="tag-box tag-standby">{t}</span>' for t in paradas]) if paradas else "<span style='color:gray; font-size:0.85rem;'>Nenhum</span>", unsafe_allow_html=True)

# ==============================================================================
# ⛽ BLOCO 6: CONSUMO GLP MENSAL (COM GRÁFICO ALTAIR)
# ==============================================================================
df_glp = carregar_dados_nuvem("Abastecimentos_GLP", cabecalho=None)
total_glp_recente = 0
mes_recente = "--/----"

if not df_glp.empty and len(df_glp.columns) >= 8:
    df_g = pd.DataFrame()
    df_g["DATA_DT"] = pd.to_datetime(df_glp.iloc[:, 2].astype(str).str.strip(), format="%d/%m/%Y", errors="coerce")
    df_g = df_g.dropna(subset=["DATA_DT"]) # Remove datas zoadas
    
    if not df_g.empty:
        df_g["MES_ANO"] = df_g["DATA_DT"].dt.strftime("%m/%Y")
        df_g["MAQUINA"] = df_glp.iloc[:, 5].astype(str).str.strip()
        df_g["KG_NUM"] = df_glp.iloc[:, 7].apply(safe_to_numeric)
        
        meses_disp = df_g["MES_ANO"].dropna().unique().tolist()
        if meses_disp:
            meses_disp.sort(key=lambda x: datetime.strptime(x, "%m/%Y"))
            mes_recente = meses_disp[-1]
            total_glp_recente = df_g[df_g["MES_ANO"] == mes_recente]["KG_NUM"].sum()

st.markdown(f"""
    <div class="master-metric-box" style="border-left-color: #fd7e14;">
        <div class="master-metric-title">⛽ Consumo de GLP da Frota</div>
        <div class="master-metric-val">{total_glp_recente:,.0f} <span style="font-size:1.1rem; color:#94a3b8;">KG</span></div>
        <div class="master-metric-sub" style="color: #fd7e14;">Acumulado do Mês Atual ({mes_recente})</div>
    </div>
""", unsafe_allow_html=True)

with st.expander("👇 Ver Gráfico de Consumo por Máquina"):
    if not df_glp.empty and 'df_g' in locals() and not df_g.empty and meses_disp:
        mes_sel_glp = st.selectbox("Selecione o Mês Referência:", meses_disp, index=len(meses_disp)-1)
        df_mes_selecionado = df_g[df_g["MES_ANO"] == mes_sel_glp]
        df_maq = df_mes_selecionado.groupby("MAQUINA")["KG_NUM"].sum().reset_index().sort_values(by="KG_NUM", ascending=False)
        
        if not df_maq.empty:
            bars_glp = alt.Chart(df_maq).mark_bar(cornerRadius=4).encode(
                x=alt.X("MAQUINA:N", sort="-y", axis=alt.Axis(labelAngle=-45, labelColor="#94a3b8", title=None)),
                y=alt.Y("KG_NUM:Q", axis=None), color=alt.value("#fd7e14")
            )
            text_glp = bars_glp.mark_text(align='center', baseline='bottom', dy=-3, color='white', fontSize=11, fontWeight='bold').encode(text=alt.Text('KG_NUM:Q', format=',.0f'))
            st.altair_chart((bars_glp + text_glp).properties(height=200, background="transparent"), use_container_width=True)
    else:
        st.caption("Planilha Abastecimentos_GLP indisponível ou sem datas válidas.")

st.markdown("<br><center><span style='color:#94a3b8; font-size: 0.75rem;'>Logística MI | A.L.O.V.E Core Mobile Dashboard</span></center>", unsafe_allow_html=True)
