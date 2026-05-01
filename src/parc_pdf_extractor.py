import fitz  # PyMuPDF
import json
import os
import re
import sys
import time
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ── Load API Key ──────────────────────────────────────────────
load_dotenv()
# ── API Key Rotation ──────────────────────────────────────────
API_KEYS = [
    os.getenv("GEMINI_API_KEY"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
     # add more if you have them
]
API_KEYS = [k for k in API_KEYS if k]  # remove None values

current_key_index = 0
client = genai.Client(api_key=API_KEYS[0])

def rotate_key():
    """Switch to the next available API key"""
    global current_key_index, client
    current_key_index += 1
    if current_key_index >= len(API_KEYS):
        print("\n⛔ ALL API KEYS EXHAUSTED for today.")
        print(f"   Resume tomorrow with: python src/parc_pdf_extractor.py {{page_num}}")
        return False
    client = genai.Client(api_key=API_KEYS[current_key_index])
    print(f"\n🔄 Switched to API key #{current_key_index + 1}")
    return True

# ── Config ────────────────────────────────────────────────────
PDF_PATH    = "data/raw/pdfs/Plant_Disease_compressed.pdf"
OUTPUT_JSON = "data/processed/parc_diseases.json"
OUTPUT_CSV  = "data/processed/parc_diseases.csv"
END_PAGE    = 300
SLEEP_SEC   = 4  # free tier minimum

EXTRACT_PROMPT = """
You are an agricultural expert. Read this page from a Pakistan 
plant disease book published by PARC (Pakistan Agricultural 
Research Council).

Extract ALL diseases mentioned on this page.
For each disease return a JSON array like this:

[
  {
    "crop_name": "Wheat",
    "disease_name_en": "Yellow Rust",
    "disease_name_urdu": "زرد زنگ",
    "symptoms_en": "Yellow stripes on leaves, powdery spores",
    "affected_part": "Leaves",
    "disease_stage": "Early/Mid/Severe",
    "recommended_spray_en": "Propiconazole 25% EC",
    "spray_dosage": "250ml per acre",
    "spray_timing": "Apply at first sign of disease",
    "season": "Rabi",
    "source": "PARC Plant Diseases Book"
  }
]

Rules:
- Return ONLY the JSON array, no extra text
- If Urdu name unknown, write English name
- If spray not mentioned, write "Consult agronomist"
- If no disease on this page, return empty array []
- Extract ALL diseases on the page, not just one
"""

# ── PDF → Image ───────────────────────────────────────────────
def pdf_page_to_image(pdf_path, page_num):
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    mat = fitz.Matrix(2.0, 2.0)
    pix = page.get_pixmap(matrix=mat)
    doc.close()
    return pix.tobytes("jpeg")

# ── Gemini call with smart retry ──────────────────────────────
def call_gemini(image_bytes):
    global client
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[
                EXTRACT_PROMPT,
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
            ]
        )
        return response.text.strip(), "ok"

    except Exception as e:
        err = str(e)
        print(f"  🔍 DEBUG error: {err[:300]}")  # ADD THIS — see full error

        # Daily quota exhausted — try next key
        if "limit: 0" in err or "GenerateRequestsPerDay" in err:
            print(f"  🔑 Key #{current_key_index + 1} exhausted, rotating...")  # ADD THIS
            if rotate_key():
                return call_gemini(image_bytes)  # retry with new key
            return None, "daily_exhausted"

        # Per-minute rate limit — wait and retry same key
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            delay = SLEEP_SEC
            match = re.search(r"retryDelay.*?(\d+)s", err)
            if match:
                delay = int(match.group(1)) + 3
            return str(delay), "rate_limit"

        return str(e), "error"
# ── Parse Gemini response → list of dicts ─────────────────────
def parse_response(text, page_num):
    try:
        # Strip markdown fences if present
        text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.MULTILINE)
        text = re.sub(r"```$", "", text.strip(), flags=re.MULTILINE)
        diseases = json.loads(text.strip())
        print(f"  ✅ Found {len(diseases)} disease(s)")
        return diseases
    except json.JSONDecodeError:
        print(f"  ⚠️  Could not parse JSON — skipping page")
        return []

# ── Save progress ─────────────────────────────────────────────
def save_progress(diseases):
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(diseases, f, ensure_ascii=False, indent=2)
    if diseases:
        df = pd.DataFrame(diseases)
        df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

# ── Load existing progress (for resume) ───────────────────────
def load_existing():
    if Path(OUTPUT_JSON).exists():
        with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# ── Main ──────────────────────────────────────────────────────
def run_extraction(start_page):
    print("=" * 50)
    print("  FASAL DOCTOR — PARC PDF Extractor")
    print("=" * 50)
    print(f"\n📄 Processing pages {start_page} to {END_PAGE}")
    print(f"📚 PDF: {PDF_PATH}\n")

    # Resume existing records
    all_diseases = load_existing()
    print(f"📂 Loaded {len(all_diseases)} existing records\n")

    total = END_PAGE - start_page + 1

    for i, page_num in enumerate(range(start_page - 1, END_PAGE)):
        display_page = page_num + 1
        print(f"[{i+1}/{total}] Processing page {display_page}...")

        # Convert to image
        image_bytes = pdf_page_to_image(PDF_PATH, page_num)

        # Retry loop for per-minute rate limits
        while True:
            text, status = call_gemini(image_bytes)

            if status == "ok":
                diseases = parse_response(text, display_page)
                for d in diseases:
                    d["source_page"] = display_page
                all_diseases.extend(diseases)
                save_progress(all_diseases)  # save after EVERY page
                break

            elif status == "rate_limit":
                wait = int(text)
                print(f"  ⏳ Rate limited — waiting {wait}s...")
                time.sleep(wait)
                continue  # retry same page

            elif status == "daily_exhausted":
                # Save and tell user exactly how to resume
                save_progress(all_diseases)
                print("\n" + "=" * 50)
                print("  ⛔ DAILY QUOTA EXHAUSTED")
                print(f"  💾 Saved {len(all_diseases)} records")
                print(f"\n  Resume tomorrow with:")
                print(f"  python src/parc_pdf_extractor.py {display_page}")
                print("=" * 50)
                sys.exit(0)

            else:  # unexpected error — skip page
                print(f"  ❌ Unexpected error: {text[:120]}")
                break

        time.sleep(SLEEP_SEC)

    # Done
    save_progress(all_diseases)
    print("\n" + "=" * 50)
    print(f"  ✅ EXTRACTION COMPLETE")
    print(f"  📊 Total records: {len(all_diseases)}")
    print(f"  💾 JSON: {OUTPUT_JSON}")
    print(f"  📄 CSV:  {OUTPUT_CSV}")
    print("=" * 50)


if __name__ == "__main__":
    # Usage: python src/parc_pdf_extractor.py [start_page]
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    run_extraction(start)