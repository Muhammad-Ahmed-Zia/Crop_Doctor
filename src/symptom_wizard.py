"""
FASAL DOCTOR — Symptom Wizard (TASK 2)
"""
import streamlit as st

def render_wizard(crop_name):
    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = 1
    if "wizard_answers" not in st.session_state:
        st.session_state.wizard_answers = {}

    st.markdown("### 🧙 Symptom Wizard | علامات گائیڈ")
    st.markdown("Answer 5 simple questions to get a diagnosis. / بیماری کی تشخیص کے لیے 5 آسان سوالات کے جوابات دیں۔")
    
    step = st.session_state.wizard_step
    
    st.progress(step / 5, text=f"Step {step} of 5")
    
    questions = {
        1: {
            "en": "Which part of plant is affected?",
            "ur": "پودے کا کون سا حصہ متاثر ہے؟",
            "key": "part",
            "options": [
                ("🍃 Leaves", "پتے", "leaves"),
                ("🌿 Stem", "تنا", "stem"),
                ("🌱 Roots", "جڑیں", "roots"),
                ("🌸 Flowers", "پھول", "flowers"),
                ("🍎 Fruit/Grain", "پھل/دانہ", "fruit/grain"),
                ("🌾 Whole Plant", "پورا پودا", "whole plant")
            ]
        },
        2: {
            "en": "What color change do you see?",
            "ur": "آپ کو کون سا رنگ بدلتا ہوا نظر آ رہا ہے؟",
            "key": "color",
            "options": [
                ("🟡 Yellow", "پیلا", "yellow color"),
                ("🟤 Brown/Black", "بھورا/کالا", "brown/black color"),
                ("⚪ White/Gray powder", "سفید/خاکستری پاؤڈر", "white/gray powder"),
                ("🔴 Red/Orange spots", "سرخ/نارنجی دھبے", "red/orange spots"),
                ("🟢 No color change", "رنگ نہیں بدلا", "no color change")
            ]
        },
        3: {
            "en": "What does it look like?",
            "ur": "یہ کیسا لگتا ہے؟",
            "key": "pattern",
            "options": [
                ("○ Spots/patches", "دھبے", "spots/patches"),
                ("≡ Stripes/lines", "دھاریاں", "stripes/lines"),
                ("∿ Curling/wilting", "مڑنا/مرجھانا", "curling/wilting"),
                ("⬛ Rotting", "سڑنا", "rotting"),
                ("🌫 Powdery coating", "پاؤڈر جیسی تہہ", "powdery coating")
            ]
        },
        4: {
            "en": "How fast is it spreading?",
            "ur": "یہ کتنی تیزی سے پھیل رہا ہے؟",
            "key": "speed",
            "options": [
                ("🔴 Very fast (1-2 days)", "بہت تیز", "spreading very fast"),
                ("🟡 Moderate (few days)", "درمیانہ", "spreading moderately"),
                ("🟢 Slow (weeks)", "آہستہ", "spreading slowly")
            ]
        },
        5: {
            "en": "What is the weather like now?",
            "ur": "اب موسم کیسا ہے؟",
            "key": "weather",
            "options": [
                ("🌧 Wet/Rainy", "بارش/نمی", "in wet/rainy weather"),
                ("☀ Hot/Dry", "گرم/خشک", "in hot/dry weather"),
                ("🌫 Cool/Foggy", "ٹھنڈا/دھند", "in cool/foggy weather"),
                ("🌤 Normal", "معمول", "in normal weather")
            ]
        }
    }
    
    if step <= 5:
        q = questions[step]
        st.markdown(f"**{q['en']}**<br><span class='urdu-text' style='font-size:1.1rem; display:block;'>{q['ur']}</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        for opt_en, opt_ur, val in q["options"]:
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button(f"{opt_en}", key=f"step_{step}_{val}_en", use_container_width=True):
                    st.session_state.wizard_answers[q["key"]] = val
                    st.session_state.wizard_step += 1
                    st.rerun()
            with c2:
                if st.button(f"{opt_ur}", key=f"step_{step}_{val}_ur", use_container_width=True):
                    st.session_state.wizard_answers[q["key"]] = val
                    st.session_state.wizard_step += 1
                    st.rerun()
                    
        st.markdown("<hr>", unsafe_allow_html=True)
        if step > 1:
            if st.button("⬅️ Back / پیچھے", use_container_width=False):
                st.session_state.wizard_step -= 1
                st.rerun()
    else:
        ans = st.session_state.wizard_answers
        crop_text = crop_name if crop_name else "Crop"
        
        query = f"{crop_text} plant with {ans.get('part', '')} showing {ans.get('color', '')} {ans.get('pattern', '')} {ans.get('speed', '')} {ans.get('weather', '')} conditions"
        
        st.success("✅ Information Collected! / معلومات جمع ہو گئیں!")
        
        st.markdown(f"**Summary:**<br>_{query}_", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Get Diagnosis / تشخیص کریں", type="primary", use_container_width=True):
                st.session_state.query_input = query
                st.session_state.trigger_query = query
                st.session_state.wizard_step = 1
                st.session_state.wizard_answers = {}
                # Active tab session state
                st.session_state.active_tab = 0
                st.rerun()
        with col2:
            if st.button("🔄 Restart / دوبارہ شروع کریں", use_container_width=True):
                st.session_state.wizard_step = 1
                st.session_state.wizard_answers = {}
                st.rerun()
