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

Fasal Doctor is a bilingual (Urdu & English) crop disease diagnostic system designed for Pakistani farmers. It uses a Retrieval-Augmented Generation (RAG) architecture over a carefully curated database of local agricultural knowledge.

[![Live Demo](https://img.shields.io/badge/Live_Demo_on_HuggingFace-Green?style=for-the-badge&logo=huggingface)](https://huggingface.co/spaces/YOUR_USERNAME/fasal-doctor)

---

## 📸 Screenshots

*(Replace these with your actual Demo Video and Screenshots links)*

**💬 Bilingual Chat Interface**  
*(Image: chat diagnosis)*

**🧙 Guided Symptom Wizard**  
*(Image: symptom wizard)*

---

## 🏗️ System Architecture

Fasal Doctor's RAG pipeline operates as follows:

```text
Farmer's Symptom Query (English or Urdu)
       ↓
ChromaDB Vector Store (671 vectors, multilingual embeddings)
       ↓
Top-3 closest disease records retrieved
       ↓
Gemini 2.0 Flash AI generates bilingual response using retrieved context
       ↓
Streamlit UI (Farmers) / FastAPI (Mobile apps)
```

---

## 📊 Dataset Statistics

- **671** localized disease records
- **19** total crops covered (Wheat, Rice, Cotton, Maize, Potato, Tomato, Mango, Onion, Chickpea, Sugarcane, etc.)
- **Pakistan-specific** commercial spray brands (e.g., Tilt 250EC, Dithane M-45)
- **Sources**: PARC Plant Diseases Book, CABI PlantWise, AARI, CCRI, and manual curation.

---

## 🚀 How to Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/fasal-doctor.git
cd fasal-doctor

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add API keys
# Copy .env.example to .env and add your GEMINI_API_KEY
# You can also add GEMINI_RAG_KEY_3, 5, 6, 7 for rotation

# 4. Build ChromaDB embeddings (first run only)
python src/embedder.py

# 5. Launch the Streamlit User Interface
streamlit run app/streamlit_app.py

# 6. OR Launch the FastAPI Backend
python -m uvicorn api.fasal_server:app --host 127.0.0.1 --port 8000 --reload
```

---

## 📈 Progress Log

- **Day 1-3:** PDF Data extraction (651 records)
- **Day 4:** Data merger + Urdu enrichment pipeline
- **Day 5:** ChromaDB multilingual embeddings + RAG engine
- **Day 6:** Streamlit UI + FastAPI server
- **Day 7:** Added 5 new major crops + guided Symptom Wizard
- **Day 8:** Advanced error handling + 50-query automated test suite
- **Day 9:** Bug fixes + HuggingFace Spaces & Railway deployments
- **Day 10:** Demo video recording & Launch

---

## ⚠️ Disclaimer | انتباہ

**English:**
AI diagnostics may occasionally be inaccurate. The spray recommendations and dosages provided are based on general guidelines. **Always confirm with a local agronomist before purchasing or applying any agricultural chemicals.**

**Urdu:**
مصنوعی ذہانت (AI) سے کی گئی تشخیص بعض اوقات غلط ہو سکتی ہے۔ اسپرے کی سفارشات اور مقدار عام ہدایات پر مبنی ہیں۔ **کوئی بھی زرعی دوا خریدنے یا استعمال کرنے سے پہلے ہمیشہ اپنے مقامی زرعی ماہر سے مشورہ اور تصدیق ضرور کریں۔**
