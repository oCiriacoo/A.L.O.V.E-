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
# 🎨 CSS AVANÇADO (CARDS NEON + EXPANDERS + GRÁFICOS VERTICAIS + FROTA TABS)
# ==============================================================================
st.markdown("""
    <style>
        .block-container {
            padding-top: 3.5rem;
            padding-bottom: 2rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
        
        input[type="radio"] { display: none; }
        
        /* ---------------- PREVISÕES ---------------- */
        .prev-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 14px;
        }
        
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

        /* ---------------- MASTER BOX ---------------- */
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
        
        .master-metric-title { color: #94a3b8; font-size: 1.1rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; padding-right: 20px;}
        .master-metric-val { color: #ffffff; font-size: 2.4rem; font-weight: 900; line-height: 1.1; margin-bottom: 6px; }
        .master-metric-sub { font-size: 0.95rem; font-weight: 700; }
        .master-content { background-color: #0a101d; padding: 16px; border-top: 1px dashed #1c2b42; }

        /* ---------------- PÁTIO E EXPEDIÇÃO ---------------- */
        .patio-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
        .card-patio-sub { background-color: #111c2e; border-radius: 8px; padding: 10px; border-left: 4px solid; border: 1px solid #1c2b42;}
        .card-patio-title { font-weight: 800; font-size: 0.95rem; margin-bottom: 4px; }
        .card-patio-qtd { font-size: 1.4rem; font-weight: 900; color: #ffffff; }
        .card-patio-ton { font-size: 0.85rem; color: #94a3b8; font-weight: 600; }

        .css-tabs-exp label {
            display: inline-block; padding: 6px 16px; background-color: #162438; color: #94a3b8; 
            border-radius: 6px; font-size: 0.85rem; font-weight: 800; margin: 0 4px; 
            cursor: pointer; border: 1px solid #1c2b42; transition: 0.2s;
        }
        .css-tabs-exp input[type="radio"]#tab_ontem:checked + label.lbl-ontem { background-color: #38bdf8; color: #0a101d; border-color: #38bdf8; }
        .css-tabs-exp input[type="radio"]#tab_hoje:checked + label.lbl-hoje { background-color: #00D672; color: #0a101d; border-color: #00D672; }
        .tab-content-exp { display: none; animation: fadeIn 0.3s ease; }
        #tab_ontem:checked ~ #content_ontem { display: block; }
        #tab_hoje:checked ~ #content_hoje { display: block; }

        /* ---------------- FROTA (DKRO) ---------------- */
        .frota-tabs-main { display: flex; gap: 8px; justify-content: center; margin-bottom: 16px; }
        .frota-tabs-main label { padding: 8px 16px; background-color: #162438; color: #94a3b8; border-radius: 6px; cursor: pointer; border: 1px solid #1c2b42; font-weight: 800; font-size: 0.9rem; transition: 0.2s; }
        .frota-tabs-sub { display: flex; gap: 6px; justify-content: center; margin-bottom: 14px; }
        .frota-tabs-sub label { padding: 6px 12px; background-color: #111c2e; color: #64748b; border-radius: 6px; cursor: pointer; border: 1px solid #1c2b42; font-weight: 800; font-size: 0.8rem; transition: 0.2s; }

        .f-rad-main, .f-rad-sub { display: none; }
        .f-content-dia { display: none; animation: fadeIn 0.3s ease; }
        
        #frota_dia_ontem:checked ~ .frota-tabs-main .lbl-f-ontem { background-color: #38bdf8; color: #0a101d; border-color: #38bdf8; }
        #frota_dia_hoje:checked ~ .frota-tabs-main .lbl-f-hoje { background-color: #E67E22; color: #0a101d; border-color: #E67E22; }
        #frota_dia_ontem:checked ~ #frota_box_ontem { display: block; }
        #frota_dia_hoje:checked ~ #frota_box_hoje { display: block; }

        .f-content-turno-hoje, .f-content-turno-ontem { display: none; background-color: #05080f; padding: 14px; border-radius: 8px; border: 1px solid #1c2b42; text-align: left; }
        #frota_h_00:checked ~ .frota-tabs-sub .lbl-h-00, #frota_h_08:checked ~ .frota-tabs-sub .lbl-h-08, #frota_h_16:checked ~ .frota-tabs-sub .lbl-h-16, #frota_o_00:checked ~ .frota-tabs-sub .lbl-o-00, #frota_o_08:checked ~ .frota-tabs-sub .lbl-o-08, #frota_o_16:checked ~ .frota-tabs-sub .lbl-o-16 { background-color: #0d2417; color: #00D672; border-color: #00D672; }
        
        #frota_h_00:checked ~ #frota_h_content_00, #frota_h_08:checked ~ #frota_h_content_08, #frota_h_16:checked ~ #frota_h_content_16, #frota_o_00:checked ~ #frota_o_content_00, #frota_o_08:checked ~ #frota_o_content_08, #frota_o_16:checked ~ #frota_o_content_16 { display: block; }

        .f-tag-ok { background-color: #00D672; color: #0a101d; }
        .f-tag-avaria { background-color: #E74C3C; color: #ffffff; }
        .f-tag-aten { background-color: #FFD600; color: #0a101d; }
        .f-tag-title { font-size: 0.85rem; color: #ffffff; font-weight: 800; margin-bottom: 8px; border-bottom: 1px dashed #1c2b42; padding-bottom: 4px; }
        .f-tag-container { margin-bottom: 16px; }
        .tag-box { display: inline-block; padding: 6px 10px; margin: 3px; border-radius: 6px; font-weight: 800; font-size: 0.8rem; text-align: center; }

        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    </style>
""", unsafe_allow_html=True)

SHEET_ID = "10FluiIwlynIlPDA74QI8mpHSIrAc-62H1hZNRBsvfCA"

def forcar_par(valor):
    val_int = int(round(float(valor or 0)))
    if val_int % 2 != 0:
        val_int += 1
    return val_int

@st.cache_data(ttl=20)
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

def parse_robusto(texto):
    if not texto or str(texto).strip() in ["", "None"]: return {}
    texto_str = str(texto).strip()
    try: return json.loads(texto_str)
    except:
        try: return ast.literal_eval(texto_str)
        except: return {}

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

        vol_t1 = forcar_par(max(0.0, corte_08 - corte_00)) if corte_08 > 0 else 0
        if is_hoje:
            vol_t2 = forcar_par(max(0.0, corte_16 - corte_08) if agora_br.hour >= 16 else (max(0.0, corte_fim - corte_08) if agora_br.hour >= 8 else 0.0))
            vol_t3 = forcar_par(max(0.0, corte_fim - corte_16) if agora_br.hour >= 16 else 0.0)
        else:
            vol_t2 = forcar_par(max(0.0, corte_16 - corte_08) if corte_16 > 0 else 0.0)
            vol_t3 = forcar_par(max(0.0, corte_fim - corte_16) if corte_fim > 0 else 0.0)

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

def classificar_kpi_mobile(valor, tipo):
    if valor == 0.0: return "#94a3b8" 
    if tipo == "alvura":
        if valor < 88.50: return "#E74C3C"
        elif valor < 88.70: return "#FFD600"
        return "#00D672"
    elif tipo == "sujidade":
        if valor > 2.50: return "#E74C3C"
        elif valor > 2.00: return "#FFD600"
        return "#00D672"
    elif tipo == "viscosidade":
        if valor < 650.0: return "#E74C3C"
        elif valor < 680.0: return "#FFD600"
        return "#00D672"
    elif tipo == "ph":
        if valor > 0 and (valor < 5.50 or valor > 8.50): return "#E74C3C"
        elif valor > 0 and ((5.50 <= valor < 6.00) or (8.00 < valor <= 8.50)): return "#FFD600"
        return "#00D672"
    return "#00D672"

# ==============================================================================
# 🚀 CARREGAMENTO DAS ABAS MOBILE GERADAS PELO CORE
# ==============================================================================
df_dash = carregar_dados_nuvem("Mobile_Dashboard", cabecalho=0)
df_qual = carregar_dados_nuvem("Mobile_Qualidade", cabecalho=0)
df_alertas = carregar_dados_nuvem("Mobile_Alertas", cabecalho=0)
df_cache = carregar_dados_nuvem("Cache_Painel", cabecalho=0)

cache_dict = {str(row.iloc[0]).strip(): str(row.iloc[1]).strip() for _, row in df_cache.iterrows()} if not df_cache.empty else {}
dados_segregados = parse_robusto(cache_dict.get("dados_segregados", "{}"))

ultima_att = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
vol_hoje = 0
vol_ontem = 0
prev_carr = 0
prod_hoje_calc = 0
prev_prod = 0
estoque_total = 0
status_transbordo = "NORMAL"
ritmo_torre = "NORMAL"

dados_patio = {
    "PR": {"veiculos": 0, "peso": 0},
    "00": {"veiculos": 0, "peso": 0},
    "01": {"veiculos": 0, "peso": 0},
    "FC": {"veiculos": 0, "peso": 0},
    "TR": {"veiculos": 0, "peso": 0}
}

if not df_dash.empty:
    row_d = df_dash.iloc[0]
    ultima_att = str(row_d.get("DATA_HORA", ultima_att))
    vol_hoje = forcar_par(safe_to_numeric(row_d.get("EXPEDICAO_HOJE", 0)))
    vol_ontem = forcar_par(safe_to_numeric(row_d.get("EXPEDICAO_ONTEM", 0)))
    prev_carr = forcar_par(safe_to_numeric(row_d.get("PREV_EXPEDICAO", 0)))
    prod_hoje_calc = forcar_par(safe_to_numeric(row_d.get("PRODUCAO_HOJE", 0)))
    prev_prod = forcar_par(safe_to_numeric(row_d.get("PREV_PRODUCAO", 0)))
    estoque_total = forcar_par(safe_to_numeric(row_d.get("ESTOQUE_TOTAL", 0)))
    status_transbordo = str(row_d.get("STATUS_TRANSBORDO", "NORMAL"))
    ritmo_torre = str(row_d.get("RITMO_TORRE", "NORMAL"))
    
    dados_patio["PR"] = {"veiculos": int(safe_to_numeric(row_d.get("PR_VEIC", 0))), "peso": forcar_par(safe_to_numeric(row_d.get("PR_TON", 0)))}
    dados_patio["00"] = {"veiculos": int(safe_to_numeric(row_d.get("00_VEIC", 0))), "peso": forcar_par(safe_to_numeric(row_d.get("00_TON", 0)))}
    dados_patio["01"] = {"veiculos": int(safe_to_numeric(row_d.get("01_VEIC", 0))), "peso": forcar_par(safe_to_numeric(row_d.get("01_TON", 0)))}
    dados_patio["FC"] = {"veiculos": int(safe_to_numeric(row_d.get("FC_VEIC", 0))), "peso": forcar_par(safe_to_numeric(row_d.get("FC_TON", 0)))}
    dados_patio["TR"] = {"veiculos": int(safe_to_numeric(row_d.get("TR_VEIC", 0))), "peso": forcar_par(safe_to_numeric(row_d.get("TR_TON", 0)))}

total_veiculos_fisicos = dados_patio["00"]["veiculos"] + dados_patio["01"]["veiculos"] + dados_patio["FC"]["veiculos"]
vol_patio_disponivel = forcar_par(dados_patio["00"]["peso"] + dados_patio["01"]["peso"] + dados_patio["FC"]["peso"])

dados_maquinas = {"MS1": {}, "MS2": {}}
if not df_qual.empty:
    for _, r_q in df_qual.iterrows():
        m_nome = str(r_q.get("MAQUINA", "")).strip().upper()
        if m_nome in dados_maquinas:
            dados_maquinas[m_nome] = {
                "material": str(r_q.get("MATERIAL", "--")),
                "alvura": safe_to_numeric(r_q.get("ALVURA", 0)),
                "sujidade": safe_to_numeric(r_q.get("SUJIDADE", 0)),
                "viscosidade": safe_to_numeric(r_q.get("VISCOSIDADE", 0)),
                "ph": safe_to_numeric(r_q.get("PH", 0)),
                "producao": forcar_par(safe_to_numeric(r_q.get("PROD_TOTAL", 0))),
                "l1": forcar_par(safe_to_numeric(r_q.get("PROD_LINHA_1", 0))),
                "l2": forcar_par(safe_to_numeric(r_q.get("PROD_LINHA_2", 0))),
                "desclassificando": str(r_q.get("DESCLASSIFICANDO", "NAO")).upper() == "SIM"
            }

# ==============================================================================
# CABEÇALHO SUPERIOR E PREVISÕES
# ==============================================================================
col_logo, col_status, col_btn = st.columns([3.5, 2.5, 1.2], vertical_alignment="center")

with col_logo:
    try:
        st.image("logo_alove.png", use_container_width=True)
    except:
        st.markdown("<h3 style='margin:0; color:#00f3ff; font-style:italic; font-weight: 900;'>A.L.O.V.E.</h3>", unsafe_allow_html=True)

with col_status:
    st.markdown(f"""
        <div style="text-align: right;">
            <div style="color: #00D672; font-size: 0.85rem; font-weight: 800; display: flex; justify-content: flex-end; align-items: center; gap: 6px;">
                <span style="font-size: 1.1rem;">🎯</span> {ritmo_torre}
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

st.markdown("<br>", unsafe_allow_html=True)

html_previsoes = f"""
<div class="prev-container">
    <div class="prev-card-prod">
        <div class="prev-title">📈 Prev. Produção</div>
        <div class="prev-val">{prev_prod:,.0f} <span style="font-size:0.9rem;">t</span></div>
    </div>
    <div class="prev-card-carr">
        <div class="prev-title">🎯 Prev. Expedição</div>
        <div class="prev-val">{prev_carr:,.0f} <span style="font-size:0.9rem;">t</span></div>
    </div>
</div>
"""
st.markdown(html_previsoes, unsafe_allow_html=True)

if not df_alertas.empty:
    linhas_alt = []
    tem_critico = False
    for _, alt_row in df_alertas.iterrows():
        txt_alt = str(alt_row.get("ALERTA", "")).strip()
        nv_alt = str(alt_row.get("NIVEL", "")).strip().upper()
        if txt_alt and "Normal" not in txt_alt:
            linhas_alt.append(f"• {txt_alt}")
            if nv_alt == "CRITICO": tem_critico = True

    if linhas_alt:
        cor_b = "#E74C3C" if tem_critico else "#FF9F1C"
        bg_b = "#2b1111" if tem_critico else "#24180d"
        txt_cor = "#ff9999" if tem_critico else "#ffd299"
        corpo_alt = "<br>".join(linhas_alt[:4])
        st.markdown(f"""
            <div style="background-color: {bg_b}; border-left: 4px solid {cor_b}; padding: 10px 14px; margin-bottom: 12px; border-radius: 6px;">
                <div style="color: {cor_b}; font-size: 11px; font-weight: 800; text-transform: uppercase;">🚨 Observações & Alertas Críticos</div>
                <div style="color: {txt_cor}; font-size: 12px; font-weight: 600; margin-top: 4px;">{corpo_alt}</div>
            </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# 🎯 BLOCO 0: COMPARATIVO PRODUÇÃO vs EXPEDIÇÃO
# ==============================================================================
hoje_dt = date.today()
fim_ano = date(hoje_dt.year, 12, 31)
dias_restantes = max(1, (fim_ano - hoje_dt).days)
meta_teto_estoque = 3468.0

carr_base_ano = 1362558.0 
prod_base_ano = 1362676.0 
ritmo_esperado_dia = 5200.0

carr_ano_atual = forcar_par(carr_base_ano + vol_hoje)
prod_ano_atual = forcar_par(prod_base_ano + prod_hoje_calc)

diff_prod_carr = forcar_par(abs(prod_ano_atual - carr_ano_atual))

if carr_ano_atual >= prod_ano_atual:
    txt_variacao = f"+{diff_prod_carr:,.0f} t (Expedição Superando)"
    cor_variacao = "#00D672"
else:
    txt_variacao = f"+{diff_prod_carr:,.0f} t (Produção Superando)"
    cor_variacao = "#FF9F1C"

excesso_estoque = max(0.0, estoque_total - meta_teto_estoque)
ritmo_extra_dia = excesso_estoque / dias_restantes
meta_diaria_carr = forcar_par(ritmo_esperado_dia + ritmo_extra_dia)

proj_prod_fechamento = forcar_par(prod_ano_atual + (dias_restantes * ritmo_esperado_dia))
carr_futuro_nec = (estoque_total + (dias_restantes * ritmo_esperado_dia)) - meta_teto_estoque
proj_carr_fechamento = forcar_par(carr_ano_atual + carr_futuro_nec)

html_meta_anual = f"""
<details class="master-box" style="border-left-color: #007BFF;" open>
    <summary>
        <div class="master-metric-title">📊 COMPARATIVO PRODUÇÃO vs EXPEDIÇÃO ({dias_restantes} DIAS ATÉ 31/12)</div>
        <div class="master-metric-val">{carr_ano_atual:,.0f} <span style="font-size:1.2rem; color:#94a3b8;">t Expedidas</span></div>
        <div class="master-metric-sub" style="color: #007BFF;">Meta Diária Necessária: {meta_diaria_carr:,.0f} t/dia</div>
    </summary>
    <div class="master-content">
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px;">
            <div style="background-color:#111c2e; border:1px solid #1c2b42; border-radius:8px; padding:10px;">
                <div style="font-size:0.75rem; color:#007BFF; font-weight:800;">EXPEDIÇÃO ANUAL</div>
                <div style="font-size:1.3rem; font-weight:900; color:#fff;">{carr_ano_atual:,.0f} t</div>
                <div style="font-size:0.7rem; color:#94a3b8;">Proj. 31/12: <b style="color:#007BFF;">{proj_carr_fechamento:,.0f} t</b></div>
            </div>
            <div style="background-color:#111c2e; border:1px solid #1c2b42; border-radius:8px; padding:10px;">
                <div style="font-size:0.75rem; color:#00D672; font-weight:800;">PRODUÇÃO ANUAL</div>
                <div style="font-size:1.3rem; font-weight:900; color:#fff;">{prod_ano_atual:,.0f} t</div>
                <div style="font-size:0.7rem; color:#94a3b8;">Proj. 31/12: <b style="color:#00D672;">{proj_prod_fechamento:,.0f} t</b></div>
            </div>
        </div>
        <div style="background-color:#111c2e; border:1px solid #1c2b42; border-radius:8px; padding:12px; font-size:0.82rem; color:#cbd5e1; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
            <span>Variação Produção vs Expedição: <b style="color:{cor_variacao}; font-size:0.9rem;">{txt_variacao}</b></span>
            <span>Estoque de Virada 25/26: <b style="color:#38bdf8; font-size:0.9rem;">3.468 t</b></span>
        </div>
    </div>
</details>
"""
st.markdown(html_meta_anual.replace('\n', ''), unsafe_allow_html=True)

# ==============================================================================
# 📦 BLOCO 1: PÁTIO DE VEÍCULOS
# ==============================================================================
html_patio = '<details class="master-box" style="border-left-color: #38bdf8;">'
html_patio += f'<summary><div class="master-metric-title">🚛 Pátio da Fábrica (Tempo Real)</div><div class="master-metric-val">{total_veiculos_fisicos} <span style="font-size:1.1rem; color:#94a3b8;">Veículos Físicos</span></div><div class="master-metric-sub" style="color: #38bdf8;">Carga Disponível: {vol_patio_disponivel:,.0f} t</div></summary>'
html_patio += '<div class="master-content patio-grid">'

blocos_patio = [("🚙 Prog/Chegando", "PR", "#94A3B8"), ("📋 Checklist", "00", "#E5B800"), ("🚛 Apoio", "01", "#E67E22"), ("✅ Fila", "FC", "#00D672"), ("📄 Termo SAP", "TR", "#3498DB")]
for tit, chv, cor in blocos_patio:
    v_qtd = dados_patio.get(chv, {}).get("veiculos", 0)
    v_ton = forcar_par(dados_patio.get(chv, {}).get("peso", 0))
    html_patio += f"<div class='card-patio-sub' style='border-left-color: {cor};'><div class='card-patio-title' style='color: {cor};'>{tit}</div><div class='card-patio-qtd'>{int(v_qtd)} <span style='font-size:0.75rem; color:#94a3b8;'>veíc</span></div><div class='card-patio-ton'>{v_ton:,.0f} t</div></div>"

html_patio += "</div></details>"
st.markdown(html_patio, unsafe_allow_html=True)

# ==============================================================================
# 🏭 BLOCO 2: PRODUÇÃO DO DIA (MS1 / MS2)
# ==============================================================================
html_prod_content = ""

for maq in ["MS1", "MS2"]:
    q_dados = dados_maquinas.get(maq, {})
    if q_dados:
        mat_maq = q_dados.get("material", "--")
        p_maq = q_dados.get("producao", 0)
        q_suj = q_dados.get('sujidade', 0.0)
        q_visc = q_dados.get('viscosidade', 0.0)
        q_alvura = q_dados.get('alvura', 0.0)
        q_ph = q_dados.get('ph', 0.0)
        l1 = q_dados.get('l1', 0)
        l2 = q_dados.get('l2', 0)
        desclass = q_dados.get("desclassificando", False)
        
        c_alv = classificar_kpi_mobile(q_alvura, "alvura")
        c_suj = classificar_kpi_mobile(q_suj, "sujidade")
        c_vis = classificar_kpi_mobile(q_visc, "viscosidade")
        c_ph  = classificar_kpi_mobile(q_ph, "ph")
        
        cor_card_borda = "#E74C3C" if desclass else "#1c2b42"
        
        lbl_l1 = "Linha A" if maq == "MS1" else "Linha C"
        lbl_l2 = "Linha B" if maq == "MS1" else "Linha D"

        html_prod_content += f"""
        <div style='background-color: #111c2e; border: 1.5px solid {cor_card_borda}; border-radius: 8px; padding: 16px; margin-bottom: 12px;'>
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;'>
                <span style='color:#ffffff; font-weight:900; font-size:1.25rem;'>⚙️ {maq}</span>
                <span style='color:#FF9F1C; font-weight:900; font-size:1.35rem;'>📦 MAT: {mat_maq}</span>
                <span style='color:#38bdf8; font-weight:900; font-size:1.4rem;'>{p_maq:,.0f} t</span>
            </div>
            
            <div style='display:flex; justify-content:flex-end; gap: 16px; margin-bottom: 12px; font-size: 0.85rem; color: #94a3b8; font-weight: 800;'>
                <span>{lbl_l1}: <span style='color:#ffffff;'>{l1:,.0f} t</span></span>
                <span>{lbl_l2}: <span style='color:#ffffff;'>{l2:,.0f} t</span></span>
            </div>
            
            <div style='display: flex; justify-content: space-between; text-align: center; border-top: 1px dashed #1c2b42; padding-top: 14px;'>
                <div>
                    <div style='font-size:0.75rem; color:#94a3b8; font-weight:800; text-transform:uppercase;'>ALVURA</div>
                    <div style='font-size:1.35rem; font-weight:900; color:{c_alv}; margin: 4px 0;'>{q_alvura:.2f}%</div>
                    <div style='font-size:0.7rem; color:#64748b; font-weight:700;'>(Mín: 88,5)</div>
                </div>
                <div>
                    <div style='font-size:0.75rem; color:#94a3b8; font-weight:800; text-transform:uppercase;'>SUJIDADE</div>
                    <div style='font-size:1.35rem; font-weight:900; color:{c_suj}; margin: 4px 0;'>{q_suj:.2f}</div>
                    <div style='font-size:0.7rem; color:#64748b; font-weight:700;'>(Máx: 2,5)</div>
                </div>
                <div>
                    <div style='font-size:0.75rem; color:#94a3b8; font-weight:800; text-transform:uppercase;'>VISCOSID.</div>
                    <div style='font-size:1.35rem; font-weight:900; color:{c_vis}; margin: 4px 0;'>{q_visc:,.0f}</div>
                    <div style='font-size:0.7rem; color:#64748b; font-weight:700;'>(Mín: 650)</div>
                </div>
                <div>
                    <div style='font-size:0.75rem; color:#94a3b8; font-weight:800; text-transform:uppercase;'>pH</div>
                    <div style='font-size:1.35rem; font-weight:900; color:{c_ph}; margin: 4px 0;'>{q_ph:.1f}</div>
                    <div style='font-size:0.7rem; color:#64748b; font-weight:700;'>(5,5 - 8,5)</div>
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
        <div class="master-metric-sub" style="color: #E5B800;">MS1: {dados_maquinas['MS1'].get('producao', 0):,.0f} t | MS2: {dados_maquinas['MS2'].get('producao', 0):,.0f} t</div>
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
agora_br = datetime.utcnow() - timedelta(hours=3)
hoje_date = agora_br.date()
ontem_date = hoje_date - timedelta(days=1)

dados_exp_hoje = buscar_dados_turnos_historico(hoje_date)
dados_exp_ontem = buscar_dados_turnos_historico(ontem_date)

vol_exp_hoje = vol_hoje if vol_hoje > 0 else (forcar_par(dados_exp_hoje.get("total_dia", 0)) if dados_exp_hoje else 0)
vol_exp_ontem = vol_ontem if vol_ontem > 0 else (forcar_par(dados_exp_ontem.get("total_dia", 0)) if dados_exp_ontem else 0)

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
        v_par = forcar_par(t['vol'])
        
        html_hoje += f"<div style='flex:1; background-color:#111c2e; border:1.5px solid {cor_b}; border-radius:8px; padding:8px; text-align:center;'><div style='font-size:0.75rem; font-weight:800; color:{cor_txt};'>{t['letra']}</div><div style='font-size:1.1rem; font-weight:900; color:#ffffff;'>{v_par:,.0f} t</div><div style='font-size:0.65rem; color:#94a3b8;'>{sub_txt}</div></div>"
        chart_data_hoje.append({"label": t['letra'], "value": v_par, "text": f"{v_par:,.0f} t", "color": "#FF9F1C" if is_atv else "#00D672"})
    html_hoje += "</div>"
    html_hoje += build_vertical_chart(chart_data_hoje)
else:
    html_hoje += "<div style='color:gray; text-align:left;'>Aguardando dados de hoje...</div>"

html_ontem = f"<div style='font-size:0.75rem; font-weight:800; color:#38bdf8; text-transform:uppercase; margin-bottom:10px; text-align:left;'>Fechamento de Ontem ({ontem_date.strftime('%d/%m')}):</div>"
if dados_exp_ontem and "turnos" in dados_exp_ontem:
    html_ontem += "<div style='display:flex; gap:6px; margin-bottom:8px;'>"
    chart_data_ontem = []
    for t in dados_exp_ontem["turnos"]:
        v_par_ontem = forcar_par(t['vol'])
        html_ontem += f"<div style='flex:1; background-color:#111c2e; border:1.5px solid #1c2b42; border-radius:8px; padding:8px; text-align:center;'><div style='font-size:0.75rem; font-weight:800; color:#38bdf8;'>{t['letra']}</div><div style='font-size:1.1rem; font-weight:900; color:#ffffff;'>{v_par_ontem:,.0f} t</div><div style='font-size:0.65rem; color:#94a3b8;'>{t['horario']}</div></div>"
        chart_data_ontem.append({"label": t['letra'], "value": v_par_ontem, "text": f"{v_par_ontem:,.0f} t", "color": "#38bdf8"})
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
"""
st.markdown(html_exp_completo.replace('\n', ''), unsafe_allow_html=True)

# ==============================================================================
# 📦 BLOCO 4: ESTOQUE TOTAL E MATERIAIS
# ==============================================================================
html_est = '<details class="master-box" style="border-left-color: #9b59b6;">'
html_est += f'<summary><div class="master-metric-title">📦 Estoque Físico no Armazém</div><div class="master-metric-val">{estoque_total:,.0f} <span style="font-size:1.1rem; color:#94a3b8;">TON</span></div><div class="master-metric-sub" style="color: #9b59b6;">Status do Armazém: {status_transbordo}</div></summary>'
html_est += '<div class="master-content">'

if dados_segregados:
    df_seg = pd.DataFrame(list(dados_segregados.items()), columns=["Material", "Toneladas"]).sort_values(by="Toneladas", ascending=False)
    chart_data_est = []
    for _, row in df_seg.iterrows():
        t_par = forcar_par(row["Toneladas"])
        mat_nome = str(row["Material"]).upper()
        
        if "SQ" in mat_nome:
            cor_barra = "#FF7700" 
        elif "EQ" in mat_nome:
            cor_barra = "#00D672" 
        else:
            cor_barra = "#38bdf8" 
            
        chart_data_est.append({
            "label": row["Material"],
            "value": t_par,
            "text": f"{t_par:,.0f} t",
            "color": cor_barra
        })
    html_est += build_vertical_chart(chart_data_est)
else:
    html_est += '<div style="color:gray;">Aguardando detalhamento de material...</div>'

html_est += "</div></details>"
st.markdown(html_est, unsafe_allow_html=True)


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
            total_glp_recente = forcar_par(df_mes_recente["KG_NUM"].sum())

            html_glp += f'<summary><div class="master-metric-title">⛽ Consumo de GLP da Frota</div><div class="master-metric-val">{total_glp_recente:,.0f} <span style="font-size:1.1rem; color:#94a3b8;">KG</span></div><div class="master-metric-sub" style="color: #fd7e14;">Acumulado do Mês Atual ({mes_recente})</div></summary>'
            html_glp += '<div class="master-content">'
            
            df_maq = df_mes_recente.groupby("MAQUINA")["KG_NUM"].sum().reset_index().sort_values(by="KG_NUM", ascending=False)
            
            if not df_maq.empty:
                chart_data_glp = []
                for _, row in df_maq.iterrows():
                    val_kg_par = forcar_par(row["KG_NUM"])
                    chart_data_glp.append({
                        "label": row["MAQUINA"],
                        "value": val_kg_par,
                        "text": f"{val_kg_par:,.0f} kg",
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

st.markdown("<br><center><span style='color:#94a3b8; font-size: 0.80rem; font-weight: 600; letter-spacing: 0.5px;'>A.L.O.V.E - Mobile / Developed by Cristiano Ciriaco</span></center>", unsafe_allow_html=True)
