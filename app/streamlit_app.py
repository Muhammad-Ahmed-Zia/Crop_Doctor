"""FASAL DOCTOR v2.0 — Professional Streamlit UI"""
import sys, os, re
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
os.chdir(ROOT)

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="فصل ڈاکٹر | Fasal Doctor", page_icon="🌾",
                   layout="wide", initial_sidebar_state="expanded")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@300;400;500;600&family=Noto+Nastaliq+Urdu:wght@400;600;700&display=swap');
:root{--g9:#14532d;--g7:#15803d;--g6:#16a34a;--g3:#86efac;--g2:#bbf7d0;--g1:#dcfce7;--g0:#f0fdf4;--tx:#111827;--tm:#6b7280;--wh:#ffffff;}
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:linear-gradient(160deg,#f0fdf4 0%,#f9fffe 100%);}
#MainMenu,footer,header{visibility:hidden!important;}
/* sidebar */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0f2d1f 0%,#14532d 50%,#0f2d1f 100%);}
[data-testid="stSidebar"] *{color:#e8f5ee!important;}
[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,0.12)!important;}
[data-testid="stSidebar"] .stSelectbox>div>div{background:rgba(255,255,255,0.10)!important;border:1px solid rgba(255,255,255,0.20)!important;border-radius:10px!important;}
[data-testid="stSidebar"] .stRadio label{color:#d1fae5!important;font-size:0.9rem!important;}
[data-testid="collapsedControl"]{background:#16a34a!important;border-radius:0 10px 10px 0!important;width:28px!important;padding:12px 4px!important;box-shadow:2px 0 8px rgba(0,0,0,0.2)!important;}
[data-testid="collapsedControl"] svg{fill:white!important;stroke:white!important;}
/* disease card — FORCE all text visible */
.dc,.dc *{color:#111827!important;}
.safety-blk,.safety-blk *{color:#92400e!important;}
.urdu-text{font-family:'Noto Nastaliq Urdu',serif!important;direction:rtl!important;text-align:right!important;color:#1a1a1a!important;line-height:2.4!important;}
/* buttons */
.stButton>button{background:white!important;color:#15803d!important;border:1.5px solid #86efac!important;border-radius:999px!important;font-size:0.82rem!important;padding:6px 16px!important;font-weight:500!important;transition:all .2s!important;}
.stButton>button:hover{background:#f0fdf4!important;border-color:#16a34a!important;transform:translateY(-1px)!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#16a34a,#14532d)!important;color:white!important;border:none!important;border-radius:14px!important;padding:14px 36px!important;font-size:1.05rem!important;font-weight:700!important;box-shadow:0 6px 20px rgba(22,163,74,.35)!important;}
.stButton>button[kind="primary"]:hover{transform:translateY(-2px)!important;box-shadow:0 10px 28px rgba(22,163,74,.45)!important;}
/* textarea */
.stTextArea textarea{border:2px solid #dcfce7!important;border-radius:14px!important;font-size:1rem!important;background:#f9fffe!important;}
.stTextArea textarea:focus{border-color:#16a34a!important;}
/* stat pill */
.pill{display:inline-block;background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.3);border-radius:999px;padding:7px 18px;font-weight:600;color:white;font-size:0.88rem;margin:4px;}
/* stat card sidebar */
.scard{background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:12px;padding:12px 8px;text-align:center;margin:4px 0;}
.snum{font-size:1.6rem;font-weight:700;color:#6ee7b7!important;}
.slbl{font-size:0.75rem;color:#a7f3d0!important;margin-top:2px;}
/* history */
.hitem{background:#f0fdf4;border-radius:10px;border-left:3px solid #16a34a;padding:8px 12px;margin:5px 0;font-size:0.84rem;color:#374151;}
/* response sections */
.rs{background:white;border:1.5px solid #dcfce7;border-radius:16px;padding:22px 26px;margin:12px 0;box-shadow:0 4px 20px rgba(22,163,74,.08);}
.rs-title{font-size:0.82rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#15803d;margin-bottom:10px;}
.treat-grid{background:#f0fdf4;border:1px solid #86efac;border-radius:12px;padding:14px 18px;}
.treat-row{display:flex;gap:12px;padding:5px 0;border-bottom:1px solid #dcfce7;align-items:baseline;}
.treat-row:last-child{border-bottom:none;}
.treat-label{font-weight:600;color:#15803d!important;min-width:110px;font-size:0.88rem;}
.treat-val{color:#111827!important;font-size:0.95rem;}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.6;transform:scale(1.1)}}
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="🌱 Loading AI engine...")
def load_engine():
    from rag_engine import get_diagnosis, get_retriever
    get_retriever()
    return get_diagnosis

try:
    from rag_engine import get_retriever
    _col, _ = get_retriever()
    RECORD_COUNT = _col.count()
except Exception:
    RECORD_COUNT = "..."


def severity_badge(text: str) -> str:
    tl = text.lower()
    if any(w in tl for w in ["critical","severe","emergency"]):
        return "<span style='background:#fee2e2;color:#991b1b;padding:4px 14px;border-radius:999px;font-size:.78rem;font-weight:700;'>🔴 CRITICAL</span>"
    if any(w in tl for w in ["high","serious"]):
        return "<span style='background:#ffedd5;color:#9a3412;padding:4px 14px;border-radius:999px;font-size:.78rem;font-weight:700;'>🟠 HIGH</span>"
    if any(w in tl for w in ["medium","moderate"]):
        return "<span style='background:#fef9c3;color:#854d0e;padding:4px 14px;border-radius:999px;font-size:.78rem;font-weight:700;'>🟡 MEDIUM</span>"
    return "<span style='background:#dcfce7;color:#166534;padding:4px 14px;border-radius:999px;font-size:.78rem;font-weight:700;'>🟢 LOW</span>"


def rx(pattern, text, default="—"):
    m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return m.group(1).strip().replace("**","").replace("*","") if m else default


def strip_md(s: str) -> str:
    return re.sub(r'\*+', '', s).strip()


def render_card(query: str, response: str):
    dis_en  = rx(r'Disease Name.*?:\*?\*?\s*(.+)', response)
    dis_ur  = rx(r'بیماری کا نام.*?:\*?\*?\s*(.+)', response)
    crop_en = rx(r'Affected Crop.*?:\*?\*?\s*(.+)', response)
    crop_ur = rx(r'متاثرہ فصل.*?:\*?\*?\s*(.+)', response)
    sym_en  = rx(r'\*\*English:\*\*\s*(.+)', response)
    sym_ur  = rx(r'\*\*اردو:\*\*\s*(.+)', response)
    chem    = rx(r'Spray Chemical.*?:\*?\*?\s*(.+)', response)
    brand   = rx(r'Pakistan Brand.*?:\*?\*?\s*(.+)', response)
    dose    = rx(r'Dose per Acre.*?:\*?\*?\s*(.+)', response)
    timing  = rx(r'Spray Timing.*?:\*?\*?\s*(.+)', response)
    sev     = rx(r'Severity.*?:\*?\*?\s*(.+)', response)
    yloss   = rx(r'Yield Loss.*?:\*?\*?\s*(.+)', response)

    # Safety block — multi-line Urdu after SAFETY WARNING header
    safety_m = re.search(r'SAFETY WARNING.*?---\s*([\s\S]+?)---', response, re.IGNORECASE)
    safety_txt = strip_md(safety_m.group(1)) if safety_m else ""

    # Bio control
    bio_m = re.search(r'BIOLOGICAL CONTROL.*?---\s*([\s\S]+?)(?:---|$)', response, re.IGNORECASE)
    bio_txt = strip_md(bio_m.group(1)) if bio_m else ""

    badge = severity_badge(response)

    # ── Header card ──
    st.markdown(f"""
    <div class='dc rs'>
      <div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px;'>
        <div>
          <div style='font-family:Plus Jakarta Sans,sans-serif;font-size:1.35rem;font-weight:700;color:#14532d!important;'>{dis_en}</div>
          <div class='urdu-text' style='font-size:1.15rem;color:#14532d!important;margin-top:4px;'>{strip_md(dis_ur)}</div>
          <div style='font-size:0.88rem;color:#6b7280!important;margin-top:6px;'>🌾 {crop_en} &nbsp;|&nbsp; <span style='font-family:Noto Nastaliq Urdu,serif;'>{strip_md(crop_ur)}</span></div>
        </div>
        <div>{badge}</div>
      </div>
      <div style='font-size:0.8rem;color:#9ca3af!important;margin-top:8px;'>Query: <em>{query[:80]}</em></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Symptoms ──
    st.markdown(f"""
    <div class='dc rs'>
      <div class='rs-title'>🔍 SYMPTOMS | علامات</div>
      <div style='color:#111827!important;margin-bottom:10px;'>{strip_md(sym_en)}</div>
      <div class='urdu-text' style='font-size:17px;'>{strip_md(sym_ur)}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Treatment ──
    st.markdown(f"""
    <div class='dc rs'>
      <div class='rs-title'>💊 TREATMENT | علاج</div>
      <div class='treat-grid'>
        <div class='treat-row'><span class='treat-label'>Chemical</span><span class='treat-val'>{strip_md(chem)}</span></div>
        <div class='treat-row'><span class='treat-label'>Pakistan Brand 🇵🇰</span><span class='treat-val'>{strip_md(brand)}</span></div>
        <div class='treat-row'><span class='treat-label'>Dose / Acre</span><span class='treat-val'>{strip_md(dose)}</span></div>
        <div class='treat-row'><span class='treat-label'>Timing</span><span class='treat-val'>{strip_md(timing)}</span></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Safety ──
    if safety_txt and safety_txt != "—":
        st.markdown(f"""
        <div class='safety-blk rs' style='background:#fffbeb;border:1.5px solid #fde68a;border-left:5px solid #f59e0b;'>
          <div class='rs-title' style='color:#92400e!important;'>⚠️ SAFETY WARNING | حفاظتی ہدایات</div>
          <div class='urdu-text' style='color:#92400e!important;font-size:17px;'>{safety_txt}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Severity & Bio ──
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class='dc rs' style='height:100%;'>
          <div class='rs-title'>📊 SEVERITY & LOSSES | نقصانات</div>
          <div style='color:#111827!important;font-size:0.95rem;'><strong>Severity:</strong> {strip_md(sev)}</div>
          <div style='color:#111827!important;font-size:0.95rem;margin-top:6px;'><strong>Yield Loss:</strong> {strip_md(yloss)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        bio_display = bio_txt if bio_txt and bio_txt != "—" else "Consult local agricultural extension officer."
        st.markdown(f"""
        <div class='dc rs' style='height:100%;'>
          <div class='rs-title'>🌿 BIOLOGICAL CONTROL | قدرتی طریقہ</div>
          <div style='color:#111827!important;font-size:0.93rem;line-height:1.7;'>{bio_display}</div>
        </div>
        """, unsafe_allow_html=True)


# ── Data ──────────────────────────────────────────────────────────────────────
CROPS = {"🌍 All Crops — تمام فصلیں":None,"🌾 Wheat — گندم":"Wheat","🌿 Cotton — کپاس":"Cotton",
         "🌾 Rice — چاول":"Rice","🎋 Sugarcane — گنا":"Sugarcane","🌽 Maize — مکئی":"Maize",
         "🥜 Groundnut — مونگ پھلی":"Groundnut","🌱 Barley — جَو":"Barley","🌾 Sorghum — جوار":"Sorghum",
         "🌾 Millet — باجرہ":"Millet","🌿 Brassica — سرسوں":"Brassica","🌱 Gram — چنا":"Gram",
         "🌿 Coriander — دھنیا":"Coriander","🌾 Paddy — دھان":"Paddy","🌱 Lentil — مسور":"Lentil"}
LANG_MAP = {"Both (default)":"both","English":"english","اردو (Urdu)":"urdu"}
EXAMPLES = ["Yellow spots on wheat leaves","Cotton leaves curling upward",
            "Rice plants turning brown","Maize stem rotting at base",
            "میری گندم کے پتوں پر پیلے دھبے ہیں","کپاس کے پتے اوپر مڑ رہے ہیں"]

for k,v in [("chat_history",[]),("query_input",""),("last_response",None),("trigger_query",None)]:
    if k not in st.session_state: st.session_state[k] = v

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:16px 0 20px;'>
      <div style='font-size:2.8rem;'>🌾</div>
      <div style='font-family:Noto Nastaliq Urdu,serif;font-size:1.4rem;font-weight:700;color:#6ee7b7;'>فصل ڈاکٹر</div>
      <div style='font-size:0.82rem;color:#a7f3d0;margin-top:4px;'>Fasal Doctor v2.0</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("**🌱 Crop | فصل**")
    crop_label = st.selectbox("crop", list(CROPS.keys()), index=0, label_visibility="collapsed")
    crop_filter = CROPS[crop_label]

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("**🌐 Language | زبان**")
    language = st.radio("lang", list(LANG_MAP.keys()), index=0, label_visibility="collapsed")
    lang_code = LANG_MAP[language]

    st.markdown("<hr>", unsafe_allow_html=True)
    cols = st.columns(3)
    for col, num, lbl in zip(cols, [f"{RECORD_COUNT}","19+","✓"], ["Records","Crops","AI"]):
        with col:
            st.markdown(f"<div class='scard'><div class='snum'>{num}</div><div class='slbl'>{lbl}</div></div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""<div style='font-size:0.84rem;line-height:1.8;'>
    ℹ️ AI crop disease advisor using Pakistan's PARC disease database + Google Gemini.<br><br>
    <span style='font-family:Noto Nastaliq Urdu,serif;direction:rtl;display:block;font-size:0.9rem;'>
    پاکستانی کسانوں کے لیے اردو میں تشخیص۔</span><br>
    <strong>Source:</strong> PARC Pakistan
    </div>""", unsafe_allow_html=True)
    st.markdown("""<div style='background:rgba(245,158,11,.18);border:1px solid rgba(245,158,11,.35);border-radius:10px;padding:10px 14px;font-size:0.82rem;margin-top:10px;color:#92400e!important;'>
    ⚠️ Consult a local agronomist before applying any spray.<br>
    <span style='font-family:Noto Nastaliq Urdu,serif;direction:rtl;display:block;font-size:0.85rem;'>سپرے سے پہلے زرعی ماہر سے مشورہ کریں۔</span>
    </div>""", unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(135deg,#14532d 0%,#16a34a 55%,#4ade80 100%);
  border-radius:24px;padding:40px 44px;margin-bottom:28px;
  box-shadow:0 8px 32px rgba(21,128,61,.30);display:flex;
  align-items:center;justify-content:space-between;flex-wrap:wrap;gap:20px;'>
  <div style='display:flex;align-items:center;gap:22px;'>
    <div style='font-size:4rem;line-height:1;'>🌾</div>
    <div>
      <div style='font-family:Plus Jakarta Sans,sans-serif;font-size:2.6rem;font-weight:800;color:#fff;line-height:1.1;'>Fasal Doctor</div>
      <div style='font-family:Noto Nastaliq Urdu,serif;font-size:1.9rem;color:#bbf7d0;direction:rtl;line-height:1.7;'>فصل ڈاکٹر</div>
      <div style='font-size:0.95rem;color:rgba(255,255,255,.80);margin-top:4px;'>🤖 AI Crop Disease Advisor — PARC Database + Gemini AI</div>
    </div>
  </div>
  <div>
    <span class='pill'>🦠 {RECORD_COUNT} Diseases</span>
    <span class='pill'>🌾 19 Crops</span>
    <span class='pill'>⚡ Gemini AI</span>
  </div>
</div>
""", unsafe_allow_html=True)

col_main, col_aside = st.columns([3, 1], gap="large")

with col_main:
    tab1, tab2 = st.tabs(["💬 Chat / چیٹ", "🧙 Symptom Wizard / علامات گائیڈ"])
    
    with tab1:
        st.markdown("**💡 Try an Example | مثالی سوال**")
        ecols = st.columns(3)
        for i, ex in enumerate(EXAMPLES):
            with ecols[i % 3]:
                if st.button(ex, key=f"ex_{i}", use_container_width=True):
                    st.session_state.query_input = ex
                    st.session_state.trigger_query = ex
                    st.rerun()

        st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
        st.markdown("**🔍 Describe Symptoms | علامات بیان کریں**")
        query_text = st.text_area("q", value=st.session_state.query_input, height=120,
            placeholder="E.g.: Yellow powdery spots on wheat leaves...\nمثلاً: گندم کے پتوں پر پیلے دھبے...",
            label_visibility="collapsed")

        b1, b2, b3 = st.columns([2.5, 2, 1])
        with b1:
            go = st.button("🔬 Diagnose | تشخیص کریں", type="primary", use_container_width=True)
        with b2:
            if crop_filter: st.info(f"🌱 Filter: **{crop_filter}**")
            else: st.caption("🌍 All crops")
        with b3:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.update(query_input="", last_response=None, trigger_query=None)
                st.rerun()

        if go and not query_text.strip():
            st.warning("Please describe your crop problem. / براہ کرم فصل کی بیماری بیان کریں۔")

    with tab2:
        from symptom_wizard import render_wizard
        render_wizard(crop_filter)

    active = None
    if 'go' in locals() and go and query_text.strip(): active = query_text.strip()
    elif st.session_state.trigger_query:
        active = st.session_state.trigger_query
        st.session_state.trigger_query = None

    if active:
        st.session_state.query_input = active
        with st.spinner(""):
            st.markdown(f"""<div style='text-align:center;padding:36px;'>
              <div style='font-size:2.8rem;animation:pulse 1.5s infinite;'>🌾</div>
              <div style='font-size:1.05rem;color:#16a34a;font-weight:600;margin-top:10px;'>Searching {RECORD_COUNT} disease records...</div>
              <div style='font-family:Noto Nastaliq Urdu,serif;direction:rtl;color:#6b7280;margin-top:6px;font-size:1rem;'>بیماری کی تشخیص جاری ہے...</div>
            </div>""", unsafe_allow_html=True)
            try:
                fn = load_engine()
                result = fn(query=active, crop_filter=crop_filter, language=lang_code)
                st.session_state.last_response = (active, result)
                hist = st.session_state.chat_history
                if active not in hist: hist.insert(0, active)
                st.session_state.chat_history = hist[:5]
            except Exception as e:
                st.error(f"❌ Error running diagnosis: {e}")
                st.session_state.last_response = None
        st.rerun()

    if st.session_state.last_response:
        q, res = st.session_state.last_response
        
        if res == "UNKNOWN_CROP_FLAG" or "UNKNOWN_CROP_FLAG" in res:
            st.error("I don't have specific data for this. Please consult your local agronomist or call 0800-KISSAN Pakistan helpline.\n\nاس بارے میں میرے پاس مخصوص معلومات نہیں۔ مقامی زرعی ماہر سے رابطہ کریں یا پاکستان کسان ہیلپ لائن 0800-55476 پر کال کریں۔")
        else:
            if "LOW_CONFIDENCE_FLAG" in res:
                st.warning("Low confidence diagnosis. Please describe more symptoms or use the symptom wizard.\n\nکم اعتماد تشخیص۔ براہ کرم مزید علامات بتائیں یا گائیڈڈ وزرڈ استعمال کریں۔")
            if "CROP_MISMATCH_FLAG" in res:
                st.info("Showing closest match — results may not be specific to your crop.\n\nقریب ترین نتیجہ دکھایا جا رہا ہے۔")
                
            if "API_ERROR_FLAG" in res:
                st.warning("AI generation unavailable. Showing database records directly.")
                raw_context = res.replace("API_ERROR_FLAG", "").replace("LOW_CONFIDENCE_FLAG", "").replace("CROP_MISMATCH_FLAG", "")
                st.markdown(f"```text\n{raw_context}\n```")
            else:
                render_card(q, res)

    st.markdown("""<div style='text-align:center;padding:32px 0 10px;border-top:1px solid #dcfce7;margin-top:40px;'>
      <div style='font-size:1.4rem;'>🌾</div>
      <div style='font-size:0.82rem;color:#6b7280;margin-top:6px;'>Fasal Doctor v2.0 — Built for Pakistani Farmers</div>
      <div style='font-family:Noto Nastaliq Urdu,serif;direction:rtl;font-size:0.9rem;color:#16a34a;margin-top:4px;'>پاکستانی کسانوں کے لیے — فصل ڈاکٹر</div>
      <div style='font-size:0.76rem;color:#9ca3af;margin-top:6px;'>Data: PARC Pakistan | AI: Google Gemini | Vectors: ChromaDB</div>
      <div style='background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.2);border-radius:10px;padding:10px 14px;font-size:0.82rem;margin-top:15px;color:#92400e;display:inline-block;'>
        ⚠️ Always confirm with a local agronomist before applying any spray.<br>
        <span style='font-family:Noto Nastaliq Urdu,serif;direction:rtl;display:block;font-size:0.85rem;'>اسپرے کرنے سے پہلے ہمیشہ مقامی زرعی ماہر سے تصدیق کریں۔</span>
      </div>
    </div>""", unsafe_allow_html=True)

with col_aside:
    st.markdown("""<div style='background:white;border:1.5px solid #dcfce7;border-radius:16px;padding:16px;margin-bottom:14px;'>
      <div style='font-size:0.82rem;font-weight:700;color:#15803d;text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;'>🕐 Recent Questions</div>""",
      unsafe_allow_html=True)
    if st.session_state.chat_history:
        for i, q in enumerate(st.session_state.chat_history):
            is_ur = bool(re.search(r'[\u0600-\u06FF]', q))
            st.markdown(f"<div class='hitem' style='{'direction:rtl;' if is_ur else ''}'><strong>#{i+1}</strong> {q[:55]}{'...' if len(q)>55 else ''}</div>",
                unsafe_allow_html=True)
    else:
        st.caption("No recent questions.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""<div style='background:white;border:1.5px solid #dcfce7;border-radius:16px;padding:16px;margin-bottom:14px;'>
      <div style='font-size:0.82rem;font-weight:700;color:#15803d;text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;'>💡 Tips | تجاویز</div>
      <div style='font-size:0.84rem;color:#374151;line-height:1.9;'>✅ Mention leaf colour<br>✅ Describe spot shape<br>✅ State growth stage<br>✅ Mention affected part<br>✅ Urdu or English!</div>
      <div style='font-family:Noto Nastaliq Urdu,serif;direction:rtl;font-size:0.88rem;color:#374151;line-height:2.2;margin-top:10px;'>پتوں کا رنگ بتائیں<br>فصل کی عمر بتائیں<br>اردو یا انگریزی میں لکھیں</div>
    </div>""", unsafe_allow_html=True)

    try:
        load_engine()
        st.markdown(f"<div style='background:white;border:1.5px solid #dcfce7;border-radius:16px;padding:14px;'><div style='background:#dcfce7;color:#166534;border-radius:10px;padding:8px 14px;font-size:0.85rem;font-weight:600;text-align:center;'>✅ AI Engine Ready</div><div style='background:#eff6ff;color:#1d4ed8;border-radius:10px;padding:8px 14px;font-size:0.85rem;font-weight:600;text-align:center;margin-top:6px;'>⚡ {RECORD_COUNT} Vectors Loaded</div></div>", unsafe_allow_html=True)
    except:
        st.warning("⏳ Engine loading...")
