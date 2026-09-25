import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import urllib.parse
import json
import requests
import csv
from io import StringIO
import ast

st.set_page_config(
    page_title="A.L.O.V.E. Mobile",
    page_icon="🚛",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# 🎨 CSS AVANÇADO (CARDS NEON + EXPANDERS + GRÁFICOS VERTICAIS)
# ==============================================================================
st.markdown("""
    <style>
        .block-container {
            padding-top: 4rem;  /* <--- O SEGREDO ESTÁ AQUI: Desce toda a página! */
            padding-bottom: 2rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
        
        input[type="radio"] { display: none; }
        
        /* Grid das Previsões no Topo (Efeito Neon) */
        .prev-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 14px;
        }
        
        /* Card Produção: Azul Neon */
        .prev-card-prod {
            background-color: #05080f;
            border: 2px solid #00f3ff;
            border-radius: 12px;
            padding: 14px;
            box-shadow: 0 0 12px rgba(0, 243, 255, 0.25), inset 0 0 8px rgba(0, 243, 255, 0.1);
        }
        .prev-card-prod .prev-title {
            color: #00f3ff;
            font-size: 0.78rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 4px;
        }
        .prev-card-prod .prev-val {
            color: #00f3ff;
            font-size: 1.85rem;
            font-weight: 900;
            line-height: 1.1;
            margin-bottom: 2px;
            text-shadow: 0 0 10px rgba(0, 243, 255, 0.4);
        }
        
        /* Card Carregamento: Laranja Neon */
        .prev-card-carr {
            background-color: #0d0600;
            border: 2px solid #ff7700;
            border-radius: 12px;
            padding: 14px;
            box-shadow: 0 0 12px rgba(255, 119, 0, 0.25), inset 0 0 8px rgba(255, 119, 0, 0.1);
        }
        .prev-card-carr .prev-title {
            color: #ff7700;
            font-size: 0.78rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 4px;
        }
        .prev-card-carr .prev-val {
            color: #ff7700;
            font-size: 1.85rem;
            font-weight: 900;
            line-height: 1.1;
            margin-bottom: 2px;
            text-shadow: 0 0 10px rgba(255, 119, 0, 0.4);
        }
        
        .prev-sub {
            font-size: 0.72rem;
            color: #94a3b8;
            font-weight: 700;
        }

        /* Mágica do Bloco Clicável (HTML details/summary) */
        details.master-box {
            background-color: #111c2e;
            border-radius: 12px;
            margin-bottom: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            border-left: 6px solid;
            overflow: hidden;
            border-top: 1px solid #1c2b42;
            border-right: 1px solid #1c2b42;
            border-bottom: 1px solid #1c2b42;
        }
        details.master-box summary {
            list-style: none;
            cursor: pointer;
            padding: 16px 20px;
            position: relative;
            outline: none;
            -webkit-tap-highlight-color: transparent; 
        }
        details.master-box summary::-webkit-details-marker { display: none; }
        
        details.master-box summary::after {
            content: '▼';
            position: absolute; right: 20px; top: 50%; transform: translateY(-50%);
            color: #94a3b8; font-size: 1.2rem; transition: transform 0.3s ease;
        }
        details.master-box[open] summary::after { transform: translateY(-50%) rotate(180deg); color: #38bdf8; }
        
        .master-metric-title { color: #94a3b8; font-size: 0.85rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; padding-right: 20px;}
        .master-metric-val { color: #ffffff; font-size: 2rem; font-weight: 900; line-height: 1.1; margin-bottom: 4px; }
        .master-metric-sub { font-size: 0.85rem; font-weight: 700; }
        .master-content { background-color: #0a101d; padding: 16px; border-top: 1px dashed #1c2b42; }

        .patio-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
        .card-patio-sub { background-color: #111c2e; border-radius: 8px; padding: 10px; border-left: 4px solid; border: 1px solid #1c2b42;}
        .card-patio-title { font-weight: 800; font-size: 0.95rem; margin-bottom: 4px; }
        .card-patio-qtd { font-size: 1.4rem; font-weight: 900; color: #ffffff; }
        .card-patio-ton { font-size: 0.85rem; color: #94a3b8; font-weight: 600; }

        .tag-box { display: inline-block; padding: 6px 10px; margin: 3px; border-radius: 6px; font-weight: 800; font-size: 0.8rem; text-align: center; }
        .tag-op { background-color: #00D672; color: #0a101d; }
        .tag-standby { background-color: #E74C3C; color: #ffffff; }
        .tag-talha { background-color: #F39C12; color: #0a101d; }
        
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    </style>
""", unsafe_allow_html=True)

SHEET_ID = "10FluiIwlynIlPDA74QI8mpHSIrAc-62H1hZNRBsvfCA"

@st.cache_data(ttl=30)
def carregar_dados_nuvem(worksheet_name: str, cabecalho=0):
    sheet_encoded = urllib.parse.quote(worksheet_name)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_encoded}&headers=1"
    try:
        df = pd.read_csv(url, header=cabecalho)
        df = df.dropna(how="all", axis=1).dropna(how="all", axis=0)
        return df
    except Exception:
        return pd.DataFrame()

def safe_to_numeric(val):
    if pd.isna(val) or val == "" or val is None: return 0.0
    if isinstance(val, (int, float)): return float(val)
    val_str = str(val).strip()
    try: return float(val_str)
    except:
        try: return float(val_str.replace(".", "").replace(",", "."))
        except: return 0.0

def descobrir_letras_turnos(data_alvo):
    data_referencia = date(2026, 9, 22)
    dias_passados = (data_alvo - data_referencia).days
    turnos = {"08_16": "C", "16_00": "B", "madrugada": "D"}
    for letra, dia in [("C", (0 + dias_passados) % 6), ("B", (2 + dias_passados) % 6), ("A", (4 + dias_passados) % 6)]:
        if dia in [0, 1]: turnos["08_16"] = letra
        elif dia in [2, 3]: turnos["16_00"] = letra
    return turnos

@st.cache_data(ttl=60)
def buscar_dados_turnos_historico(data_alvo):
    agora_br = datetime.utcnow() - timedelta(hours=3)
    hoje_date = agora_br.date()
    is_hoje = (data_alvo == hoje_date)
    
    letras = descobrir_letras_turnos(data_alvo)
    
    ativo_key = None
    if is_hoje:
        if agora_br.hour < 8: ativo_key = "t1"
        elif agora_br.hour < 16: ativo_key = "t2"
        else: ativo_key = "t3"

    try:
        url_csv = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
        resp = requests.get(url_csv, timeout=10)
        resp.encoding = 'utf-8'
        linhas = list(csv.reader(StringIO(resp.text)))

        corte_00, corte_08, corte_16, corte_fim = 0.0, 0.0, 0.0, 0.0
        
        hora_00 = datetime.combine(data_alvo, datetime.min.time())
        hora_08 = hora_00.replace(hour=8)
        hora_16 = hora_00.replace(hour=16)
        hora_fim = hora_00.replace(hour=23, minute=59, second=59)

        for row in reversed(linhas[1:]):
            if len(row) > 3:
                try:
                    dt_row = datetime.strptime(row[0].strip(), "%d/%m/%Y %H:%M:%S")
                    vol_linha = safe_to_numeric(row[3])
                    
                    if dt_row.date() == data_alvo:
                        if corte_fim == 0.0 and dt_row <= hora_fim: corte_fim = vol_linha
                        if corte_16 == 0.0 and dt_row <= hora_16: corte_16 = vol_linha
                        if corte_08 == 0.0 and dt_row <= hora_08: corte_08 = vol_linha
                        if corte_00 == 0.0 and dt_row <= hora_00: corte_00 = vol_linha
                except:
                    continue

        vol_t1 = max(0.0, corte_08 - corte_00) if corte_08 > 0 else 0.0
        
        if is_hoje:
            vol_t2 = max(0.0, corte_16 - corte_08) if agora_br.hour >= 16 else (max(0.0, corte_fim - corte_08) if agora_br.hour >= 8 else 0.0)
            vol_t3 = max(0.0, corte_fim - corte_16) if agora_br.hour >= 16 else 0.0
        else:
            vol_t2 = max(0.0, corte_16 - corte_08) if corte_16 > 0 else 0.0
            vol_t3 = max(0.0, corte_fim - corte_16) if corte_fim > 0 else 0.0

        turnos_exibir = []
        if vol_t1 > 0 or (is_hoje and agora_br.hour < 8 and vol_t1 > 0):
            turnos_exibir.append({"key": "t1", "letra": f"Turno {letras['madrugada']}", "vol": vol_t1, "horario": "00h - 08h"})
            
        turnos_exibir.append({"key": "t2", "letra": f"Turno {letras['08_16']}", "vol": vol_t2, "horario": "08h - 16h"})
        turnos_exibir.append({"key": "t3", "letra": f"Turno {letras['16_00']}", "vol": vol_t3, "horario": "16h - 00h"})
        
        total_dia = vol_t1 + vol_t2 + vol_t3
        return {"ativo_key": ativo_key, "turnos": turnos_exibir, "total_dia": total_dia}
    except Exception:
        return None

def build_vertical_chart(data, height=150):
    if not data: return ""
    max_v = max([d["value"] for d in data]) if max([d["value"] for d in data]) > 0 else 100
    html = f"<div style='display:flex; justify-content:space-evenly; align-items:flex-end; height:{height}px; border-bottom:1px solid #1c2b42; padding-bottom:0px; margin-top:15px;'>"
    lbl_html = "<div style='display:flex; justify-content:space-evenly; margin-top:8px;'>"
    for d in data:
        h_pct = min(100, (d["value"] / max_v) * 100)
        color = d.get("color", "#38bdf8")
        html += f"<div style='display:flex; flex-direction:column; align-items:center; height:100%; width:100%; justify-content:flex-end;'><span style='font-size:0.85rem; font-weight:800; color:{color}; margin-bottom:6px;'>{d['text']}</span><div style='width:38px; height:{h_pct}%; background-color:{color}; border-radius:4px 4px 0 0;'></div></div>"
        lbl_html += f"<div style='width:100%; text-align:center; font-size:0.75rem; color:#94a3b8; font-weight:800;'>{d['label']}</div>"
    html += "</div>"
    lbl_html += "</div>"
    return html + lbl_html

# ==============================================================================
# 🔥 RESGATE DOS DADOS DA NUVEM & CÁLCULOS (MOTOR CUMULATIVO REAL)
# ==============================================================================
# 1. Puxa os dados gerais e os históricos da Qualidade
df_cache = carregar_dados_nuvem("Cache_Painel", cabecalho=0)
df_qual_hist = carregar_dados_nuvem("Qualidade_MS", cabecalho=None) # 🔥 O Segredo está aqui!

cache_dict = {str(row.iloc[0]).strip(): str(row.iloc[1]).strip() for _, row in df_cache.iterrows()} if not df_cache.empty else {}

def parse_robusto(texto):
    if not texto or str(texto).strip() in ["", "None"]: return {}
    texto_str = str(texto).strip()
    try: return json.loads(texto_str)
    except:
        try: return ast.literal_eval(texto_str)
        except: return {}

dados_patio = parse_robusto(cache_dict.get("dados_patio", "{}"))
dados_segregados = parse_robusto(cache_dict.get("dados_segregados", "{}"))

vol_hoje = safe_to_numeric(cache_dict.get("vol_hoje", 0))
estoque_total = safe_to_numeric(cache_dict.get("estoque_total", 0))
ultima_att = cache_dict.get("ultima_atualizacao", "Desconhecida")
observacoes = cache_dict.get("observacoes", "")

# 2. 🧠 LÓGICA CUMULATIVA PARA A QUALIDADE E PRODUÇÃO (LENDO A ABA HISTÓRICA)
agora = datetime.utcnow() - timedelta(hours=3)
hoje_date = agora.date()
ontem_date = hoje_date - timedelta(days=1)

acumuladores = {
    "MS1": {"acumulado_prod": 0.0, "acumulado_l1": 0.0, "acumulado_l2": 0.0, "last_prod": 0.0, "last_l1": 0.0, "last_l2": 0.0},
    "MS2": {"acumulado_prod": 0.0, "acumulado_l1": 0.0, "acumulado_l2": 0.0, "last_prod": 0.0, "last_l1": 0.0, "last_l2": 0.0}
}

qualidade_sintetizada = {}

if not df_qual_hist.empty:
    for _, row in df_qual_hist.iterrows():
        if pd.isna(row.iloc[0]) or pd.isna(row.iloc[1]): continue
        chave_str = str(row.iloc[0]).strip()
        valor_str = str(row.iloc[1]).strip()
        
        if "MS1" in valor_str and "producao" in valor_str:
            try: dt_row = datetime.strptime(chave_str[:10], "%d/%m/%Y").date()
            except: dt_row = hoje_date
                
            if dt_row == hoje_date:
                dados = parse_robusto(valor_str)
                for maq in ["MS1", "MS2"]:
                    if maq in dados:
                        maq_data = dados[maq]
                        qualidade_sintetizada[maq] = maq_data
                        
                        cur_prod = safe_to_numeric(maq_data.get("producao", maq_data.get("prod", maq_data.get("peso", 0))))
                        cur_l1 = safe_to_numeric(maq_data.get("l1", 0.0))
                        cur_l2 = safe_to_numeric(maq_data.get("l2", 0.0))
                        
                        # 🚨 DETECTOR DE RESET (Se a produção caiu mais de 20t, a máquina resetou o lote!)
                        if cur_prod < acumuladores[maq]["last_prod"] and (acumuladores[maq]["last_prod"] - cur_prod) > 20:
                            acumuladores[maq]["acumulado_prod"] += acumuladores[maq]["last_prod"]
                            acumuladores[maq]["acumulado_l1"] += acumuladores[maq]["last_l1"]
                            acumuladores[maq]["acumulado_l2"] += acumuladores[maq]["last_l2"]
                        
                        acumuladores[maq]["last_prod"] = cur_prod
                        acumuladores[maq]["last_l1"] = cur_l1
                        acumuladores[maq]["last_l2"] = cur_l2

# Fallback de segurança se a aba histórica falhar (Puxa o Cache_Painel)
if not qualidade_sintetizada:
    qualidade_sintetizada = parse_robusto(cache_dict.get("qualidade", "{}"))
    for maq in ["MS1", "MS2"]:
        if maq in qualidade_sintetizada:
            acumuladores[maq]["last_prod"] = safe_to_numeric(qualidade_sintetizada[maq].get("producao", 0))
            acumuladores[maq]["last_l1"] = safe_to_numeric(qualidade_sintetizada[maq].get("l1", 0))
            acumuladores[maq]["last_l2"] = safe_to_numeric(qualidade_sintetizada[maq].get("l2", 0))

# 3. Consolidação Final das Máquinas
q_ms1 = qualidade_sintetizada.get("MS1", {})
q_ms2 = qualidade_sintetizada.get("MS2", {})

prod_ms1 = acumuladores["MS1"]["acumulado_prod"] + acumuladores["MS1"]["last_prod"]
q_ms1["l1"] = acumuladores["MS1"]["acumulado_l1"] + acumuladores["MS1"]["last_l1"]
q_ms1["l2"] = acumuladores["MS1"]["acumulado_l2"] + acumuladores["MS1"]["last_l2"]
q_ms1["producao"] = prod_ms1

prod_ms2 = acumuladores["MS2"]["acumulado_prod"] + acumuladores["MS2"]["last_prod"]
q_ms2["l1"] = acumuladores["MS2"]["acumulado_l1"] + acumuladores["MS2"]["last_l1"]
q_ms2["l2"] = acumuladores["MS2"]["acumulado_l2"] + acumuladores["MS2"]["last_l2"]
q_ms2["producao"] = prod_ms2

prod_hoje_calc = prod_ms1 + prod_ms2

# Cálculos temporais e estimativas
horas_passadas_prod = max(0.1, agora.hour + (agora.minute / 60.0))
prev_prod = (prod_hoje_calc / horas_passadas_prod) * 24

horas_produtivas = sum((1.0 if h > agora.hour else (1.0 - (agora.minute / 60.0))) * (0.0 if 0 <= h < 8 and agora.weekday() in (0, 6) else (6.25 / 8.0)) for h in range(agora.hour, 24))
cap_maxima_restante = horas_produtivas * 500.0

total_veiculos_fisicos = sum(dados_patio.get(k, {}).get("veiculos", 0) for k in ["00", "01", "FC"]) if dados_patio else 0
vol_patio_disponivel = sum(dados_patio.get(k, {}).get("peso", 0.0) for k in ["00", "01", "FC"]) if dados_patio else 0.0
prev_carr = vol_hoje + min(cap_maxima_restante, vol_patio_disponivel)

# ==============================================================================
# CABEÇALHO SUPERIOR E PREVISÕES
# ==============================================================================
# 1. CABEÇALHO (LOGO, TEXTOS E BOTÃO) - Agora com alinhamento central vertical!
col_logo, col_desc, col_status, col_btn = st.columns([1.5, 2.5, 2.5, 1.2], vertical_alignment="center")

with col_logo:
    try:
        st.image("logo_alove.png", use_container_width=True)
    except:
        st.markdown("<h3 style='margin:0; color:#00f3ff; font-style:italic; font-weight: 900;'>A.L.O.V.E.</h3>", unsafe_allow_html=True)

with col_desc:
    st.markdown("""
        <div style="border-left: 2px solid #1c2b42; padding-left: 15px; height: 100%;">
            <span style="color: #e2e8f0; font-size: 0.85rem; font-weight: 600; line-height: 1.4; display: inline-block;">
                Assistente Logístico Virtual<br>da Expedição
            </span>
        </div>
    """, unsafe_allow_html=True)

with col_status:
    st.markdown(f"""
        <div style="text-align: right;">
            <div style="color: #00D672; font-size: 0.85rem; font-weight: 800; display: flex; justify-content: flex-end; align-items: center; gap: 6px;">
                <span style="font-size: 1.1rem;">🎯</span> Sistema Online
            </div>
            <div style="color: #94a3b8; font-size: 0.7rem; font-weight: 600; margin-top: 2px;">
                Sincronizado: {ultima_att}
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_btn:
    if st.button("🔄 Atualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True) # Espaçamento entre cabeçalho e os blocos

# 2. BLOCOS DE PREVISÕES (NEON CYBERPUNK)
html_previsoes = f"""
<div class="prev-container">
    <div class="prev-card-prod">
        <div class="prev-title">📈 Prev. Produção</div>
        <div class="prev-val">{prev_prod:,.0f} <span style="font-size:0.9rem;">t</span></div>
        <div class="prev-sub">Ritmo 24h Base MS1+MS2</div>
    </div>
    <div class="prev-card-carr">
        <div class="prev-title">🎯 Prev. Expedição</div>
        <div class="prev-val">{prev_carr:,.0f} <span style="font-size:0.9rem;">t</span></div>
        <div class="prev-sub">Realizado + Cap. Pátio</div>
    </div>
</div>
"""
st.markdown(html_previsoes, unsafe_allow_html=True)

# 3. OBSERVAÇÕES OPERACIONAIS
if observacoes and observacoes.strip() not in ["", "None"]:
    cor_bg, cor_border, cor_txt = ("#0d2417", "#00D672", "#00D672") if "Normal" in observacoes else ("#2b1111", "#E74C3C", "#ff9999")
    st.markdown(f'<div style="background-color: {cor_bg}; border-left: 4px solid {cor_border}; padding: 10px 14px; margin-bottom: 12px; border-radius: 6px;"><div style="color: {cor_border}; font-size: 11px; font-weight: 800; text-transform: uppercase;">📋 Observação Operacional</div><div style="color: {cor_txt}; font-size: 12px; font-weight: 600; white-space: pre-wrap;">{observacoes}</div></div>', unsafe_allow_html=True)# ==============================================================================
# 📦 BLOCO 1: PÁTIO DE VEÍCULOS
# ==============================================================================
html_patio = '<details class="master-box" style="border-left-color: #38bdf8;">'
html_patio += f'<summary><div class="master-metric-title">🚛 Pátio da Fábrica (Tempo Real)</div><div class="master-metric-val">{total_veiculos_fisicos} <span style="font-size:1.1rem; color:#94a3b8;">Veículos Físicos</span></div><div class="master-metric-sub" style="color: #38bdf8;">Carga Disponível p/ Carregar: {vol_patio_disponivel:,.0f} t</div></summary>'
html_patio += '<div class="master-content patio-grid">'

if dados_patio:
    blocos_patio = [("🚙 Prog/Chegando", "PR", "#94A3B8"), ("📋 Checklist", "00", "#E5B800"), ("🚛 Apoio", "01", "#E67E22"), ("✅ Fila", "FC", "#00D672"), ("📄 Termo SAP", "TR", "#3498DB")]
    for tit, chv, cor in blocos_patio:
        v_qtd = dados_patio.get(chv, {}).get("veiculos", 0)
        v_ton = dados_patio.get(chv, {}).get("peso", 0.0)
        html_patio += f"<div class='card-patio-sub' style='border-left-color: {cor};'><div class='card-patio-title' style='color: {cor};'>{tit}</div><div class='card-patio-qtd'>{int(v_qtd)} <span style='font-size:0.75rem; color:#94a3b8;'>veíc</span></div><div class='card-patio-ton'>{v_ton:,.0f} t</div></div>"
else:
    html_patio += '<div style="color:gray;">Sem dados de pátio.</div>'

html_patio += "</div></details>"
st.markdown(html_patio, unsafe_allow_html=True)

# ==============================================================================
# 🏭 BLOCO 2: PRODUÇÃO DO DIA (COM L1, L2, ALVURA E PH)
# ==============================================================================
html_prod_content = ""

for maq, q_dados, p_maq in [("MS1", q_ms1, prod_ms1), ("MS2", q_ms2, prod_ms2)]:
    if q_dados:
        mat_maq = q_dados.get("material", q_dados.get("mat", "--"))
        q_suj = safe_to_numeric(q_dados.get('sujidade', 0.0))
        q_visc = safe_to_numeric(q_dados.get('viscosidade', 0.0))
        q_teor = safe_to_numeric(q_dados.get('teor', 0.0))
        q_alvura = safe_to_numeric(q_dados.get('alvura', 0.0))
        q_ph = safe_to_numeric(q_dados.get('ph', 0.0))
        
        l1 = safe_to_numeric(q_dados.get('l1', 0.0))
        l2 = safe_to_numeric(q_dados.get('l2', 0.0))
        
        c_suj = "#00D672" if q_suj <= 2.5 else "#E74C3C"
        c_vis = "#00D672" if q_visc >= 650 else "#E74C3C"
        c_teo = "#00D672" if q_teor >= 88.5 else "#E74C3C"
        c_alv = "#38bdf8"
        c_ph = "#38bdf8"

        html_prod_content += f"""
        <div style='background-color: #111c2e; border: 1px solid #1c2b42; border-radius: 8px; padding: 12px; margin-bottom: 8px;'>
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:2px;'>
                <span style='color:#ffffff; font-weight:800; font-size:1rem;'>⚙️ {maq}</span>
                <span style='color:#FF9F1C; font-weight:800; font-size:0.85rem;'>📦 MAT: {mat_maq}</span>
                <span style='color:#3498DB; font-weight:900; font-size:1.1rem;'>{p_maq:,.0f} t</span>
            </div>
            
            <div style='display:flex; justify-content:flex-end; gap: 12px; margin-bottom: 10px; font-size: 0.75rem; color: #94a3b8; font-weight: 700;'>
                <span>L1: <span style='color:#ffffff;'>{l1:,.0f} t</span></span>
                <span>L2: <span style='color:#ffffff;'>{l2:,.0f} t</span></span>
            </div>
            
            <div style='display: flex; justify-content: space-between; text-align: center; border-top: 1px dashed #1c2b42; padding-top: 10px;'>
                <div>
                    <div style='font-size:0.65rem; color:#94a3b8; text-transform:uppercase;'>Sujidade</div>
                    <div style='font-size:0.95rem; font-weight:bold; color:{c_suj};'>{q_suj:.2f}</div>
                </div>
                <div>
                    <div style='font-size:0.65rem; color:#94a3b8; text-transform:uppercase;'>Viscosid.</div>
                    <div style='font-size:0.95rem; font-weight:bold; color:{c_vis};'>{q_visc:,.0f}</div>
                </div>
                <div>
                    <div style='font-size:0.65rem; color:#94a3b8; text-transform:uppercase;'>Teor</div>
                    <div style='font-size:0.95rem; font-weight:bold; color:{c_teo};'>{q_teor:.2f}%</div>
                </div>
                <div>
                    <div style='font-size:0.65rem; color:#94a3b8; text-transform:uppercase;'>Alvura</div>
                    <div style='font-size:0.95rem; font-weight:bold; color:{c_alv};'>{q_alvura:.2f}</div>
                </div>
                <div>
                    <div style='font-size:0.65rem; color:#94a3b8; text-transform:uppercase;'>pH</div>
                    <div style='font-size:0.95rem; font-weight:bold; color:{c_ph};'>{q_ph:.2f}</div>
                </div>
            </div>
        </div>
        """
    else:
        html_prod_content += f"<div style='color:gray; padding:10px 0;'>Aguardando dados da {maq}...</div>"

html_prod_completo = f"""
<details class="master-box" style="border-left-color: #E5B800;">
    <summary>
        <div class="master-metric-title">🏭 Produção de Celulose</div>
        <div class="master-metric-val">{prod_hoje_calc:,.0f} <span style="font-size:1.1rem; color:#94a3b8;">TON</span></div>
        <div class="master-metric-sub" style="color: #94a3b8;">MS1: {prod_ms1:,.0f} t | MS2: {prod_ms2:,.0f} t</div>
    </summary>
    <div class="master-content">
        {html_prod_content}
    </div>
</details>
"""
st.markdown(html_prod_completo.replace('\n', ''), unsafe_allow_html=True)

# ==============================================================================
# 🚚 BLOCO 3: EXPEDIÇÃO DO DIA & TURNOS
# ==============================================================================
dados_exp_hoje = buscar_dados_turnos_historico(hoje_date)
dados_exp_ontem = buscar_dados_turnos_historico(ontem_date)

vol_exp_hoje = vol_hoje if vol_hoje > 0 else (dados_exp_hoje.get("total_dia", 0.0) if dados_exp_hoje else 0.0)
vol_exp_ontem = dados_exp_ontem.get("total_dia", 0.0) if dados_exp_ontem else 0.0

html_hoje = "<div style='font-size:0.75rem; font-weight:800; color:#00D672; text-transform:uppercase; margin-bottom:10px; text-align:left;'>Turnos em Operação Hoje:</div>"
if dados_exp_hoje and "turnos" in dados_exp_hoje:
    ativo_key = dados_exp_hoje.get("ativo_key")
    html_hoje += "<div style='display:flex; gap:6px; margin-bottom:8px;'>"
    chart_data_hoje = []
    for t in dados_exp_hoje["turnos"]:
        is_atv = (t["key"] == ativo_key)
        cor_b = "#FF9F1C" if is_atv else "#1c2b42"
        cor_txt = "#FF9F1C" if is_atv else "#ffffff"
        sub_txt = f"{t['horario']} (ATIVO)" if is_atv else t['horario']
        
        html_hoje += f"<div style='flex:1; background-color:#111c2e; border:1.5px solid {cor_b}; border-radius:8px; padding:8px; text-align:center;'><div style='font-size:0.75rem; font-weight:800; color:{cor_txt};'>{t['letra']}</div><div style='font-size:1.1rem; font-weight:900; color:#ffffff;'>{t['vol']:,.0f} t</div><div style='font-size:0.65rem; color:#94a3b8;'>{sub_txt}</div></div>"
        chart_data_hoje.append({"label": t['letra'], "value": t['vol'], "text": f"{t['vol']:,.0f} t", "color": "#FF9F1C" if is_atv else "#00D672"})
    html_hoje += "</div>"
    html_hoje += build_vertical_chart(chart_data_hoje)
else:
    html_hoje += "<div style='color:gray; text-align:left;'>Aguardando dados de hoje...</div>"

html_ontem = f"<div style='font-size:0.75rem; font-weight:800; color:#38bdf8; text-transform:uppercase; margin-bottom:10px; text-align:left;'>Fechamento de Ontem ({ontem_date.strftime('%d/%m')}):</div>"
if dados_exp_ontem and "turnos" in dados_exp_ontem:
    html_ontem += "<div style='display:flex; gap:6px; margin-bottom:8px;'>"
    chart_data_ontem = []
    for t in dados_exp_ontem["turnos"]:
        html_ontem += f"<div style='flex:1; background-color:#111c2e; border:1.5px solid #1c2b42; border-radius:8px; padding:8px; text-align:center;'><div style='font-size:0.75rem; font-weight:800; color:#38bdf8;'>{t['letra']}</div><div style='font-size:1.1rem; font-weight:900; color:#ffffff;'>{t['vol']:,.0f} t</div><div style='font-size:0.65rem; color:#94a3b8;'>{t['horario']}</div></div>"
        chart_data_ontem.append({"label": t['letra'], "value": t['vol'], "text": f"{t['vol']:,.0f} t", "color": "#38bdf8"})
    html_ontem += "</div>"
    html_ontem += build_vertical_chart(chart_data_ontem)
else:
    html_ontem += "<div style='color:gray; text-align:left;'>Sem dados consolidados de ontem.</div>"

html_exp_completo = f"""
<details class="master-box" style="border-left-color: #00D672;" open>
    <summary>
        <div class="master-metric-title">🚛 Expedição Realizada</div>
        <div class="master-metric-val">{vol_exp_hoje:,.0f} <span style="font-size:1.1rem; color:#94a3b8;">TON</span></div>
        <div class="master-metric-sub" style="color: #00D672;">Consolidado Ontem (D-1): {vol_exp_ontem:,.0f} t</div>
    </summary>
    <div class="master-content css-tabs-exp">
        <div style="text-align: center; margin-bottom: 16px;">
            <input type="radio" name="exp_tabs" id="tab_ontem">
            <label for="tab_ontem" class="lbl-ontem">⏮️ Ontem (D-1)</label>
            
            <input type="radio" name="exp_tabs" id="tab_hoje" checked>
            <label for="tab_hoje" class="lbl-hoje">📅 Hoje</label>
            
            <div class="tab-content-exp" id="content_ontem" style="margin-top: 14px;">
                {html_ontem}
            </div>
            
            <div class="tab-content-exp" id="content_hoje" style="margin-top: 14px;">
                {html_hoje}
            </div>
        </div>
    </div>
</details>
<style>
    .css-tabs-exp label {{
        display: inline-block; padding: 6px 16px; background-color: #162438; color: #94a3b8; 
        border-radius: 6px; font-size: 0.85rem; font-weight: 800; margin: 0 4px; 
        cursor: pointer; border: 1px solid #1c2b42; transition: 0.2s;
    }}
    .css-tabs-exp input[type="radio"]#tab_ontem:checked + label.lbl-ontem {{
        background-color: #38bdf8; color: #0a101d; border-color: #38bdf8;
    }}
    .css-tabs-exp input[type="radio"]#tab_hoje:checked + label.lbl-hoje {{
        background-color: #00D672; color: #0a101d; border-color: #00D672;
    }}
    .tab-content-exp {{ display: none; animation: fadeIn 0.3s ease; }}
    #tab_ontem:checked ~ #content_ontem {{ display: block; }}
    #tab_hoje:checked ~ #content_hoje {{ display: block; }}
</style>
"""
st.markdown(html_exp_completo.replace('\n', ''), unsafe_allow_html=True)

# ==============================================================================
# 📦 BLOCO 4: ESTOQUE TOTAL E MATERIAIS
# ==============================================================================
html_est = '<details class="master-box" style="border-left-color: #9b59b6;">'
html_est += f'<summary><div class="master-metric-title">📦 Estoque Físico no Armazém</div><div class="master-metric-val">{estoque_total:,.0f} <span style="font-size:1.1rem; color:#94a3b8;">TON</span></div><div class="master-metric-sub" style="color: #9b59b6;">Distribuição por Material</div></summary>'
html_est += '<div class="master-content">'

if dados_segregados:
    df_seg = pd.DataFrame(list(dados_segregados.items()), columns=["Material", "Toneladas"]).sort_values(by="Toneladas", ascending=False)
    chart_data_est = []
    for _, row in df_seg.iterrows():
        chart_data_est.append({
            "label": row["Material"],
            "value": row["Toneladas"],
            "text": f"{row['Toneladas']:,.0f} t",
            "color": "#38bdf8"
        })
    html_est += build_vertical_chart(chart_data_est)
else:
    html_est += '<div style="color:gray;">Aguardando detalhamento de material...</div>'

html_est += "</div></details>"
st.markdown(html_est, unsafe_allow_html=True)

# ==============================================================================
# 🚜 BLOCO 5: FROTA
# ==============================================================================
df_frota = carregar_dados_nuvem("Rodizio_Frota")
equip_em_uso_agora = 0

html_frota = '<details class="master-box" style="border-left-color: #E67E22;">'

if not df_frota.empty:
    cols_upper = {str(c).strip().upper(): c for c in df_frota.columns}
    col_t = cols_upper.get("TURNO_JANELA", df_frota.columns[0])
    col_posto = cols_upper.get("POSTO", df_frota.columns[1] if len(df_frota.columns) > 1 else df_frota.columns[0])
    col_status = cols_upper.get("STATUS_RODIZIO", cols_upper.get("STATUS", df_frota.columns[-1]))
    col_equip = cols_upper.get("EQUIPAMENTO", df_frota.columns[2] if len(df_frota.columns) > 2 else df_frota.columns[0])

    turnos_frota = df_frota[col_t].dropna().unique().tolist()
    
    idx_sug = next((i for i, t in enumerate(turnos_frota) if ("00:00" in str(t) and 0 <= agora.hour < 8) or ("08:00" in str(t) and 8 <= agora.hour < 16) or ("16:00" in str(t) and 16 <= agora.hour <= 23)), 0)
    turno_atual_str = turnos_frota[idx_sug] if turnos_frota else ""
    df_f_agora = df_frota[df_frota[col_t] == turno_atual_str] if turnos_frota else df_frota
    
    op1 = df_f_agora[(df_f_agora[col_posto].astype(str).str.contains("CARREG", case=False, na=False)) & (df_f_agora[col_status].astype(str).str.contains("OPERA", case=False, na=False))]
    op2 = df_f_agora[(df_f_agora[col_posto].astype(str).str.contains("LINHA", case=False, na=False)) & (df_f_agora[col_status].astype(str).str.contains("OPERA", case=False, na=False))]
    op3 = df_f_agora[(df_f_agora[col_posto].astype(str).str.contains("TALHA", case=False, na=False) | df_f_agora[col_equip].astype(str).str.contains("TALHA", case=False, na=False)) & (df_f_agora[col_status].astype(str).str.contains("OPERA", case=False, na=False))]
    equip_em_uso_agora = len(op1) + len(op2) + len(op3)

    html_frota += f'<summary><div class="master-metric-title">🚜 Equipamentos em Operação</div><div class="master-metric-val">{equip_em_uso_agora} <span style="font-size:1.1rem; color:#94a3b8;">Em Atividade Agora</span></div><div class="master-metric-sub" style="color: #E67E22;">Carregamento, Linhas e Talhas</div></summary>'
    html_frota += '<div class="master-content css-tabs">'
    
    html_frota += '<div style="text-align: center; margin-bottom: 12px;">'
    html_frota += '<div style="color: #94a3b8; font-size: 0.85rem; font-weight: bold; margin-bottom: 8px;">Selecione o Turno / Janela:</div>'
    for i, t_str in enumerate(turnos_frota):
        checked = "checked" if i == idx_sug else ""
        html_frota += f'<input type="radio" name="ftabs" id="ftab{i}" {checked}><label for="ftab{i}">{t_str}</label>'
    html_frota += '</div>'
    
    for i, t_str in enumerate(turnos_frota):
        df_t = df_frota[df_frota[col_t] == t_str]
        carr = df_t[(df_t[col_posto].astype(str).str.contains("CARREG", case=False, na=False)) & (df_t[col_status].astype(str).str.contains("OPERA", case=False, na=False))][col_equip].tolist()
        linha = df_t[(df_t[col_posto].astype(str).str.contains("LINHA", case=False, na=False)) & (df_t[col_status].astype(str).str.contains("OPERA", case=False, na=False))][col_equip].tolist()
        talhas = df_t[(df_t[col_posto].astype(str).str.contains("TALHA", case=False, na=False) | df_t[col_equip].astype(str).str.contains("TALHA", case=False, na=False)) & (df_t[col_status].astype(str).str.contains("OPERA", case=False, na=False))][col_equip].tolist()
        paradas = df_t[df_t[col_status].astype(str).str.contains("STAND|PARAD|MANUT", case=False, na=False)][col_equip].tolist()

        str_carr = " ".join([f"<span class='tag-box tag-op'>{t}</span>" for t in carr]) if carr else "<span style='color:gray; font-size:0.8rem;'>Nenhum</span>"
        str_linha = " ".join([f"<span class='tag-box tag-op'>{t}</span>" for t in linha]) if linha else "<span style='color:gray; font-size:0.8rem;'>Nenhum</span>"
        str_talha = " ".join([f"<span class='tag-box tag-talha'>{t}</span>" for t in talhas]) if talhas else "<span style='color:gray; font-size:0.8rem;'>Nenhuma</span>"
        str_parada = " ".join([f"<span class='tag-box tag-standby'>{t}</span>" for t in paradas]) if paradas else "<span style='color:gray; font-size:0.8rem;'>Nenhum</span>"

        html_frota += f'<div class="tab-content" id="fcontent{i}">'
        html_frota += f'<div style="margin-bottom:6px; font-size:0.85rem; color:#fff; font-weight:800; margin-top:8px;">🟢 Empilhadeiras - Carregamento:</div><div style="margin-bottom:14px;">{str_carr}</div>'
        html_frota += f'<div style="margin-bottom:6px; font-size:0.85rem; color:#fff; font-weight:800;">🟢 Empilhadeiras - Linha:</div><div style="margin-bottom:14px;">{str_linha}</div>'
        html_frota += f'<div style="margin-bottom:6px; font-size:0.85rem; color:#fff; font-weight:800;">🏗️ Pontes Rolantes / Talhas:</div><div style="margin-bottom:14px;">{str_talha}</div>'
        html_frota += f'<div style="margin-bottom:6px; font-size:0.85rem; color:#fff; font-weight:800;">🔴 Stand-by / Paradas:</div><div style="margin-bottom:12px;">{str_parada}</div>'
        html_frota += '</div>'
    html_frota += '</div>'
else:
    html_frota += '<summary><div class="master-metric-title">🚜 Equipamentos</div></summary><div class="master-content"><div style="color:gray;">Aba Rodizio_Frota indisponível ou sem dados.</div></div>'

html_frota += '</details>'
st.markdown(html_frota, unsafe_allow_html=True)

# ==============================================================================
# ⛽ BLOCO 6: CONSUMO GLP MENSAL
# ==============================================================================
df_glp = carregar_dados_nuvem("Abastecimentos_GLP", cabecalho=None)
html_glp = '<details class="master-box" style="border-left-color: #fd7e14;">'

if not df_glp.empty and len(df_glp.columns) >= 8:
    df_g = pd.DataFrame()
    df_g["DATA_DT"] = pd.to_datetime(df_glp.iloc[:, 2].astype(str).str.strip(), format="%d/%m/%Y", errors="coerce")
    df_g = df_g.dropna(subset=["DATA_DT"])
    
    if not df_g.empty:
        df_g["MES_ANO"] = df_g["DATA_DT"].dt.strftime("%m/%Y")
        df_g["MAQUINA"] = df_glp.iloc[:, 5].astype(str).str.strip()
        df_g["KG_NUM"] = df_glp.iloc[:, 7].apply(safe_to_numeric)
        
        meses_disp = df_g["MES_ANO"].dropna().unique().tolist()
        if meses_disp:
            meses_disp.sort(key=lambda x: datetime.strptime(x, "%m/%Y"))
            mes_recente = meses_disp[-1]
            df_mes_recente = df_g[df_g["MES_ANO"] == mes_recente]
            total_glp_recente = df_mes_recente["KG_NUM"].sum()

            html_glp += f'<summary><div class="master-metric-title">⛽ Consumo de GLP da Frota</div><div class="master-metric-val">{total_glp_recente:,.0f} <span style="font-size:1.1rem; color:#94a3b8;">KG</span></div><div class="master-metric-sub" style="color: #fd7e14;">Acumulado do Mês Atual ({mes_recente})</div></summary>'
            html_glp += '<div class="master-content">'
            
            df_maq = df_mes_recente.groupby("MAQUINA")["KG_NUM"].sum().reset_index().sort_values(by="KG_NUM", ascending=False)
            
            if not df_maq.empty:
                chart_data_glp = []
                for _, row in df_maq.iterrows():
                    chart_data_glp.append({
                        "label": row["MAQUINA"],
                        "value": row["KG_NUM"],
                        "text": f"{row['KG_NUM']:,.0f} kg",
                        "color": "#fd7e14"
                    })
                html_glp += build_vertical_chart(chart_data_glp)
            else:
                html_glp += '<div style="color:gray; text-align:center;">Sem consumo registrado.</div>'
            html_glp += '</div>'
else:
    html_glp += '<summary><div class="master-metric-title">⛽ Consumo de GLP</div></summary><div class="master-content"><div style="color:gray;">Planilha indisponível.</div></div>'

html_glp += '</details>'
st.markdown(html_glp, unsafe_allow_html=True)

st.markdown("<br><center><span style='color:#94a3b8; font-size: 0.75rem;'>Logística MI | A.L.O.V.E Core Mobile Dashboard</span></center>", unsafe_allow_html=True)
