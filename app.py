import streamlit as st
import time
from agents import run_research, get_memory_stats
from langchain_core.messages import AIMessage

st.set_page_config(
    page_title="FIT Orchestrator",
    page_icon="◈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── GLOBAL CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

:root {
  --bg:         #0a0a0f;
  --surface:    #111118;
  --surface2:   #18181f;
  --border:     rgba(255,255,255,0.07);
  --border2:    rgba(255,255,255,0.13);
  --accent:     #6c63ff;
  --accent2:    #a78bfa;
  --accent3:    #22d3ee;
  --gold:       #f59e0b;
  --green:      #10b981;
  --red:        #f43f5e;
  --text:       #e8e8f0;
  --muted:      rgba(232,232,240,0.38);
  --muted2:     rgba(232,232,240,0.6);
  --mono:       'DM Mono', monospace;
  --sans:       'DM Sans', sans-serif;
  --display:    'Syne', sans-serif;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
  font-family: var(--sans) !important;
  background: var(--bg) !important;
  color: var(--text) !important;
}

#MainMenu, footer, header { visibility: hidden; }

.block-container {
  padding: 3rem 1.5rem 8rem !important;
  max-width: 780px !important;
}

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

.fit-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 2.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border);
}
.fit-wordmark {
  font-family: var(--display);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  color: var(--accent2);
  opacity: 0.8;
}
.fit-title {
  font-family: var(--display);
  font-size: 2.6rem;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.03em;
  color: var(--text);
  margin-top: 6px;
}
.fit-title span {
  background: linear-gradient(135deg, var(--accent), var(--accent3));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.fit-sub {
  font-family: var(--sans);
  font-size: 13px;
  font-weight: 300;
  color: var(--muted);
  margin-top: 8px;
  letter-spacing: 0.01em;
}
.fit-badge {
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent3);
  background: rgba(34,211,238,0.07);
  border: 1px solid rgba(34,211,238,0.15);
  border-radius: 4px;
  padding: 4px 9px;
}

[data-testid="stForm"] {
  background: var(--surface);
  border: 1px solid var(--border2);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 2rem;
  position: relative;
  overflow: hidden;
}
[data-testid="stForm"]::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 50% 0%, rgba(108,99,255,0.06) 0%, transparent 65%);
  pointer-events: none;
}
.input-label {
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 10px;
}
.stTextInput > div > div > input {
  font-family: var(--mono) !important;
  font-size: 14px !important;
  font-weight: 400 !important;
  border-radius: 10px !important;
  border: 1px solid var(--border2) !important;
  background: rgba(255,255,255,0.03) !important;
  color: var(--text) !important;
  padding: 12px 16px !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stTextInput > div > div > input:focus {
  border-color: rgba(108,99,255,0.5) !important;
  box-shadow: 0 0 0 3px rgba(108,99,255,0.08) !important;
  outline: none !important;
}
.stTextInput > div > div > input::placeholder {
  color: var(--muted) !important;
}
[data-testid="InputInstructions"] { display: none !important; }

.stButton > button {
  font-family: var(--display) !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  letter-spacing: 0.12em !important;
  text-transform: uppercase !important;
  border-radius: 10px !important;
  border: 1px solid rgba(108,99,255,0.4) !important;
  background: linear-gradient(135deg, rgba(108,99,255,0.15), rgba(167,139,250,0.08)) !important;
  color: var(--accent2) !important;
  padding: 12px 20px !important;
  width: 100% !important;
  transition: all 0.2s !important;
}
.stButton > button:hover {
  background: linear-gradient(135deg, rgba(108,99,255,0.28), rgba(167,139,250,0.18)) !important;
  border-color: rgba(108,99,255,0.7) !important;
  box-shadow: 0 0 20px rgba(108,99,255,0.2) !important;
  transform: translateY(-1px) !important;
}

.sec-label {
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--muted);
  margin: 2rem 0 1rem;
  display: flex;
  align-items: center;
  gap: 10px;
}
.sec-label::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
}

.orch-card {
  background: var(--surface);
  border: 1px solid var(--border2);
  border-radius: 16px;
  padding: 22px 24px;
  margin-bottom: 1rem;
  position: relative;
  overflow: hidden;
}
.orch-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--accent), var(--accent3), transparent);
  border-radius: 16px 16px 0 0;
}
.orch-head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 16px;
}
.orch-avatar {
  width: 44px; height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(108,99,255,0.2), rgba(34,211,238,0.1));
  border: 1px solid rgba(108,99,255,0.25);
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; flex-shrink: 0;
  position: relative;
}
.orch-avatar.pulse::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 16px;
  border: 1px solid rgba(108,99,255,0.3);
  animation: pulse-ring 1.5s cubic-bezier(0.4,0,0.6,1) infinite;
}
@keyframes pulse-ring {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0; transform: scale(1.25); }
}
.orch-name {
  font-family: var(--display);
  font-size: 15px;
  font-weight: 700;
  letter-spacing: -0.01em;
}
.orch-status { font-family: var(--mono); font-size: 11px; color: var(--muted); margin-top: 3px; }
.orch-status.live { color: var(--accent2); }

.thinking-box {
  background: rgba(108,99,255,0.04);
  border: 1px solid rgba(108,99,255,0.12);
  border-radius: 10px;
  padding: 14px 16px;
  font-family: var(--sans);
  font-size: 13px;
  font-weight: 300;
  line-height: 1.75;
  color: var(--muted2);
  min-height: 52px;
  white-space: pre-wrap;
}
.thinking-box.active {
  color: var(--text);
  border-color: rgba(108,99,255,0.22);
}
.thinking-box.typing::after {
  content: '▋';
  display: inline-block;
  font-family: var(--mono);
  font-size: 12px;
  color: var(--accent2);
  animation: blink 0.9s step-end infinite;
  margin-left: 2px;
}
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

.mem-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-family: var(--mono);
  font-size: 10px;
  color: var(--accent3);
  background: rgba(34,211,238,0.07);
  border: 1px solid rgba(34,211,238,0.15);
  border-radius: 20px;
  padding: 3px 10px;
  margin: 4px 3px 0 0;
}

/* Similarity bar */
.sim-bar-wrap {
  display: flex; align-items: center; gap: 8px; margin-top: 2px;
}
.sim-bar-bg {
  flex: 1; height: 4px; background: rgba(34,211,238,0.12);
  border-radius: 2px; overflow: hidden;
}
.sim-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--accent3));
  border-radius: 2px;
}
.sim-pct {
  font-family: var(--mono); font-size: 10px; color: var(--accent3); white-space: nowrap;
}

/* Reflection score badge */
.reflect-badge {
  display: inline-flex; align-items: center; gap: 6px;
  font-family: var(--mono); font-size: 11px;
  border-radius: 20px; padding: 3px 12px; margin-top: 8px;
}
.reflect-badge.good {
  color: var(--green); background: rgba(16,185,129,0.08);
  border: 1px solid rgba(16,185,129,0.2);
}
.reflect-badge.warn {
  color: var(--gold); background: rgba(245,158,11,0.08);
  border: 1px solid rgba(245,158,11,0.2);
}

.agents-grid { display: flex; flex-direction: column; gap: 8px; }

.ag-card {
  display: flex; align-items: flex-start; gap: 14px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 14px 16px;
  position: relative; overflow: hidden;
  transition: border-color 0.25s, background 0.25s, opacity 0.3s, transform 0.2s;
}
.ag-card::before {
  content: '';
  position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: transparent; transition: background 0.25s; border-radius: 3px 0 0 3px;
}
.ag-card.active { border-color: rgba(108,99,255,0.35); background: rgba(108,99,255,0.04); transform: translateX(3px); }
.ag-card.active::before { background: linear-gradient(180deg, var(--accent), var(--accent3)); }
.ag-card.done { opacity: 0.45; }
.ag-card.done::before { background: var(--green); }
.ag-card.waiting { opacity: 0.6; }
.ag-card.skipped { opacity: 0.15; }

.ag-card.active::after {
  content: ''; position: absolute; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(108,99,255,0.4), transparent);
  animation: scan 1.8s linear infinite;
}
@keyframes scan {
  0%   { top: 0; opacity: 0; } 10%  { opacity: 1; } 90%  { opacity: 1; } 100% { top: 100%; opacity: 0; }
}

.ag-icon {
  width: 36px; height: 36px; border-radius: 9px;
  background: rgba(255,255,255,0.04); border: 1px solid var(--border);
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; flex-shrink: 0; transition: border-color 0.25s, background 0.25s;
}
.ag-card.active .ag-icon { background: rgba(108,99,255,0.1); border-color: rgba(108,99,255,0.3); }
.ag-name { font-family: var(--display); font-size: 13px; font-weight: 600; color: var(--text); }
.ag-task { font-family: var(--sans); font-size: 12px; font-weight: 300; color: var(--muted); margin-top: 3px; line-height: 1.55; }
.ag-task.assigned { color: var(--muted2); }
.ag-badge { font-family: var(--mono); font-size: 10px; margin-left: auto; flex-shrink: 0; padding-top: 2px; white-space: nowrap; }
.badge-wait { color: var(--muted); } .badge-live { color: var(--accent2); }
.badge-done { color: var(--green); } .badge-skip { color: var(--muted); }
.dispatch-msg {
  margin-top: 8px; background: rgba(108,99,255,0.05);
  border: 1px solid rgba(108,99,255,0.13); border-radius: 7px;
  padding: 8px 12px; font-family: var(--mono); font-size: 11px;
  color: rgba(108,99,255,0.85); line-height: 1.6;
}

.progress-line { height: 2px; background: var(--border); border-radius: 1px; margin: 1.5rem 0; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent3)); border-radius: 1px; transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1); }

.stTabs [data-baseweb="tab-list"] {
  gap: 0 !important; background: var(--surface) !important;
  border: 1px solid var(--border2) !important; border-radius: 12px 12px 0 0 !important;
  padding: 6px 6px 0 !important; border-bottom: none !important;
}
.stTabs [data-baseweb="tab"] {
  font-family: var(--display) !important; font-size: 12px !important; font-weight: 600 !important;
  letter-spacing: 0.04em !important; padding: 10px 18px !important; color: var(--muted) !important;
  border-radius: 8px 8px 0 0 !important; transition: color 0.2s, background 0.2s !important;
  text-transform: uppercase !important; border: none !important;
}
.stTabs [aria-selected="true"] {
  color: var(--text) !important; background: rgba(108,99,255,0.1) !important;
  border-bottom: 2px solid var(--accent) !important;
}
.stTabs [data-baseweb="tab-panel"] {
  background: var(--surface) !important; border: 1px solid var(--border2) !important;
  border-top: none !important; border-radius: 0 0 12px 12px !important; padding: 20px !important;
}

.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
  font-family: var(--display) !important; font-weight: 700 !important;
  letter-spacing: -0.02em !important; color: var(--text) !important;
}
.stMarkdown p {
  font-family: var(--sans) !important; font-size: 14px !important;
  line-height: 1.8 !important; font-weight: 300 !important; color: var(--muted2) !important;
}

[data-testid="metric-container"] {
  background: var(--surface2) !important; border: 1px solid var(--border) !important;
  border-radius: 10px !important; padding: 14px !important;
}
[data-testid="metric-container"] label {
  font-family: var(--mono) !important; font-size: 10px !important;
  letter-spacing: 0.1em !important; text-transform: uppercase !important; color: var(--muted) !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
  font-family: var(--display) !important; font-size: 26px !important;
  font-weight: 800 !important; color: var(--text) !important;
}

.stDownloadButton > button {
  font-family: var(--display) !important; font-size: 11px !important; font-weight: 700 !important;
  letter-spacing: 0.12em !important; text-transform: uppercase !important; border-radius: 8px !important;
  border: 1px solid var(--border2) !important; background: var(--surface2) !important;
  color: var(--muted2) !important; padding: 9px 18px !important; transition: all 0.2s !important;
}
.stDownloadButton > button:hover {
  border-color: var(--accent) !important; color: var(--accent2) !important;
  background: rgba(108,99,255,0.08) !important;
}

.fit-hr { border: none; border-top: 1px solid var(--border); margin: 2rem 0 1.5rem; }

.models-footer { margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--border); }
.models-label { font-family: var(--mono); font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--muted); margin-bottom: 1rem; }
.models-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.model-chip {
  display: inline-flex; align-items: center; gap: 7px;
  background: var(--surface); border: 1px solid var(--border2); border-radius: 8px;
  padding: 8px 14px; transition: border-color 0.2s, background 0.2s;
}
.model-chip:hover { border-color: rgba(108,99,255,0.3); background: rgba(108,99,255,0.04); }
.model-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.model-name { font-family: var(--mono); font-size: 11px; font-weight: 400; color: var(--muted2); }
.model-role { font-family: var(--mono); font-size: 10px; color: var(--muted); }

.q-pill {
  display: inline-block; font-family: var(--mono); font-size: 11px; color: var(--accent3);
  background: rgba(34,211,238,0.06); border: 1px solid rgba(34,211,238,0.15);
  border-radius: 6px; padding: 4px 10px; margin: 3px 4px 3px 0;
}
</style>
""", unsafe_allow_html=True)

# ─── AGENTS META ───────────────────────────────────────────────────────────────
AGENTI = [
    {"id": "web",        "ikona": "⬡", "naziv": "Web Search",      "opis": "Pretražuje internet za aktuelne izvore"},
    {"id": "akademski",  "ikona": "◈", "naziv": "Academic",         "opis": "Dubinska analiza i sinteza izvora"},
    {"id": "reflection", "ikona": "↺", "naziv": "Self-Reflection",  "opis": "Ocjenjuje kvalitet analize i pokreće iteraciju"},
    {"id": "provjera",   "ikona": "◇", "naziv": "Fact Check",       "opis": "Provjerava tvrdnje i pouzdanost izvora"},
    {"id": "pisac",      "ikona": "▣", "naziv": "Writer",           "opis": "Sastavlja konačni strukturirani izvještaj"},
]

# ─── HTML HELPERS ───────────────────────────────────────────────────────────────
def render_orch(thinking="", status="Čekam temu istraživanja...", active=False, typing=False,
                mem_chips=None, reflection_score=None, reflection_attempts=None):
    avatar_cls = "orch-avatar pulse" if active else "orch-avatar"
    status_cls = "orch-status live" if active else "orch-status"
    thinking_cls = "thinking-box active" + (" typing" if typing else "") if active else "thinking-box"

    mem_html = ""
    if mem_chips:
        chips = ""
        for m in mem_chips:
            sim = m.get("similarity", 0)
            sim_pct = int(sim * 100)
            chips += f"""
<div style="margin-bottom:8px">
  <span class="mem-chip">↩ {m['topic'][:40]}</span>
  <div class="sim-bar-wrap">
    <div class="sim-bar-bg"><div class="sim-bar-fill" style="width:{sim_pct}%"></div></div>
    <span class="sim-pct">{sim_pct}% match</span>
  </div>
</div>"""
        mem_html = f'<div style="margin-top:12px">{chips}</div>'

    reflect_html = ""
    if reflection_score is not None:
        cls = "good" if reflection_score >= 7 else "warn"
        itr = f" · {reflection_attempts} iter." if reflection_attempts else ""
        reflect_html = f'<div><span class="reflect-badge {cls}">◎ Reflection score: {reflection_score}/10{itr}</span></div>'

    return f"""
<div class="orch-card {'active' if active else ''}">
  <div class="orch-head">
    <div class="{avatar_cls}">◉</div>
    <div>
      <div class="orch-name">Orchestrator</div>
      <div class="{status_cls}">{status}</div>
    </div>
  </div>
  <div class="{thinking_cls}">{thinking if thinking else 'Postavite temu iznad i ja ću planirati istraživanje...'}</div>
  {mem_html}
  {reflect_html}
</div>"""

def render_agent_card(meta, stanje="waiting", zadatak=None, dispatch_msg=None, preskocen=False):
    if preskocen:
        card_cls = "ag-card skipped"
        badge = '<span class="ag-badge badge-skip">— skip</span>'
        task_html = '<div class="ag-task"><em>Nije potreban</em></div>'
    elif stanje == "active":
        card_cls = "ag-card active"
        badge = '<span class="ag-badge badge-live">● running</span>'
        task_html = f'<div class="ag-task assigned">{zadatak or meta["opis"]}</div>'
    elif stanje == "done":
        card_cls = "ag-card done"
        badge = '<span class="ag-badge badge-done">✓ done</span>'
        task_html = f'<div class="ag-task assigned">{zadatak or meta["opis"]}</div>'
    else:
        card_cls = "ag-card waiting"
        badge = '<span class="ag-badge badge-wait">○ waiting</span>'
        task_html = f'<div class="ag-task">{zadatak or meta["opis"]}</div>'

    dispatch_html = f'<div class="dispatch-msg">→ {dispatch_msg}</div>' if dispatch_msg and stanje == "active" else ""
    return f"""
<div class="{card_cls}">
  <div class="ag-icon">{meta['ikona']}</div>
  <div style="flex:1;min-width:0">
    <div class="ag-name">{meta['naziv']}</div>
    {task_html}
    {dispatch_html}
  </div>
  {badge}
</div>"""

def render_agents(stanja, zadaci, dispatch_msgs):
    cards = "".join([
        render_agent_card(
            m,
            stanje=stanja.get(m["id"], "waiting"),
            zadatak=zadaci.get(m["id"], {}).get("zadatak") if not zadaci.get(m["id"], {}).get("preskoči") else None,
            dispatch_msg=dispatch_msgs.get(m["id"]) if stanja.get(m["id"]) == "active" else None,
            preskocen=zadaci.get(m["id"], {}).get("preskoči", False)
        ) for m in AGENTI
    ])
    return f'<div class="agents-grid">{cards}</div>'

def render_progress(pct):
    return f'<div class="progress-line"><div class="progress-fill" style="width:{pct}%"></div></div>'

def render_models():
    models = [
        {"name": "llama-3.3-70b",        "role": "Orchestrator + Agents", "color": "#6c63ff"},
        {"name": "ChromaDB + MiniLM-L6",  "role": "Vector Memory",         "color": "#22d3ee"},
        {"name": "Tavily Search",          "role": "Web Retrieval",          "color": "#a78bfa"},
        {"name": "LangGraph",              "role": "Agent Orchestration",    "color": "#10b981"},
        {"name": "Groq API",               "role": "Inference Engine",       "color": "#f59e0b"},
    ]
    chips = "".join([
        f'<div class="model-chip">'
        f'<div class="model-dot" style="background:{m["color"]}"></div>'
        f'<div><div class="model-name">{m["name"]}</div>'
        f'<div class="model-role">{m["role"]}</div></div>'
        f'</div>'
        for m in models
    ])
    return f'<div class="models-footer"><div class="models-label">Models & Services</div><div class="models-grid">{chips}</div></div>'

# ─── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="fit-header">
  <div>
    <div class="fit-wordmark">FIT Research</div>
    <div class="fit-title">Orchestrator<span>.</span></div>
    <div class="fit-sub">Multi-agent AI istraživački sistem &mdash; planira, pretražuje, reflektira, analizira, piše</div>
  </div>
  <div style="padding-top:6px"><div class="fit-badge">v3.0</div></div>
</div>
""", unsafe_allow_html=True)

# ─── INPUT ─────────────────────────────────────────────────────────────────────
with st.form(key="input_zone", border=False):
    st.markdown('<div class="input-label">↳ tema istraživanja</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([5, 1])
    with col1:
        tema = st.text_input("tema", placeholder="npr. vještačka inteligencija u medicini...", label_visibility="collapsed")
    with col2:
        pokreni = st.form_submit_button("▶ Run", use_container_width=True)

ph_orch    = st.empty()
ph_sec     = st.empty()
ph_agents  = st.empty()
ph_prog    = st.empty()
ph_hr      = st.empty()
ph_results = st.empty()
ph_footer  = st.empty()

if not pokreni:
    ph_orch.markdown(render_orch(), unsafe_allow_html=True)
    ph_footer.markdown(render_models(), unsafe_allow_html=True)

# ─── PIPELINE ──────────────────────────────────────────────────────────────────
if pokreni and tema:
    ph_footer.empty()
    ph_orch.markdown(render_orch(
        thinking=f'Tema: "{tema}"\n\nAnaliziram zahtjev i pretražujem semantičku memoriju...',
        status="Inicijalizacija...", active=True, typing=True
    ), unsafe_allow_html=True)
    ph_sec.markdown('<div class="sec-label">Agenti</div>', unsafe_allow_html=True)
    ph_agents.markdown(render_agents({a["id"]: "waiting" for a in AGENTI}, {}, {}), unsafe_allow_html=True)
    ph_prog.markdown(render_progress(0), unsafe_allow_html=True)
    time.sleep(0.4)

    ph_orch.markdown(render_orch(
        thinking=f'Tema: "{tema}"\n\nPokrećem pipeline...',
        status="Pokrećem agente...", active=True
    ), unsafe_allow_html=True)

    rezultat = run_research(tema)

    razmisljanje   = rezultat.get("orchestrator_reasoning", "")
    upiti          = rezultat.get("search_queries", [])
    memorija_mem   = rezultat.get("related_memories", [])
    refl_score     = rezultat.get("reflection_score", 0)
    refl_attempts  = rezultat.get("reflection_attempts", 0)

    mem_nota = ""
    if memorija_mem:
        teme_str = ", ".join(f'"{m["topic"]}"' for m in memorija_mem[:2])
        avg_sim = int(sum(m.get("similarity", 0) for m in memorija_mem) / len(memorija_mem) * 100)
        mem_nota = f"\n\n[Semantička memorija aktivna — {len(memorija_mem)} srodnih tema, prosj. sličnost {avg_sim}%]"

    ph_orch.markdown(render_orch(
        thinking=razmisljanje + mem_nota,
        status="Strategija osmišljena — distribucija zadataka...",
        active=True,
        mem_chips=memorija_mem if memorija_mem else None
    ), unsafe_allow_html=True)
    ph_prog.markdown(render_progress(10), unsafe_allow_html=True)
    time.sleep(0.6)

    zadaci = {
        "web":        {"zadatak": f"Pretraži: {' / '.join(upiti[:2])}", "preskoči": False},
        "akademski":  {"zadatak": "Dubinska analiza + semantička memorija", "preskoči": False},
        "reflection": {"zadatak": f"Self-reflection ocjena: {refl_score}/10 ({refl_attempts} iteracija)", "preskoči": False},
        "provjera":   {"zadatak": "Validacija tvrdnji, ocjena pouzdanosti", "preskoči": False},
        "pisac":      {"zadatak": "Sinteza izvještaja + ažuriranje ChromaDB memorije", "preskoči": False},
    }
    dispatch_msgs = {
        "web":        f'Orchestrator → "Pretraži: {", ".join(upiti[:2])}"',
        "akademski":  'Orchestrator → "Analiziraj uz semantički memorijski kontekst."',
        "reflection": 'Orchestrator → "Ocijeni analizu. Iteracija ako score < 7."',
        "provjera":   'Orchestrator → "Provjeri ključne tvrdnje."',
        "pisac":      'Orchestrator → "Sintetiziraj i ažuriraj ChromaDB memoriju."',
    }

    stanja = {a["id"]: "waiting" for a in AGENTI}
    ph_agents.markdown(render_agents(stanja, zadaci, {}), unsafe_allow_html=True)
    time.sleep(0.4)

    total = len(AGENTI)
    for i, meta in enumerate(AGENTI):
        aid = meta["id"]
        stanja[aid] = "active"
        ph_agents.markdown(render_agents(stanja, zadaci, dispatch_msgs), unsafe_allow_html=True)
        ph_prog.markdown(render_progress(10 + int(((i) / total) * 80)), unsafe_allow_html=True)
        time.sleep(0.9)
        stanja[aid] = "done"
        ph_agents.markdown(render_agents(stanja, zadaci, {}), unsafe_allow_html=True)
        ph_prog.markdown(render_progress(10 + int(((i + 1) / total) * 80)), unsafe_allow_html=True)
        time.sleep(0.35)

    ph_prog.markdown(render_progress(100), unsafe_allow_html=True)
    ph_orch.markdown(render_orch(
        thinking=f'Istraživanje teme "{tema}" kompletno.\n\nSelf-reflection ocjena: {refl_score}/10 ({refl_attempts} iteracija).\nSvi agenti završili. Pogledaj rezultate ispod.',
        status="✓ Istraživanje završeno",
        active=False,
        mem_chips=memorija_mem if memorija_mem else None,
        reflection_score=refl_score,
        reflection_attempts=refl_attempts
    ), unsafe_allow_html=True)
    time.sleep(0.3)

    ph_hr.markdown('<div class="fit-hr"></div>', unsafe_allow_html=True)

    with ph_results.container():
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["▣ Izvještaj", "◈ Analiza", "↺ Reflection", "◇ Provjera", "◉ Memorija"])

        with tab1:
            izvjestaj = rezultat.get("final_report", "")
            st.markdown(izvjestaj)
            st.markdown("---")
            st.download_button(
                "↓ Preuzmi izvještaj (.md)",
                data=izvjestaj,
                file_name=f"fitorch_{tema[:30].replace(' ','_')}.md",
                mime="text/markdown"
            )

        with tab2:
            st.markdown(rezultat.get("academic_analysis", ""))

        with tab3:
            score = rezultat.get("reflection_score", 0)
            attempts = rezultat.get("reflection_attempts", 0)
            feedback = rezultat.get("reflection_feedback", "Nema povratnih informacija.")

            col1, col2 = st.columns(2)
            col1.metric("Reflection ocjena", f"{score}/10")
            col2.metric("Iteracija", attempts)

            st.markdown("**Povratna informacija Self-Reflection agenta:**")
            st.info(feedback if feedback else "Analiza prihvaćena bez primjedbi.")

            if score >= 7:
                st.success(f"✓ Analiza prošla provjeru kvaliteta ({score}/10)")
            else:
                st.warning(f"⚠ Analiza iterirana {attempts}x (finalna ocjena: {score}/10)")

        with tab4:
            st.markdown(rezultat.get("fact_check", ""))

        with tab5:
            stats = get_memory_stats()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Istraživanja", stats["total_researches"])
            c2.metric("Tema (JSON)", stats["topics_count"])
            c3.metric("Vektora (ChromaDB)", stats["vector_memories"])
            c4.metric("Domene", len(stats["domains_learned"]))

            if memorija_mem:
                st.markdown("**Semantički srodni pogodoci:**")
                for m in memorija_mem:
                    sim_pct = int(m.get("similarity", 0) * 100)
                    st.markdown(
                        f'<span class="mem-chip">↩ {m["topic"][:50]} — {sim_pct}% match</span>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("Nova tema — rezultati sačuvani u ChromaDB za semantička buduća istraživanja.")

            if stats["learning_log"]:
                st.markdown("**Log učenja:**")
                for e in reversed(stats["learning_log"]):
                    st.markdown(f"- `[{e.get('timestamp','')}]` {e.get('event','')}")

        with st.expander("Korišteni upiti"):
            queries_html = "".join([f'<span class="q-pill">{q}</span>' for q in upiti])
            st.markdown(f'<div style="padding:6px 0">{queries_html}</div>', unsafe_allow_html=True)

        with st.expander("Log aktivnosti agenata"):
            for msg in rezultat.get("messages", []):
                if isinstance(msg, AIMessage):
                    st.markdown(f"- {msg.content}")

    ph_footer.markdown(render_models(), unsafe_allow_html=True)

elif pokreni and not tema:
    ph_orch.markdown(render_orch(), unsafe_allow_html=True)
    st.warning("Unesite temu istraživanja.")
    ph_footer.markdown(render_models(), unsafe_allow_html=True)