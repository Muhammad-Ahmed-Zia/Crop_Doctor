---
title: Fasal Doctor
emoji: 🌾
colorFrom: green
colorTo: green
sdk: streamlit
sdk_version: 1.32.0
app_file: app.py
pinned: false
---

# Fasal Doctor (فصل ڈاکٹر) 🌾

> **Pakistan's First AI Agronomist — Powered by Google Gemini & ChromaDB**

Fasal Doctor is a bilingual (Urdu & English) crop disease diagnostic system built for Pakistani farmers. It uses a Retrieval-Augmented Generation (RAG) architecture over a carefully curated database of 671 localized disease records from PARC Pakistan.

[![GitHub](https://img.shields.io/badge/GitHub-Muhammad--Ahmed--Zia-black?style=for-the-badge&logo=github)](https://github.com/Muhammad-Ahmed-Zia/Health-Risk-AI)
[![Live Demo](https://img.shields.io/badge/Live_Demo_on_HuggingFace-green?style=for-the-badge&logo=huggingface)](https://huggingface.co/spaces/YOUR_USERNAME/fasal-doctor)
[![FastAPI](https://img.shields.io/badge/FastAPI_Backend-Railway-purple?style=for-the-badge&logo=railway)](https://your-app.up.railway.app)

---

## 📸 Screenshots

*(Add your demo video link and screenshots after recording Day 10 video)*

**💬 Bilingual Chat Interface** — Describe symptoms in Urdu or English, get instant disease name + spray brand + Urdu safety warnings  
**🧙 Guided Symptom Wizard** — 5-step wizard for farmers who cannot describe symptoms in text

---

## 🏗️ System Architecture

```text
Farmer's Symptom Query (English / Urdu / Romanized Urdu)
       ↓
Query Normalizer  ←  Romanized Urdu word map (gandum→wheat, patte→leaves …)
       ↓
ChromaDB Vector Store  (671 disease vectors, multilingual MiniLM embeddings)
       ↓
Top-3 closest disease records retrieved
       ↓
Gemini 2.0 Flash  →  structured bilingual diagnosis (EN + UR)
       ↓
Streamlit UI  /  FastAPI REST API  /  Flutter (future)
```

---

## 📊 Dataset Statistics

| Stat | Value |
|---|---|
| Disease records | **671** |
| Crops covered | **19** (Wheat, Cotton, Rice, Sugarcane, Maize, Potato, Tomato, Onion, Chickpea, Groundnut, Mango, Barley, Sorghum, Millet, Brassica, Gram, Lentil, Coriander, Paddy) |
| Spray brands | Pakistan-specific (Tilt 250EC, Dithane M-45, Confidor, …) |
| Languages | Urdu + English (bilingual output) |
| Sources | PARC Plant Diseases Book, AARI, CCRI, CABI PlantWise, manual curation |

---

## 🧪 Test Suite Results

Automated 50-query suite — Urdu, English & Romanized Urdu:

| Metric | Score |
|---|---|
| **Overall** | **46 / 50 (92%)** |
| Core disease queries | 43 / 46 passed |
| Edge-case / off-topic filters | 7 / 8 passed |
| Romanized Urdu queries | 100% correctly resolved |

---

## 🚀 How to Run Locally

```bash
# 1. Clone
git clone https://github.com/Muhammad-Ahmed-Zia/Health-Risk-AI.git
cd Health-Risk-AI

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file and add your keys:
#    GEMINI_API_KEY=your_primary_key
#    GEMINI_RAG_KEY_3=key3   (optional — for rotation)
#    GEMINI_RAG_KEY_5=key5
#    GEMINI_RAG_KEY_6=key6
#    GEMINI_RAG_KEY_7=key7

# 4. Build ChromaDB embeddings (first run only, ~3 min)
python src/embedder.py

# 5. Run Streamlit UI
streamlit run app/streamlit_app.py

# 6. OR run FastAPI backend (serves HTML frontend at /app/)
python -m uvicorn fasal_server:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🔧 Technical Stack

| Layer | Technology |
|---|---|
| AI Model | Google Gemini 2.0 Flash (via `google-genai`) |
| Vector DB | ChromaDB (persistent, local) |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` |
| UI | Streamlit (primary) + HTML/CSS/JS (web) |
| Backend API | FastAPI + Uvicorn |
| API Rotation | 4-key round-robin on 429/503 errors |
| Languages | Python 3.12 |

---

## 📈 10-Day Progress Log

| Day | Work Done |
|---|---|
| Day 1–3 | PDF extraction from PARC book — 651 raw disease records |
| Day 4 | Data merger + Urdu enrichment pipeline |
| Day 5 | ChromaDB multilingual embeddings + RAG engine |
| Day 6 | Streamlit UI + FastAPI server + 4-page HTML frontend |
| Day 7 | 5 new crops + guided Symptom Wizard |
| Day 8 | Error handling, off-topic guard, 50-query test suite |
| Day 9 | Bug fixes + HuggingFace Spaces & Railway deployments |
| Day 10 | Demo video recording & LinkedIn launch |

---

## ⚠️ Disclaimer | انتباہ

**English:** AI diagnostics may occasionally be inaccurate. Spray recommendations are based on general guidelines. **Always confirm with a local agronomist before applying any agricultural chemicals.**

**Urdu:** مصنوعی ذہانت سے کی گئی تشخیص بعض اوقات غلط ہو سکتی ہے۔ **کوئی بھی زرعی دوا استعمال کرنے سے پہلے ہمیشہ اپنے مقامی زرعی ماہر سے مشورہ ضرور کریں۔**

---

*Built in 10 days for Pakistani farmers. Feedback from agronomists welcome!*
