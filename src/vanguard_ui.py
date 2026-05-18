import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import time

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VANGUARD MILANO | Command Tower",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


url_demo = st.query_params.get("demo", "") == "true"

# ─────────────────────────────────────────────────────────────────────────────
#  HYBRID LOCALIZATION ENGINE
#  Strategy: Demo+Italiano → hardcoded IT dict (reliable, no internet needed)
#            Live+Italiano  → GoogleTranslator real-time (shows live capability)
#            English        → EN dict (default)
# ─────────────────────────────────────────────────────────────────────────────
try:
    from deep_translator import GoogleTranslator as _GT
    _translator_available = True
except ImportError:
    _translator_available = False

_EN: dict = {
    "tagline":        "Autonomous Logistics &amp; X402 Settlement Engine",
    "system_armed":   "SYSTEM ARMED",
    "env_prod":       "ENV: PRODUCTION",
    "region":         "REGION: EU-SOUTH",
    "operational":    "◆ OPERATIONAL",
    "op_mode":        "⚙️ Operation Mode",
    "demo_toggle":    "   Demo Mode (Simulated Strike)",
    "manifest_lbl":   "📄 Cargo Manifest (Optional)",
    "agent_cmd":      "🚀 Agent Command",
    "execute_btn":    "Execute Strike Scan",
    "threat_lbl":     "📡 Threat Assessment",
    "log_lbl":        "🤖 Agent Decision Log",
    "map_lbl":        " Dynamic Logistics Network",
    "plan_lbl":       "📋 Rerouting Plan",
    "pay_lbl":        "💸 X402 Autonomous Settlement",
    "standing_by":    "STANDING BY — AWAITING SCAN COMMAND",
    "standing_sub":   "Select operation mode and press Execute Strike Scan",
    "footer":         "Protecting Northern Italian supply chains — Milan · Genoa · Turin",
    "metric_strike":  "Strike Level",
    "metric_routes":  "Affected Routes",
    "metric_network": "Network Status",
    "status_rerouted":"REROUTED",
    "status_disrupted":"Disrupted",
    "status_stable":  "STABLE",
    "status_clear":   "Clear",
    "trace_title":    "◆ Autonomous Execution Trace",
    "receipt_title":  "◆ Settlement Receipt",
    "receipt_amt":    "Amount",
    "receipt_rec":    "Recipient",
    "receipt_rsn":    "Reason",
    "receipt_stat":   "Status",
    "receipt_blk":    "Block Ref",
    "sys_time":       "System Time",
    "sys_region":     "Region",
    "sys_status":     "Status: OPERATIONAL",
    
    # --- Status Box Translations ---
    "scan_complete":  "✅ Scan Complete — Manifest Generated",
    "status_init":    "Initialising VANGUARD Agent...",
    "sys_mode_sim":   "[sys] Mode:  Simulation",
    "sys_mode_live":  "[sys] Mode: 🌍 Live Feed",
    "sys_engage":     "[sys] Engaging Gemini 2.5 Flash — tool loop active...",
    "sys_payload":    "[sys] Multimodal payload:",
    "sys_ok":         "[ok] Manifest compiled and validated.",
    "err_backend":    "❌ Backend Error",
    "err_conn":       "❌ Cannot reach backend. Is FastAPI running on port 8000?",
    "err_gen":        "❌ Error:",
}

_IT: dict = {
    "tagline":        "Motore Autonomo di Logistica &amp; Pagamento X402",
    "system_armed":   "SISTEMA ARMATO",
    "env_prod":       "AMB: PRODUZIONE",
    "region":         "REGIONE: EU-SUD",
    "operational":    "◆ OPERATIVO",
    "op_mode":        "⚙️ Modalità Operativa",
    "demo_toggle":    "  Modalità Demo (Sciopero Simulato)",
    "manifest_lbl":   "📄 Manifesto Cargo (Facoltativo)",
    "agent_cmd":      "🚀 Comando Agente",
    "execute_btn":    "Esegui Scansione Sciopero",
    "threat_lbl":     "📡 Valutazione Minaccia",
    "log_lbl":        "🤖 Log Decisionale Agente",
    "map_lbl":        " Rete Logistica Dinamica",
    "plan_lbl":       "📋 Piano di Rerouting",
    "pay_lbl":        "💸 Accordo Autonomo X402",
    "standing_by":    "IN ATTESA — COMANDO SCANSIONE RICHIESTO",
    "standing_sub":   "Seleziona la modalità e premi Esegui Scansione",
    "footer":         "Proteggere le supply chain del Nord Italia — Milano · Genova · Torino",
    "metric_strike":  "Livello Sciopero",
    "metric_routes":  "Rotte Coinvolte",
    "metric_network": "Stato Rete",
    "status_rerouted":"RIDIRETTO",
    "status_disrupted":"Interrotto",
    "status_stable":  "STABILE",
    "status_clear":   "Regolare",
    "trace_title":    "◆ Tracciamento Esecuzione Autonoma",
    "receipt_title":  "◆ Ricevuta di Regolamento",
    "receipt_amt":    "Importo",
    "receipt_rec":    "Destinatario",
    "receipt_rsn":    "Motivo",
    "receipt_stat":   "Stato",
    "receipt_blk":    "Rif. Blocco",
    "sys_time":       "Ora di Sistema",
    "sys_region":     "Regione",
    "sys_status":     "Stato: OPERATIVO",
    
    # --- Status Box Translations ---
    "scan_complete":  "✅ Scansione Completata — Manifesto Generato",
    "status_init":    "Inizializzazione Agente VANGUARD...",
    "sys_mode_sim":   "[sys] Modalità:  Simulazione",
    "sys_mode_live":  "[sys] Modalità: 🌍 Feed Live",
    "sys_engage":     "[sys] Attivazione Gemini 2.5 Flash — ciclo strumenti attivo...",
    "sys_payload":    "[sys] Payload multimodale:",
    "sys_ok":         "[ok] Manifesto compilato e validato.",
    "err_backend":    "❌ Errore Backend",
    "err_conn":       "❌ Impossibile raggiungere il backend. FastAPI è sulla porta 8000?",
    "err_gen":        "❌ Errore:",
}

@st.cache_data(show_spinner=False)
def _live_translate() -> dict:
    """Translates EN dict via GoogleTranslator; falls back to hardcoded IT on error."""
    if not _translator_available:
        return _IT
    try:
        tr = _GT(source="en", target="it")
        return {k: tr.translate(v) for k, v in _EN.items()}
    except Exception:
        return _IT

# Read persisted widget states from the PREVIOUS Streamlit run
_lang = st.session_state.get("lang_sel", "English")
_demo_persisted = st.session_state.get("demo_mode_key", url_demo)

if _lang == "Italiano":
    # Demo + Italian = use reliable hardcoded dict
    # Live + Italian = use real-time GoogleTranslator (demonstrates live capability)
    T: dict = _IT if _demo_persisted else _live_translate()
else:
    T = _EN


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Base ── */
html, body { font-family: 'Inter', sans-serif !important; }

[data-testid="stAppViewContainer"] {
    background-image:
        linear-gradient(rgba(37,99,235,0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(37,99,235,0.035) 1px, transparent 1px),
        radial-gradient(ellipse 70% 50% at 5%   0%,   rgba(37,99,235,0.18) 0%, transparent 55%),
        radial-gradient(ellipse 55% 40% at 95% 100%,  rgba(16,185,129,0.08) 0%, transparent 55%),
        linear-gradient(165deg, #05101e 0%, #070d1b 25%, #050a17 55%, #060c1a 80%, #040e1d 100%);
    background-size:   52px 52px, 52px 52px, 100% 100%, 100% 100%, 100% 100%;
    background-repeat: repeat, repeat, no-repeat, no-repeat, no-repeat;
    background-attachment: scroll;
}

/* Grid merged into main background above — no separate overlay needed */

[data-testid="stHeader"]  { background: transparent !important; }
[data-testid="stSidebar"] { background: rgba(4,9,20,0.97) !important; }
#MainMenu, footer, .viewerBadge_container__1QSob { visibility: hidden; }

/* ── Hero ── */
.vg-hero {
    text-align: center;
    padding: 2.2rem 1rem 1.4rem;
    border-bottom: 1px solid rgba(37,99,235,0.22);
    margin-bottom: 1.8rem;
}
.vg-wordmark {
    font-size: clamp(2rem, 5vw, 3.6rem);
    font-weight: 900;
    letter-spacing: 0.14em;
    color: #ffffff;
    text-transform: uppercase;
    margin: 0;
    line-height: 1;
    text-shadow: 0 0 40px rgba(37,99,235,0.45);
}
.vg-wordmark span { color: #3B82F6; }
.vg-tagline {
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.38em;
    color: #475569;
    text-transform: uppercase;
    margin-top: 0.55rem;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Status bar ── */
.vg-status-bar {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 2.2rem;
    margin-top: 0.9rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    color: #64748B;
    letter-spacing: 0.06em;
}
.live-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: #10B981;
    border-radius: 50%;
    margin-right: 6px;
    animation: blink 2s infinite;
    vertical-align: middle;
    will-change: opacity;   /* hardware-accelerate → no layout repaints */
}
@keyframes blink {
    0%,100% { opacity:1; box-shadow:0 0 5px #10B981; }
    50%      { opacity:0.3; box-shadow:none; }
}

/* ── Section header labels ── */
.vg-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    color: #4B6480;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
    padding-bottom: 0.35rem;
    border-bottom: 1px solid rgba(37,99,235,0.18);
}

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background:     rgba(10,18,35,0.88) !important;
    border:         1px solid rgba(37,99,235,0.22) !important;
    border-radius:  10px !important;
    padding:        1.1rem !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
    box-shadow:     0 4px 24px rgba(0,0,0,0.7) !important;
}
[data-testid="metric-container"] label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size:   0.62rem !important;
    letter-spacing: 0.18em !important;
    color:       #475569 !important;
    text-transform: uppercase !important;
    font-weight: 600 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size:   1.65rem !important;
    font-weight: 800 !important;
    color:       #F1F5F9 !important;
}

/* ── Command button ── */
.stButton > button {
    background:    linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%) !important;
    color:         #ffffff !important;
    border:        none !important;
    border-radius: 8px !important;
    font-family:   'JetBrains Mono', monospace !important;
    font-size:     0.76rem !important;
    font-weight:   700 !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    padding:       0.85rem 1.6rem !important;
    transition:    all 0.25s ease !important;
    box-shadow:    0 0 22px rgba(37,99,235,0.35) !important;
    width:         100% !important;
}
.stButton > button:hover {
    box-shadow: 0 0 40px rgba(37,99,235,0.75) !important;
    transform:  translateY(-2px) !important;
}

/* ── Agent decision log ── */
.agent-log-wrap {
    background:    rgba(3,7,18,0.95);
    border:        1px solid rgba(37,99,235,0.22);
    border-radius: 10px;
    overflow:      hidden;
    margin-top:    0.4rem;
}
.agent-log-title {
    font-family:    'JetBrains Mono', monospace;
    font-size:      0.62rem;
    letter-spacing: 0.18em;
    color:          #1D4ED8;
    text-transform: uppercase;
    padding:        0.55rem 1rem;
    border-bottom:  1px solid rgba(37,99,235,0.15);
    background:     rgba(37,99,235,0.06);
}
.agent-log-body {
    padding:    0.5rem 0.8rem;
    max-height: 260px;
    overflow-y: auto;
    font-family:'JetBrains Mono', monospace;
}
.log-row {
    display:       flex;
    align-items:   flex-start;
    gap:           8px;
    padding:       5px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    font-size:     0.76rem;
    line-height:   1.45;
}
.log-row:last-child { border-bottom: none; }
.log-ts    { color:#2D3748; white-space:nowrap; padding-top:1px; font-size:0.68rem; }
.log-ok    { color:#94A3B8; }
.log-run   { color:#60A5FA; }
.log-warn  { color:#FBBF24; }
.log-err   { color:#F87171; }
.log-bold  { font-weight:600; }

/* ── X402 receipt ── */
.receipt-wrap {
    background:    rgba(3,7,18,0.95);
    border:        1px solid rgba(16,185,129,0.28);
    border-radius: 10px;
    overflow:      hidden;
    margin-top:    0.8rem;
}
.receipt-header {
    font-family:    'JetBrains Mono', monospace;
    font-size:      0.62rem;
    letter-spacing: 0.2em;
    color:          #10B981;
    text-transform: uppercase;
    padding:        0.55rem 1rem;
    border-bottom:  1px solid rgba(16,185,129,0.15);
    background:     rgba(16,185,129,0.06);
}
.receipt-body {
    font-family: 'JetBrains Mono', monospace;
    font-size:   0.8rem;
    padding:     0.9rem 1rem;
    color:       #94A3B8;
    line-height: 2;
}
.receipt-val   { color:#E2E8F0; }
.receipt-green { color:#34D399; font-weight:600; }

/* ── Info / warning blocks ── */
[data-testid="stInfo"],
[data-testid="stWarning"],
[data-testid="stSuccess"] {
    border-radius: 8px !important;
    font-size:     0.88rem !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background:    rgba(10,18,35,0.7) !important;
    border:        1px dashed rgba(37,99,235,0.3) !important;
    border-radius: 8px !important;
}

/* ── General text ── */
p, li, .stMarkdown p { color:#CBD5E1 !important; font-size:0.92rem !important; }
h1,h2,h3             { color:#F1F5F9 !important; }
label                { color:#94A3B8 !important; }

/* ── Toggle ── */
[data-testid="stToggle"] label { font-size:0.9rem !important; color:#CBD5E1 !important; }

/* ── Caption ── */
[data-testid="stCaptionContainer"] p { color:#4B6480 !important; font-size:0.84rem !important; font-family:'JetBrains Mono',monospace !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  HERO SECTION
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="vg-hero">
    <h1 class="vg-wordmark">VANGUARD <span>MILANO</span></h1>
    <p class="vg-tagline">{T['tagline']}</p>
    <div class="vg-status-bar">
        <span><span class="live-dot"></span>{T['system_armed']}</span>
        <span>{T['env_prod']}</span>
        <span>{T['region']}</span>
        <span>{T['operational']}</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.caption(
    f"◆  {T['sys_time']}: {datetime.utcnow().strftime('%Y-%m-%d  %H:%M:%S')} UTC   |   "
    f"{T['sys_region']}: EU-SOUTH   |   {T['sys_status']}"
)
st.markdown("---")


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
col_cmd, col_results = st.columns([1, 2.3], gap="large")


# ════════════════════════════════════════════════════════════════════════════
#  LEFT: COMMAND PANEL
# ════════════════════════════════════════════════════════════════════════════
with col_cmd:

    # ── Language Toggle ──────────────────────────────────────────────────
    st.markdown('<p class="vg-label">🌐 Language</p>', unsafe_allow_html=True)
    st.radio(
        "Language", ["English", "Italiano"],
        horizontal=True,
        label_visibility="collapsed",
        key="lang_sel",          # persisted in session_state → T recomputes on rerun
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Operation Mode ───────────────────────────────────────────────────
    st.markdown(f'<p class="vg-label">{T["op_mode"]}</p>', unsafe_allow_html=True)
    demo_mode = st.toggle(
        T["demo_toggle"],
        value=url_demo,
        key="demo_mode_key",     # persisted in session_state → used by T logic at top
        help=(
            "Enable when presenting to judges or when no live strikes are active in Italy. "
            "Injects a realistic 48-hr national rail & road-freight strike scenario. "
            "All real-time RSS feeds are bypassed."
        )
    )
    if demo_mode:
        if _lang == "Italiano":
            st.warning(
                "**SIMULAZIONE ATTIVA** — Scenario di sciopero iniettato. "
                "Feed di notizie reali ignorati. Ideale per demo dal vivo.",
                icon="🎬"
            )
        else:
            st.warning(
                "**SIMULATION ACTIVE** — Strike scenario is injected. "
                "Real news feeds bypassed. Ideal for live demos.",
                icon="🎬"
            )
    else:
        st.info(
            "**LIVE MODE** — Agent will scan ANSA + BBC Europe RSS feeds "
            "for real Italian transport disruptions.",
            icon="🌍"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Multimodal Upload ────────────────────────────────────────────────
    st.markdown(f'<p class="vg-label">{T["manifest_lbl"]}</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        label="Upload shipping manifest for AI Vision analysis",
        type=["pdf", "png", "jpg", "jpeg"],
        label_visibility="collapsed",
        help="Gemini Vision will analyse cargo contents and elevate threat level if high-value or perishable goods are detected."
    )
    if uploaded_file:
        st.success(f"📎 Manifest loaded: **{uploaded_file.name}**", icon="✅")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Execute Button ───────────────────────────────────────────────────
    st.markdown(f'<p class="vg-label">{T["agent_cmd"]}</p>', unsafe_allow_html=True)

    if st.button(T["execute_btn"], use_container_width=True, type="primary"):

        with st.status(T["status_init"], expanded=True) as status:
            try:
                _mode_text = T["sys_mode_sim"] if demo_mode else T["sys_mode_live"]
                st.write(_mode_text)
                st.write(T["sys_engage"])
                time.sleep(0.8)

                if uploaded_file:
                    st.write(f"{T['sys_payload']} {uploaded_file.name} ({uploaded_file.type})")

                # ── Build multipart request ──────────────────────────
                files = {}
                if uploaded_file is not None:
                    files = {
                        "document": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type,
                        )
                    }

                data     = {"demo_mode": str(demo_mode).lower()}
                response = requests.post(
                    f"{BACKEND_URL}/status",
                    data=data,
                    files=files if files else None,
                    timeout=120,
                )

                if response.status_code == 200:
                    st.write(T["sys_ok"])
                    st.session_state["data"] = response.json()

                    _resp_pay = st.session_state["data"].get("manifest", {}).get("payment_settlement")
                    if _resp_pay and isinstance(_resp_pay, dict):
                        st.toast(
                            f"✅ X402 settled: {_resp_pay.get('amount',0):,.2f} "
                            f"{_resp_pay.get('currency','USDC')} → {_resp_pay.get('recipient','')}",
                            icon="💸",
                        )
                    status.update(
                        label=T["scan_complete"],
                        state="complete",
                        expanded=False,
                    )
                else:
                    status.update(
                        label=f"{T['err_backend']} {response.status_code}: {response.text[:120]}",
                        state="error",
                    )

            except requests.exceptions.ConnectionError:
                status.update(
                    label=T["err_conn"],
                    state="error",
                )
            except Exception as exc:
                status.update(label=f"{T['err_gen']} {exc}", state="error")

    elif "data" in st.session_state:
        with st.status(T["scan_complete"], state="complete", expanded=False):
            _mode_text = T["sys_mode_sim"] if demo_mode else T["sys_mode_live"]
            st.write(_mode_text)
            st.write(T["sys_engage"])
            st.write(T["sys_ok"])

    # ── Mission Footer ───────────────────────────────────────────────────
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.caption(T["footer"])


# ════════════════════════════════════════════════════════════════════════════
#  RIGHT: RESULTS PANEL
# ════════════════════════════════════════════════════════════════════════════
with col_results:

    if "data" not in st.session_state:
        st.markdown(
            f"""
            <div style="text-align:center; padding:5rem 2rem; color:#1E293B;">
                <div style="font-size:4rem; margin-bottom:1.2rem; color: #3B82F6; filter: drop-shadow(0 0 20px rgba(37,99,235,0.8));">⬡</div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.95rem; letter-spacing:0.25em; color:#2D4A6B; font-weight:600;">
                    {T['standing_by']}
                </div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; letter-spacing:0.12em; color:#1E3A5F; margin-top:0.6rem;">
                    {T['standing_sub']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        resp_data   = st.session_state["data"]
        manifest    = resp_data.get("manifest", {})
        agent_steps = resp_data.get("agent_steps", [])

        # ── Threat Metrics ────────────────────────────────────────────
        st.markdown(f'<p class="vg-label">{T["threat_lbl"]}</p>', unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)

        strike_level = manifest.get("strike_level", "Unknown")
        m1.metric(T["metric_strike"], strike_level)
        m2.metric(T["metric_routes"], len(manifest.get("affected_routes", [])))

        if manifest.get("strike_detected"):
            m3.metric(T["metric_network"], T["status_rerouted"], delta=T["status_disrupted"], delta_color="inverse")
        else:
            m3.metric(T["metric_network"], T["status_stable"], delta=T["status_clear"], delta_color="normal")

        # ── Agent Decision Log ────────────────────────────────────────
        if agent_steps:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f'<p class="vg-label">{T["log_lbl"]}</p>', unsafe_allow_html=True)

            color_map = {
                "ok":      "log-ok",
                "running": "log-run",
                "warning": "log-warn",
                "error":   "log-err",
            }
            rows_html = ""
            for s in agent_steps:
                css_class = color_map.get(s.get("status", "ok"), "log-ok")
                rows_html += (
                    f'<div class="log-row">'
                    f'  <span class="log-ts">[{s.get("ts","?")}]</span>'
                    f'  <span class="{css_class}">'
                    f'    <span class="log-bold">{s.get("step","")}</span>'
                    f'    &nbsp;—&nbsp;{s.get("detail","")}'
                    f'  </span>'
                    f'</div>'
                )

            st.markdown(
                f'<div class="agent-log-wrap">'
                f'  <div class="agent-log-title">{T["trace_title"]}</div>'
                f'  <div class="agent-log-body">{rows_html}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # ── Dynamic Logistics Map ─────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f'<p class="vg-label">{T["map_lbl"]}</p>', unsafe_allow_html=True)

        # Map Style Toggle
        _map_choice = st.radio(
            "Map View", [" Dark Mode", " Street View"],
            horizontal=True, label_visibility="collapsed",
        )
        if _map_choice == " Dark Mode":
            _mapbox_style = "carto-darkmatter"
            _legend_color = "#94A3B8"
            _legend_bg    = "rgba(3,7,18,0.85)"
            _hover_bg     = "#0d1b2a"
        else:
            _mapbox_style = "open-street-map"
            _legend_color = "#1E293B"
            _legend_bg    = "rgba(255,255,255,0.9)"
            _hover_bg     = "#ffffff"

        city_coords = {
            "Milan":    (45.4642,  9.1900),
            "Turin":    (45.0703,  7.6868),
            "Genoa":    (44.4056,  8.9463),
            "Verona":   (45.4384, 10.9916),
            "Piacenza": (45.0526,  9.6930),
            "Bologna":  (44.4949, 11.3426),
            "Brescia":  (45.5416, 10.2118),
            "Rome":     (41.9028, 12.4964),
        }

        is_strike   = manifest.get("strike_detected", False)
        dynamic_hubs = [{
            "City":   "Milan",
            "lat":    45.4642,
            "lon":    9.1900,
            "Status": "Disrupted" if is_strike else "Stable",
            "Info":   "HQ / Origin Hub",
        }]

        for hub in manifest.get("alternative_hubs", []):
            city_name = hub.get("name", "")
            cap_raw   = hub.get("capacity_status", "").lower()

            if city_name in city_coords and city_name != "Milan":
                lat, lon = city_coords[city_name]
                if "available" in cap_raw or "operational" in cap_raw or "active" in cap_raw:
                    ui_status = "Active Backup"
                elif "blocked" in cap_raw or "strike" in cap_raw:
                    ui_status = "Disrupted"
                elif "limited" in cap_raw:
                    ui_status = "Warning"
                else:
                    ui_status = "Stable"

                dynamic_hubs.append({
                    "City":   city_name,
                    "lat":    lat,
                    "lon":    lon,
                    "Status": ui_status,
                    "Info":   hub.get("capacity_status", ""),
                })

        # Fallback nodes if AI didn't populate hubs
        existing_cities = {h["City"] for h in dynamic_hubs}
        if len(dynamic_hubs) == 1:
            for city, (lat, lon) in [("Turin", city_coords["Turin"]), ("Genoa", city_coords["Genoa"])]:
                if city not in existing_cities:
                    dynamic_hubs.append({"City": city, "lat": lat, "lon": lon, "Status": "Stable", "Info": ""})

        hubs_df = pd.DataFrame(dynamic_hubs)
        color_discrete = {
            "Disrupted":   "#EF4444",
            "Active Backup": "#10B981",
            "Warning":     "#F59E0B",
            "Stable":      "#3B82F6",
        }

        fig = px.scatter_mapbox(
            hubs_df,
            lat="lat", lon="lon",
            hover_name="City",
            hover_data={"Info": True, "lat": False, "lon": False},
            color="Status",
            color_discrete_map=color_discrete,
            zoom=6,
            height=380,
        )
        fig.update_traces(marker=dict(size=14))
        fig.update_layout(
            mapbox_style=_mapbox_style,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(
                font=dict(size=13, color=_legend_color, family="JetBrains Mono"),
                bgcolor=_legend_bg,
                bordercolor="rgba(37,99,235,0.2)",
                borderwidth=1,
                x=0.01, y=0.99,
            ),
            hoverlabel=dict(
                font_size=13,
                font_family="JetBrains Mono",
                bgcolor=_hover_bg,
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── Rerouting Plan ────────────────────────────────────────────
        rerouting_plan = manifest.get("rerouting_plan", "")
        if rerouting_plan and rerouting_plan not in ("", "All routes clear."):
            st.markdown(f'<p class="vg-label">{T["plan_lbl"]}</p>', unsafe_allow_html=True)
            st.info(rerouting_plan, icon="🗺️")

        # ── X402 Settlement Receipt ───────────────────────────────────
        payment = manifest.get("payment_settlement")
        if payment and isinstance(payment, dict):
            st.markdown("<br>", unsafe_allow_html=True)
            badge_html = (
                '<span style="background:#F59E0B;color:#000;font-size:0.68rem;'
                'font-weight:700;padding:3px 8px;border-radius:4px;'
                'font-family:JetBrains Mono,monospace;letter-spacing:0.08em;">SIMULATION</span>'
                if demo_mode else
                '<span style="background:#10B981;color:#000;font-size:0.68rem;'
                'font-weight:700;padding:3px 8px;border-radius:4px;'
                'font-family:JetBrains Mono,monospace;letter-spacing:0.08em;">ON-CHAIN</span>'
            )
            st.markdown(
                f'<p class="vg-label">{T["pay_lbl"]} &nbsp; {badge_html}</p>',
                unsafe_allow_html=True,
            )

            block_ref  = payment.get("block_ref", payment.get("status", "—"))
            st.markdown(
                f"""
                <div class="receipt-wrap">
                    <div class="receipt-header">{T["receipt_title"]} — {payment.get("transaction_id","")}</div>
                    <div class="receipt-body">
                        <div style="display:flex;justify-content:space-between;">
                            <span>{T["receipt_amt"]}</span>
                            <span class="receipt-green">{payment.get("amount",0):,.2f} {payment.get("currency","USDC")}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;">
                            <span>{T["receipt_rec"]}</span>
                            <span class="receipt-val">{payment.get("recipient","")}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;">
                            <span>{T["receipt_rsn"]}</span>
                            <span class="receipt-val">{payment.get("reason","")}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;">
                            <span>{T["receipt_stat"]}</span>
                            <span class="receipt-green">{payment.get("status","")}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;">
                            <span>{T["receipt_blk"]}</span>
                            <span class="receipt-val" style="font-size:0.7rem;">{block_ref}</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )