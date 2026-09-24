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
# 🎨 CSS PURO (BLOCOS CLICÁVEIS E GRÁFICOS NATIVOS MÓVEIS)
# ==============================================================================
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
        /* Mágica do Bloco Clicável (Expander Nativo HTML) */
        details.master-box {
            background-color: #111c2e;
            border-radius: 12px;
            margin-bottom: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            border-left: 6px solid;
            overflow: hidden;
        }
        details.master-box summary {
            list-style: none;
            cursor: pointer;
            padding: 16px 20px;
            outline: none;
            position: relative;
        }
        details.master-box summary::-webkit-details-marker { display: none; }
        details.master-box summary::after {
            content: '▼';
            position: absolute;
            right: 20px;
            top: 50%;
            transform: translateY(-50%);
            color: #94a3b8;
            font-size: 1.1rem;
            transition: transform 0.3s ease;
        }
        details.master-box[open] summary::after { transform: translateY(-50%) rotate(180deg); }

        .master-metric-title { color: #94a3b8; font-size: 0.85rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
        .master-metric-val { color: #ffffff; font-size: 1.9rem; font-weight: 900; line-height: 1.2; margin-bottom: 4px; }
        .master-metric-sub { font-size: 0.85rem; font-weight: 700; }
        .master-content { background-color: #0a101d; padding: 16px; border-top: 1px solid #1c2b42; }

        .patio-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
        .card-patio-sub { background-color: #111c2e; border-radius: 8px; padding: 10px; border-left: 4px solid; }
        .card-patio-title { font-weight: 800; font-size: 0.95rem; margin-bottom: 4px; }
        .card-patio-qtd { font-size: 1.4rem; font-weight: 900; color: #ffffff; }
        .card-patio-ton { font-size: 0.85rem; color: #94a3b8; font-weight: 600; }

        .bar-chart-row { margin-bottom: 12px; }
        .bar-chart-labels { display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 700; color: #fff; margin-bottom: 4px; }
        .bar-chart-bg { background-color: #1c2b42; border-radius: 6px; height: 14px; width: 100%; overflow: hidden; }
        .bar-chart-fill { height: 100%; border-radius: 6px; transition: width 0.5s ease-in-out; }

        .tag-box { display: inline-block; padding: 4px 8px; margin: 3px; border-radius: 6px; font-weight: 800; font-size: 0.75rem; }
        .tag-op { background-color: #00D672; color: #0a101d; }
        .tag-standby { background-color: #E74C3C; color: #ffffff; }
        .tag-talha { background-color: #F39C12; color: #0a101d; }
        .shift-header { color: #3498DB; font-size: 0.9rem; font-weight: 800; border-bottom: 1px solid #1c2b42; padding-bottom: 4px; margin-top: 12px; margin-bottom: 8px; }
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
# 🔥 RESGATE DOS DADOS DA NUVEM & CÁLCULOS
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

vol_patio_disponivel = sum(dados_patio.get(k, {}).get("peso", 0.0) for k in ["00", "01", "FC"]) if dados_patio else 0.0
total_veiculos_fisicos = sum(dados_patio.get(k, {}).get("veiculos", 0) for k in ["00", "01", "FC", "TR"]) if dados_patio else 0
prev_carr = vol_hoje + min(cap_maxima_restante, vol_patio_disponivel)

# ==============================================================================
# CABEÇALHO
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
# 📦 BLOCO 1: PÁTIO DE VEÍCULOS (CLICÁVEL 100% NATIVO)
# ==============================================================================
html_patio = '<details class="master-box" style="border-left-color: #38bdf8;">'
html_patio += '<summary>'
html_patio += '<div class="master-metric-title">🚛 Pátio da Fábrica (Tempo Real)</div>'
html_patio += f'<div class="master-metric-val">{total_veiculos_fisicos} <span style="font-size:1.1rem; color:#94a3b8;">Veículos Físicos</span></div>'
html_patio += f'<div class="master-metric-sub" style="color: #38bdf8;">Carga Disponível: {vol_patio_disponivel:,.0f} t</div>'
html_patio += '</summary>'
html_patio += '<div class="master-content patio-grid">'

if dados_patio:
    blocos_patio = [("🚙 Prog/Chegando", "PR", "#94A3B8"), ("📋 Checklist", "00", "#E5B800"), ("🚛 Apoio", "01", "#E67E22"), ("✅ Fila", "FC", "#00D672"), ("📄 Termo SAP", "TR", "#3498DB")]
    for tit, chv, cor in blocos_patio:
        v_qtd = dados_patio.get(chv, {}).get("veiculos", 0)
        v_ton = dados_patio.get(chv, {}).get("peso", 0.0)
        html_patio += f"<div class='card-patio-sub' style='border-left-color: {cor};'>"
        html_patio += f"<div class='card-patio-title' style='color: {cor};'>{tit}</div>"
        html_patio += f"<div class='card-patio-qtd'>{int(v_qtd)} <span style='font-size:0.75rem; color:#94a3b8;'>veíc</span></div>"
        html_patio += f"<div class='card-patio-ton'>{v_ton:,.0f} t</div>"
        html_patio += "</div>"
html_patio += "</div></details>"
st.markdown(html_patio, unsafe_allow_html=True)

# ==============================================================================
# 🏭 BLOCO 2: PRODUÇÃO & QUALIDADE (CLICÁVEL 100% NATIVO)
# ==============================================================================
html_prod = '<details class="master-box" style="border-left-color: #E5B800;">'
html_prod += '<summary>'
html_prod += '<div class="master-metric-title">🏭 Produção de Celulose (Hoje)</div>'
html_prod += f'<div class="master-metric-val">{prod_hoje:,.0f} <span style="font-size:1.1rem; color:#94a3b8;">TON</span></div>'
html_prod += f'<div class="master-metric-sub" style="color: #E5B800;">Previsão de Fechamento: {prev_prod:,.0f} t</div>'
html_prod += '</summary>'
html_prod += '<div class="master-content">'

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

        html_prod += "<div style='background-color: #111c2e; border: 1px solid #1c2b42; border-radius: 8px; padding: 12px; margin-bottom: 8px;'>"
        html_prod += "<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>"
        html_prod += f"<span style='color:#ffffff; font-weight:800; font-size:1rem;'>⚙️ {maq}</span>"
        html_prod += f"<span style='color:#FF9F1C; font-weight:800; font-size:0.85rem;'>📦 MAT: {mat_maq}</span>"
        html_prod += f"<span style='color:#3498DB; font-weight:900; font-size:1rem;'>{p_maq:,.0f} t</span>"
        html_prod += "</div>"
        html_prod += "<div style='display: flex; justify-content: space-between; text-align: center; border-top: 1px solid #1c2b42; padding-top: 8px;'>"
        html_prod += f"<div><div style='font-size:0.75rem; color:#94a3b8;'>Sujidade</div><div style='font-size:1.05rem; font-weight:bold; color:{c_suj};'>{q_suj:.2f}</div></div>"
        html_prod += f"<div><div style='font-size:0.75rem; color:#94a3b8;'>Viscosidade</div><div style='font-size:1.05rem; font-weight:bold; color:{c_vis};'>{q_visc:,.0f}</div></div>"
        html_prod += f"<div><div style='font-size:0.75rem; color:#94a3b8;'>Teor Seco</div><div style='font-size:1.05rem; font-weight:bold; color:{c_teo};'>{q_teor:.2f}%</div></div>"
        html_prod += "</div></div>"
html_prod += "</div></details>"
st.markdown(html_prod, unsafe_allow_html=True)

# ==============================================================================
# 🚚 BLOCO 3: EXPEDIÇÃO & TURNOS COM GRÁFICO CSS (CLICÁVEL 100% NATIVO)
# ==============================================================================
html_exp = '<details class="master-box" style="border-left-color: #00D672;">'
html_exp += '<summary>'
html_exp += '<div class="master-metric-title">🚛 Expedição Realizada (Hoje)</div>'
html_exp += f'<div class="master-metric-val">{vol_hoje:,.0f} <span style="font-size:1.1rem; color:#94a3b8;">TON</span></div>'
html_exp += f'<div class="master-metric-sub" style="color: #00D672;">Previsão de Fechamento: {prev_carr:,.0f} t</div>'
html_exp += '</summary>'
html_exp += '<div class="master-content">'

if dados_turnos and "turnos" in dados_turnos:
    turnos_list = dados_turnos["turnos"]
    ativo_key = dados_turnos.get("ativo_key")
    
    html_exp += '<div style="display:flex; gap:6px; margin-bottom:16px;">'
    for t in turnos_list:
        is_atv = (t["key"] == ativo_key)
        cor_b = "#FF9F1C" if is_atv else "#1c2b42"
        cor_txt = "#FF9F1C" if is_atv else "#ffffff"
        sub_txt = f"{t['horario']} (ATIVO)" if is_atv else t['horario']
        
        html_exp += f"<div style='flex:1; background-color:#111c2e; border:1.5px solid {cor_b}; border-radius:8px; padding:8px; text-align:center;'>"
        html_exp += f"<div style='font-size:0.75rem; font-weight:800; color:{cor_txt};'>{t['letra']}</div>"
        html_exp += f"<div style='font-size:1.1rem; font-weight:900; color:#ffffff;'>{t['vol']:,.0f} t</div>"
        html_exp += f"<div style='font-size:0.65rem; color:#94a3b8;'>{sub_txt}</div>"
        html_exp += "</div>"
    html_exp += '</div>'

    html_exp += '<div style="margin-top: 10px;">'
    max_vol = max([t["vol"] for t in turnos_list] + [100])
    for t in turnos_list:
        w_pct = min(100, (t["vol"] / max_vol) * 100)
        c_barra = "#FF9F1C" if t["key"] == ativo_key else "#3498DB"
        html_exp += "<div class='bar-chart-row'>"
        html_exp += f"<div class='bar-chart-labels'><span>{t['letra']}</span><span>{t['vol']:,.0f} t</span></div>"
        html_exp += f"<div class='bar-chart-bg'><div class='bar-chart-fill' style='width: {w_pct}%; background-color: {c_barra};'></div></div>"
        html_exp += "</div>"
    html_exp += '</div>'
else:
    html_exp += '<div style="color:gray; font-size:0.85rem;">Aguardando escala de turnos...</div>'

html_exp += "</div></details>"
st.markdown(html_exp, unsafe_allow_html=True)

# ==============================================================================
# 📦 BLOCO 4: ESTOQUE TOTAL & MATERIAIS COM GRÁFICO CSS (CLICÁVEL 100% NATIVO)
# ==============================================================================
html_est = '<details class="master-box" style="border-left-color: #9b59b6;">'
html_est += '<summary>'
html_est += '<div class="master-metric-title">📦 Estoque Físico no Armazém</div>'
html_est += f'<div class="master-metric-val">{estoque_total:,.0f} <span style="font-size:1.1rem; color:#94a3b8;">TON</span></div>'
html_est += '<div class="master-metric-sub" style="color: #9b59b6;">Distribuição por Material</div>'
html_est += '</summary>'
html_est += '<div class="master-content">'

if dados_segregados:
    df_seg = pd.DataFrame(list(dados_segregados.items()), columns=["Material", "Toneladas"]).sort_values(by="Toneladas", ascending=False)
    max_mat_vol = df_seg["Toneladas"].max() if not df_seg.empty else 100
    for _, row in df_seg.iterrows():
        w_pct = min(100, (row["Toneladas"] / max_mat_vol) * 100)
        html_est += "<div class='bar-chart-row' style='margin-bottom:8px;'>"
        html_est += f"<div class='bar-chart-labels'><span style='font-size:0.75rem; color:#94a3b8;'>{row['Material']}</span><span style='font-size:0.85rem; color:#fff;'>{row['Toneladas']:,.0f} t</span></div>"
        html_est += f"<div class='bar-chart-bg' style='height:8px;'><div class='bar-chart-fill' style='width: {w_pct}%; background-color: #38bdf8;'></div></div>"
        html_est += "</div>"
else:
    html_est += '<div style="color:gray; font-size:0.85rem;">Aguardando detalhamento de material...</div>'

html_est += "</div></details>"
st.markdown(html_est, unsafe_allow_html=True)

# ==============================================================================
# 🚜 BLOCO 5: FROTA (LISTA OS 3 TURNOS DIRETAMENTE DENTRO DO BLOCO)
# ==============================================================================
df_frota = carregar_dados_nuvem("Rodizio_Frota")
html_frota = '<details class="master-box" style="border-left-color: #E67E22;">'

if not df_frota.empty:
    col_turno = "TURNO_JANELA" if "TURNO_JANELA" in df_frota.columns else df_frota.columns[0]
    turnos = df_frota[col_turno].dropna().unique().tolist()
    
    # Descobre o turno atual para o título
    hora_atual = agora.hour
    idx_sug = next((i for i, t in enumerate(turnos) if ("00:00" in str(t) and 0 <= hora_atual < 8) or ("08:00" in str(t) and 8 <= hora_atual < 16) or ("16:00" in str(t) and 16 <= hora_atual <= 23)), 0)
    turno_atual_str = turnos[idx_sug] if turnos else ""
    df_f_atual = df_frota[df_frota[col_turno] == turno_atual_str]
    
    carr_op = df_f_atual[(df_f_atual["POSTO"].astype(str).str.contains("CARREG", case=False)) & (df_f_atual["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]["EQUIPAMENTO"].tolist()
    linha_op = df_f_atual[(df_f_atual["POSTO"].astype(str).str.contains("LINHA", case=False)) & (df_f_atual["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]["EQUIPAMENTO"].tolist()
    talhas_op = df_f_atual[(df_f_atual["POSTO"].astype(str).str.contains("TALHA", case=False) | df_f_atual["EQUIPAMENTO"].astype(str).str.contains("TALHA", case=False)) & (df_f_atual["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]["EQUIPAMENTO"].tolist()
    
    equip_em_uso_agora = len(carr_op) + len(linha_op) + len(talhas_op)

    html_frota += '<summary>'
    html_frota += '<div class="master-metric-title">🚜 Alocação de Equipamentos</div>'
    html_frota += f'<div class="master-metric-val">{equip_em_uso_agora} <span style="font-size:1.1rem; color:#94a3b8;">Em Operação (Agora)</span></div>'
    html_frota += '<div class="master-metric-sub" style="color: #E67E22;">Toque para ver a alocação dos 3 turnos</div>'
    html_frota += '</summary>'
    html_frota += '<div class="master-content">'

    # Renderiza o detalhamento dos 3 turnos dentro do bloco
    for t_str in turnos:
        df_t = df_frota[df_frota[col_turno] == t_str]
        carr = df_t[(df_t["POSTO"].astype(str).str.contains("CARREG", case=False)) & (df_t["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]["EQUIPAMENTO"].tolist()
        linha = df_t[(df_t["POSTO"].astype(str).str.contains("LINHA", case=False)) & (df_t["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]["EQUIPAMENTO"].tolist()
        talhas = df_t[(df_t["POSTO"].astype(str).str.contains("TALHA", case=False) | df_t["EQUIPAMENTO"].astype(str).str.contains("TALHA", case=False)) & (df_t["STATUS_RODIZIO"].astype(str).str.contains("OPERA", case=False))]["EQUIPAMENTO"].tolist()
        paradas = df_t[df_t["STATUS_RODIZIO"].astype(str).str.contains("STAND", case=False)]["EQUIPAMENTO"].tolist()

        str_carr = " ".join([f"<span class='tag-box tag-op'>{t}</span>" for t in carr]) if carr else "<span style='color:gray; font-size:0.8rem;'>Nenhum</span>"
        str_linha = " ".join([f"<span class='tag-box tag-op'>{t}</span>" for t in linha]) if linha else "<span style='color:gray; font-size:0.8rem;'>Nenhum</span>"
        str_talha = " ".join([f"<span class='tag-box tag-talha'>{t}</span>" for t in talhas]) if talhas else "<span style='color:gray; font-size:0.8rem;'>Nenhuma operando</span>"
        str_parada = " ".join([f"<span class='tag-box tag-standby'>{t}</span>" for t in paradas]) if paradas else "<span style='color:gray; font-size:0.8rem;'>Nenhum</span>"

        html_frota += f'<div class="shift-header">🕒 Turno / Janela: {t_str}</div>'
        html_frota += '<div style="margin-bottom:4px; font-size:0.8rem; color:#fff;">🟢 Carregamento:</div>'
        html_frota += f'<div style="margin-bottom:10px;">{str_carr}</div>'
        html_frota += '<div style="margin-bottom:4px; font-size:0.8rem; color:#fff;">🟢 Abastecimento de Linha:</div>'
        html_frota += f'<div style="margin-bottom:10px;">{str_linha}</div>'
        html_frota += '<div style="margin-bottom:4px; font-size:0.8rem; color:#fff;">🏗️ Pontes Rolantes / Talhas:</div>'
        html_frota += f'<div style="margin-bottom:10px;">{str_talha}</div>'
        html_frota += '<div style="margin-bottom:4px; font-size:0.8rem; color:#fff;">🔴 Stand-by / Paradas:</div>'
        html_frota += f'<div style="margin-bottom:10px;">{str_parada}</div>'

    html_frota += '</div></details>'
else:
    html_frota += '<summary><div class="master-metric-title">🚜 Equipamentos</div></summary><div class="master-content"><div style="color:gray; font-size:0.85rem;">Planilha Rodizio_Frota indisponível.</div></div></details>'

st.markdown(html_frota, unsafe_allow_html=True)

# ==============================================================================
# ⛽ BLOCO 6: CONSUMO DE GLP MENSAL (CLICÁVEL 100% NATIVO)
# ==============================================================================
df_glp = carregar_dados_nuvem("Abastecimentos_GLP", cabecalho=None)
html_glp = '<details class="master-box" style="border-left-color: #fd7e14;">'

if not df_glp.empty:
    df_g = pd.DataFrame()
    df_g["DATA_DT"] = pd.to_datetime(df_glp.iloc[:, 2].astype(str).str.strip(), format="%d/%m/%Y", errors="coerce")
    df_g["MES_ANO"] = df_g["DATA_DT"].dt.strftime("%m/%Y")
    df_g["MAQUINA"] = df_glp.iloc[:, 5].astype(str).str.strip()
    df_g["KG_NUM"] = df_glp.iloc[:, 7].apply(safe_to_numeric)
    
    meses_disp = df_g["MES_ANO"].dropna().unique().tolist()
    if meses_disp:
        meses_disp.sort(key=lambda x: datetime.strptime(x, "%m/%Y"))
        mes_sel = meses_disp[-1]
        df_mes = df_g[df_g["MES_ANO"] == mes_sel]
        total_glp = df_mes["KG_NUM"].sum()
        df_maq = df_mes.groupby("MAQUINA")["KG_NUM"].sum().reset_index().sort_values(by="KG_NUM", ascending=False)
        
        html_glp += '<summary>'
        html_glp += f'<div class="master-metric-title">⛽ Consumo de GLP ({mes_sel})</div>'
        html_glp += f'<div class="master-metric-val">{total_glp:,.0f} <span style="font-size:1.1rem; color:#94a3b8;">kg</span></div>'
        html_glp += '<div class="master-metric-sub" style="color: #fd7e14;">Toque para ver o consumo por máquina</div>'
        html_glp += '</summary>'
        html_glp += '<div class="master-content">'

        max_glp = df_maq["KG_NUM"].max() if not df_maq.empty else 100
        for _, row in df_maq.iterrows():
            w_pct = min(100, (row["KG_NUM"] / max_glp) * 100)
            html_glp += "<div class='bar-chart-row' style='margin-bottom:8px;'>"
            html_glp += f"<div class='bar-chart-labels'><span style='font-size:0.75rem; color:#94a3b8;'>{row['MAQUINA']}</span><span style='font-size:0.85rem; color:#fff;'>{row['KG_NUM']:,.0f} kg</span></div>"
            html_glp += f"<div class='bar-chart-bg' style='height:8px;'><div class='bar-chart-fill' style='width: {w_pct}%; background-color: #fd7e14;'></div></div>"
            html_glp += "</div>"
        html_glp += '</div></details>'
    else:
        html_glp += '<summary><div class="master-metric-title">⛽ Consumo de GLP</div></summary><div class="master-content"><div style="color:gray; font-size:0.85rem;">Sem dados de datas válidas.</div></div></details>'
else:
    html_glp += '<summary><div class="master-metric-title">⛽ Consumo de GLP</div></summary><div class="master-content"><div style="color:gray; font-size:0.85rem;">Planilha Abastecimentos_GLP indisponível.</div></div></details>'

st.markdown(html_glp, unsafe_allow_html=True)

st.markdown("<br><center><span style='color:#94a3b8; font-size: 0.75rem;'>Logística MI | A.L.O.V.E Core Mobile Dashboard</span></center>", unsafe_allow_html=True)
