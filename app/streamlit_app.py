"""
FASAL DOCTOR — Streamlit Web UI
================================
Run from project root:
    streamlit run app/streamlit_app.py
"""

import sys, os, re
from pathlib import Path

# ── Make src/ importable ──────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent          # D:\MObile App Project\fasal-doctor
sys.path.insert(0, str(ROOT / "src"))
os.chdir(ROOT)                               # ensure relative paths (data/) work

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

# ── Page config (MUST be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="فصل ڈاکٹر | Fasal Doctor",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Fasal Doctor — AI Crop Disease Advisor for Pakistani Farmers | فصل ڈاکٹر",
    },
)

# ── CSS: green theme + Urdu RTL font ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Root variables ── */
:root {
    --green-deep:   #1a4731;
    --green-mid:    #2d7a4f;
    --green-light:  #4caf7d;
    --green-pale:   #e8f5ee;
    --amber:        #f59e0b;
    --red:          #ef4444;
    --orange:       #f97316;
    --card-bg:      #ffffff;
    --text-dark:    #1a2e1a;
    --text-muted:   #6b7280;
    --border:       #d1fae5;
    --shadow:       0 4px 24px rgba(45,122,79,0.10);
}

/* ── Global ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%); }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer { visibility: hidden; }
header { visibility: hidden; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--green-deep) 0%, #0f2d1f 100%);
    border-right: none;
}
[data-testid="stSidebar"] * { color: #e8f5ee !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label { color: #a7f3d0 !important; font-weight: 500; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15) !important; }

/* ── Header banner ── */
.fasal-header {
    background: linear-gradient(135deg, var(--green-deep) 0%, var(--green-mid) 60%, var(--green-light) 100%);
    border-radius: 20px;
    padding: 32px 40px;
    margin-bottom: 28px;
    box-shadow: var(--shadow);
    display: flex;
    align-items: center;
    gap: 24px;
}
.fasal-header .title-en {
    font-size: 2.4rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.5px;
    line-height: 1.1;
}
.fasal-header .title-ur {
    font-family: 'Noto Nastaliq Urdu', serif;
    font-size: 2rem;
    color: #a7f3d0;
    direction: rtl;
    line-height: 1.6;
}
.fasal-header .subtitle {
    font-size: 1.05rem;
    color: rgba(255,255,255,0.78);
    margin-top: 6px;
}

/* ── Urdu text blocks ── */
.urdu-text {
    font-family: 'Noto Nastaliq Urdu', serif;
    direction: rtl;
    text-align: right;
    font-size: 18px;
    line-height: 2.4;
    color: var(--text-dark);
}
.urdu-small {
    font-family: 'Noto Nastaliq Urdu', serif;
    direction: rtl;
    text-align: right;
    font-size: 15px;
    line-height: 2.2;
    color: var(--text-muted);
}

/* ── Disease result card ── */
.disease-card {
    background: var(--card-bg);
    border: 1.5px solid var(--border);
    border-radius: 18px;
    padding: 28px 32px;
    margin-top: 20px;
    box-shadow: var(--shadow);
}
.card-section {
    border-left: 4px solid var(--green-mid);
    padding: 14px 18px;
    margin: 14px 0;
    background: var(--green-pale);
    border-radius: 0 10px 10px 0;
}
.card-section-title {
    font-size: 0.88rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--green-mid);
    margin-bottom: 6px;
}

/* ── Severity badge ── */
.badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.badge-critical { background: #fee2e2; color: #b91c1c; }
.badge-high     { background: #ffedd5; color: #c2410c; }
.badge-medium   { background: #fef9c3; color: #854d0e; }
.badge-low      { background: #dcfce7; color: #166534; }

/* ── Example question buttons ── */
.example-btn {
    display: inline-block;
    background: var(--green-pale);
    border: 1.5px solid var(--border);
    border-radius: 22px;
    padding: 8px 16px;
    margin: 4px;
    font-size: 0.88rem;
    color: var(--green-deep);
    cursor: pointer;
    transition: all 0.2s;
    font-weight: 500;
}
.example-btn:hover {
    background: var(--green-light);
    color: white;
    border-color: var(--green-light);
}

/* ── Chat history ── */
.chat-item {
    background: #f8fffe;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 10px 16px;
    margin: 6px 0;
    font-size: 0.9rem;
    color: var(--text-muted);
}
.chat-item strong { color: var(--green-deep); }

/* ── Input box ── */
.stTextArea textarea {
    border-radius: 12px !important;
    border: 2px solid var(--border) !important;
    font-size: 1rem !important;
    padding: 14px !important;
    transition: border 0.2s !important;
}
.stTextArea textarea:focus {
    border-color: var(--green-mid) !important;
    box-shadow: 0 0 0 3px rgba(45,122,79,0.12) !important;
}

/* ── Primary button ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--green-mid), var(--green-deep)) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 32px !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 14px rgba(45,122,79,0.30) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(45,122,79,0.40) !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: var(--green-mid) !important; }

/* ── Stat cards ── */
.stat-card {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 12px;
    padding: 14px;
    text-align: center;
    margin: 6px 0;
}
.stat-number { font-size: 1.8rem; font-weight: 700; color: #6ee7b7; }
.stat-label  { font-size: 0.8rem; color: #a7f3d0; margin-top: 2px; }

/* ── Disclaimer ── */
.disclaimer {
    background: rgba(245,158,11,0.18);
    border: 1px solid rgba(245,158,11,0.35);
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 0.85rem;
    color: #92400e;
    margin-top: 12px;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# ── Load RAG engine (cached — loads model only once) ─────────────────────────
@st.cache_resource(show_spinner="🌱 Loading Fasal Doctor AI Engine...")
def load_engine():
    from rag_engine import get_diagnosis, get_retriever
    get_retriever()          # warm up: loads ChromaDB + sentence transformer
    return get_diagnosis

# ── Crop options ──────────────────────────────────────────────────────────────
CROPS = {
    "🌍 All Crops — تمام فصلیں":  None,
    "🌾 Wheat — گندم":             "Wheat",
    "🌿 Cotton — کپاس":            "Cotton",
    "🌾 Rice — چاول":              "Rice",
    "🎋 Sugarcane — گنا":          "Sugarcane",
    "🌽 Maize — مکئی":             "Maize",
    "🥜 Groundnut — مونگ پھلی":    "Groundnut",
    "🌱 Barley — جَو":             "Barley",
    "🌾 Sorghum — جوار":           "Sorghum",
    "🌾 Millet — باجرہ":           "Millet",
    "🌿 Brassica — سرسوں":         "Brassica",
    "🌱 Gram — چنا":               "Gram",
    "🌿 Coriander — دھنیا":        "Coriander",
    "🌾 Paddy — دھان":             "Paddy",
    "🌱 Lentil — مسور":            "Lentil",
}

EXAMPLE_QUESTIONS = [
    "Yellow spots on wheat leaves",
    "Cotton leaves curling upward",
    "Rice plants turning brown",
    "Maize stem rotting at base",
    "میری گندم کے پتوں پر پیلے دھبے ہیں",
    "کپاس کے پتے اوپر مڑ رہے ہیں",
]

# ── Session state init ────────────────────────────────────────────────────────
if "chat_history"  not in st.session_state: st.session_state.chat_history  = []
if "query_input"   not in st.session_state: st.session_state.query_input   = ""
if "last_response" not in st.session_state: st.session_state.last_response = None
if "trigger_query" not in st.session_state: st.session_state.trigger_query = None

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 10px 0 20px;'>
        <div style='font-size:3rem;'>🌾</div>
        <div style='font-size:1.3rem; font-weight:700; color:#6ee7b7;'>فصل ڈاکٹر</div>
        <div style='font-size:0.85rem; color:#a7f3d0;'>Fasal Doctor</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Crop selector ──
    st.markdown("**🌱 Select Crop | فصل منتخب کریں**")
    selected_crop_label = st.selectbox(
        "Crop",
        options=list(CROPS.keys()),
        index=0,
        label_visibility="collapsed",
    )
    crop_filter = CROPS[selected_crop_label]

    st.markdown("---")

    # ── Language toggle ──
    st.markdown("**🌐 Response Language | زبان**")
    language = st.radio(
        "Language",
        options=["Both (default)", "English", "اردو (Urdu)"],
        index=0,
        label_visibility="collapsed",
    )
    lang_map = {"Both (default)": "both", "English": "english", "اردو (Urdu)": "urdu"}
    lang_code = lang_map[language]

    st.markdown("---")

    # ── Dataset stats ──
    st.markdown("**📊 Dataset Info**")
    st.markdown("""
    <div class='stat-card'><div class='stat-number'>427</div><div class='stat-label'>Disease Records</div></div>
    <div class='stat-card'><div class='stat-number'>14+</div><div class='stat-label'>Crops Covered</div></div>
    <div class='stat-card'><div class='stat-number'>427</div><div class='stat-label'>ChromaDB Vectors</div></div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── About ──
    st.markdown("""
    **ℹ️ About | تعارف**

    Fasal Doctor uses AI + a Pakistan-specific crop disease database (PARC) to help farmers diagnose plant diseases and get treatment advice in Urdu & English.

    <div class='urdu-small'>
    فصل ڈاکٹر پاکستانی کسانوں کی مدد کے لیے بنایا گیا ہے۔
    </div>

    **Data Source:** PARC Pakistan Agricultural Research Council
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='disclaimer'>
    ⚠️ <strong>Disclaimer:</strong> Always consult your local agronomist before applying any spray.<br>
    <span class='urdu-small'>سپرے کرنے سے پہلے مقامی زرعی ماہر سے مشورہ ضرور کریں۔</span>
    </div>
    """, unsafe_allow_html=True)


# ── MAIN CONTENT ──────────────────────────────────────────────────────────────

# ── Header ──
st.markdown("""
<div class='fasal-header'>
    <div style='font-size:3.5rem;'>🌾</div>
    <div>
        <div class='title-en'>Fasal Doctor</div>
        <div class='title-ur'>فصل ڈاکٹر</div>
        <div class='subtitle'>🤖 AI Crop Disease Advisor — Powered by PARC Database + Gemini AI</div>
    </div>
</div>
""", unsafe_allow_html=True)

col_main, col_history = st.columns([3, 1], gap="large")

with col_main:

    # ── Example questions ──
    st.markdown("**💡 Example Questions | مثالی سوالات**")
    cols = st.columns(3)
    for i, example in enumerate(EXAMPLE_QUESTIONS):
        with cols[i % 3]:
            if st.button(example, key=f"ex_{i}", use_container_width=True):
                st.session_state.query_input   = example
                st.session_state.trigger_query = example
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Query input ──
    st.markdown("**🔍 Describe Symptoms | علامات بیان کریں**")
    query_text = st.text_area(
        label="Query",
        value=st.session_state.query_input,
        height=110,
        placeholder=(
            "E.g.: Yellow powdery spots on wheat leaves, plant wilting...\n"
            "مثلاً: گندم کے پتوں پر پیلے دھبے، پودا مرجھا رہا ہے..."
        ),
        label_visibility="collapsed",
        key="main_query_area",
    )

    col_btn1, col_btn2, col_clear = st.columns([2, 2, 1])
    with col_btn1:
        diagnose_clicked = st.button(
            "🔬 Diagnose | تشخیص کریں",
            type="primary",
            use_container_width=True,
        )
    with col_btn2:
        if crop_filter:
            st.info(f"🌱 Filtered: {selected_crop_label}", icon=None)
    with col_clear:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.query_input   = ""
            st.session_state.last_response = None
            st.session_state.trigger_query = None
            st.rerun()

    # ── Determine active query ──
    active_query = None
    if diagnose_clicked and query_text.strip():
        active_query = query_text.strip()
    elif st.session_state.trigger_query:
        active_query = st.session_state.trigger_query
        st.session_state.trigger_query = None

    # ── Run diagnosis ──
    if active_query:
        st.session_state.query_input = active_query

        with st.spinner("🔍 Searching disease database & generating diagnosis..."):
            try:
                get_diagnosis = load_engine()
                response = get_diagnosis(
                    query=active_query,
                    crop_filter=crop_filter,
                    language=lang_code,
                )
                st.session_state.last_response = (active_query, response)
                # Add to history (keep last 5)
                st.session_state.chat_history.insert(0, active_query)
                st.session_state.chat_history = st.session_state.chat_history[:5]
            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.session_state.last_response = None

    # ── Display response ──
    if st.session_state.last_response:
        q, response = st.session_state.last_response
        render_disease_card(q, response)


# ── History column ──
with col_history:
    st.markdown("**🕐 Recent Questions**")
    if st.session_state.chat_history:
        for i, past_q in enumerate(st.session_state.chat_history):
            st.markdown(f"""
            <div class='chat-item'>
                <strong>#{i+1}</strong><br>
                {past_q[:60]}{"..." if len(past_q) > 60 else ""}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(
            "<div style='color:#9ca3af; font-size:0.88rem;'>No questions yet</div>",
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**🔑 Quick Tips**")
    st.markdown("""
    <div style='font-size:0.85rem; color:#4b5563; line-height:1.9;'>
    ✅ Describe leaf colour<br>
    ✅ Mention crop growth stage<br>
    ✅ Say if roots are affected<br>
    ✅ Ask in Urdu or English<br>
    <br>
    <span class='urdu-small'>
    پتوں کا رنگ بتائیں<br>
    فصل کی عمر بتائیں<br>
    جڑ یا تنے کی بات کریں
    </span>
    </div>
    """, unsafe_allow_html=True)


# ── Disease card renderer (defined after st.cache_resource call) ──────────────
def render_disease_card(query: str, response: str):
    """Parse the Gemini markdown response and render a styled card."""

    # ── Detect severity from text ──
    severity_badge = ""
    resp_lower = response.lower()
    if any(w in resp_lower for w in ["critical", "severe", "emergency"]):
        severity_badge = "<span class='badge badge-critical'>🔴 Critical</span>"
    elif any(w in resp_lower for w in ["high", "serious", "significant"]):
        severity_badge = "<span class='badge badge-high'>🟠 High</span>"
    elif any(w in resp_lower for w in ["medium", "moderate"]):
        severity_badge = "<span class='badge badge-medium'>🟡 Medium</span>"
    else:
        severity_badge = "<span class='badge badge-low'>🟢 Low–Moderate</span>"

    st.markdown(f"""
    <div class='disease-card'>
        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
            <span style='font-size:1.15rem; font-weight:700; color:#1a4731;'>🦠 Diagnosis Result</span>
            {severity_badge}
        </div>
        <div style='font-size:0.85rem; color:#6b7280; margin-bottom:16px;'>
            Query: <em>{query[:80]}{"..." if len(query)>80 else ""}</em>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Render full Gemini markdown response ──
    st.markdown(response)

    # ── Urdu text blocks (extract lines with Urdu chars) ──
    urdu_lines = [
        line.strip() for line in response.split("\n")
        if re.search(r'[\u0600-\u06FF]', line) and len(line.strip()) > 10
    ]
    if urdu_lines:
        urdu_html = "<br>".join(urdu_lines)
        st.markdown(f"""
        <div class='disease-card' style='margin-top:16px; border-color:#bbf7d0;'>
            <div class='card-section-title'>📖 اردو خلاصہ — Urdu Summary</div>
            <div class='urdu-text'>{urdu_html}</div>
        </div>
        """, unsafe_allow_html=True)
