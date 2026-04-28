"""
FASAL DOCTOR — PDF Extractor
=============================
Extracts crop disease + treatment data from PARC/AARI/CCRI PDF bulletins
using Gemini API. Outputs structured JSON records ready for the dataset.

Usage:
    python src/pdf_extractor.py --pdf data/raw/your_bulletin.pdf
    python src/pdf_extractor.py --folder data/raw/
    python src/pdf_extractor.py --url https://parc.gov.pk/...
"""

import os, sys, json, time, hashlib, argparse, logging
from pathlib import Path
from datetime import datetime
from typing import Optional

import fitz
import google.generativeai as genai
from colorama import Fore, Style, init

init(autoreset=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/extractor.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

GEMINI_MODEL   = "gemini-1.5-flash"
MAX_CHARS_PAGE = 3000
CHUNK_PAGES    = 4
RETRY_LIMIT    = 3
RETRY_DELAY    = 5
COUNTRY_CODE   = "PK"
VERIFIED_YEAR  = datetime.now().year

EXTRACTION_PROMPT = """
You are an expert agricultural scientist specializing in Pakistani crop diseases.
Analyze the following text from a Pakistani agricultural research bulletin and
extract ALL crop diseases mentioned. Return ONLY a valid JSON array with no
explanation, no markdown, no code fences.

Each item must follow this exact schema:
{{
  "crop_name_en": "English crop name",
  "crop_name_ur": "Urdu crop name or empty string",
  "disease_name_en": "Full English disease name",
  "disease_name_ur": "Urdu disease name or empty string",
  "pathogen_type": "Fungal | Bacterial | Viral | Insect Pest | Nematode | Physiological | Unknown",
  "symptoms_en": "Detailed symptom description 2-4 sentences",
  "symptoms_ur": "Urdu translation of symptoms or empty string",
  "affected_part": "comma-separated: Leaves, Stem, Root, Fruit, Seed, Flower, Whole Plant",
  "season": "Rabi | Kharif | Both | Unknown",
  "region_pakistan": "comma-separated provinces or All or Unknown",
  "climate_trigger": "weather conditions that cause disease",
  "severity_level": "Critical | High | Medium | Low | Unknown",
  "spray_chemical_en": "active ingredient and formulation",
  "brand_name_pakistan": "local Pakistan brand names or empty string",
  "dose_per_acre": "dosage instructions or empty string",
  "spray_timing": "when to apply",
  "safety_precautions_ur": "Urdu safety warnings or empty string",
  "biological_control": "resistant varieties or non-chemical methods",
  "economic_loss_pct": "yield loss estimate or empty string",
  "data_source": "{source}",
  "verified_year": "{year}",
  "country_code": "PK",
  "confidence": "High | Medium | Low",
  "extraction_notes": "caveats or missing info for reviewer"
}}

Rules:
- Extract EVERY disease mentioned, even if info is incomplete
- If a field is not in the text, use empty string — never invent data
- For spray info, extract EXACTLY what the text says
- Return ONLY the JSON array. No other text.

TEXT:
{text}
"""


class PDFExtractor:
    def __init__(self, api_key: str, country: str = "PK"):
        genai.configure(api_key=api_key)
        self.model   = genai.GenerativeModel(GEMINI_MODEL)
        self.country = country
        self.stats   = {"pages": 0, "chunks": 0, "records": 0, "errors": 0}

    def extract_pdf_text(self, pdf_path: str) -> list:
        doc   = fitz.open(pdf_path)
        pages = []
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            if len(text) > 100:
                pages.append({"page_num": i + 1, "text": text})
        doc.close()
        self.stats["pages"] += len(pages)
        log.info(f"  Extracted {len(pages)} text pages from {Path(pdf_path).name}")
        return pages

    def pages_to_chunks(self, pages: list) -> list:
        chunks = []
        for i in range(0, len(pages), CHUNK_PAGES):
            group = pages[i : i + CHUNK_PAGES]
            text  = "\n\n--- PAGE BREAK ---\n\n".join(
                p["text"][:MAX_CHARS_PAGE] for p in group
            )
            chunks.append({
                "chunk_id":  i // CHUNK_PAGES + 1,
                "page_from": group[0]["page_num"],
                "page_to":   group[-1]["page_num"],
                "text":      text,
            })
        return chunks

    def call_gemini(self, text: str, source: str) -> list:
        prompt = EXTRACTION_PROMPT.format(text=text, source=source, year=VERIFIED_YEAR)
        for attempt in range(1, RETRY_LIMIT + 1):
            try:
                resp = self.model.generate_content(prompt)
                raw  = resp.text.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                raw     = raw.strip()
                records = json.loads(raw)
                if not isinstance(records, list):
                    records = [records]
                return records
            except json.JSONDecodeError as e:
                log.warning(f"    JSON parse error attempt {attempt}: {e}")
            except Exception as e:
                log.warning(f"    Gemini error attempt {attempt}: {e}")
            if attempt < RETRY_LIMIT:
                time.sleep(RETRY_DELAY * attempt)
        self.stats["errors"] += 1
        return []

    def process_pdf(self, pdf_path: str, source_name: str = "") -> list:
        pdf_path = str(pdf_path)
        source   = source_name or Path(pdf_path).stem
        print(f"\n{Fore.CYAN}Processing: {Path(pdf_path).name}{Style.RESET_ALL}")
        log.info(f"Processing PDF: {pdf_path}")

        pages = self.extract_pdf_text(pdf_path)
        if not pages:
            log.warning("  No extractable text (scanned PDF?)")
            return []

        chunks      = self.pages_to_chunks(pages)
        all_records = []
        seen        = set()

        for chunk in chunks:
            print(f"  Chunk {chunk['chunk_id']} (pages {chunk['page_from']}-{chunk['page_to']})...", end=" ", flush=True)
            records = self.call_gemini(chunk["text"], source)
            self.stats["chunks"] += 1
            new = 0
            for rec in records:
                key = f"{rec.get('crop_name_en','').lower()}|{rec.get('disease_name_en','').lower()}"
                h   = hashlib.md5(key.encode()).hexdigest()
                if h not in seen and rec.get("disease_name_en"):
                    seen.add(h)
                    rec["source_file"] = Path(pdf_path).name
                    rec["chunk_pages"] = f"{chunk['page_from']}-{chunk['page_to']}"
                    all_records.append(rec)
                    new += 1
            print(f"{Fore.GREEN}+{new} records{Style.RESET_ALL}")
            time.sleep(1)

        self.stats["records"] += len(all_records)
        print(f"  {Fore.GREEN}Done: {len(all_records)} unique records{Style.RESET_ALL}")
        return all_records

    def process_folder(self, folder: str) -> list:
        folder = Path(folder)
        pdfs   = list(folder.glob("*.pdf")) + list(folder.glob("*.PDF"))
        if not pdfs:
            log.warning(f"No PDFs found in {folder}")
            return []
        print(f"\n{Fore.CYAN}Found {len(pdfs)} PDFs in {folder}{Style.RESET_ALL}")
        all_records = []
        for pdf in pdfs:
            all_records.extend(self.process_pdf(str(pdf)))
        return all_records

    def assign_ids(self, records: list, start: int = 1) -> list:
        for i, rec in enumerate(records, start=start):
            rec["id"] = f"{self.country}-{i:03d}"
        return records

    def print_summary(self):
        print(f"\n{'='*50}")
        print(f"{Fore.GREEN}EXTRACTION COMPLETE{Style.RESET_ALL}")
        print(f"  Pages processed : {self.stats['pages']}")
        print(f"  API calls made  : {self.stats['chunks']}")
        print(f"  Records found   : {self.stats['records']}")
        print(f"  Errors          : {self.stats['errors']}")
        print(f"{'='*50}\n")


def download_pdf(url: str, dest_folder: str = "data/raw") -> Optional[str]:
    import requests
    dest = Path(dest_folder)
    dest.mkdir(parents=True, exist_ok=True)
    filename = url.split("/")[-1].split("?")[0]
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"
    out_path = dest / filename
    print(f"  Downloading {url}")
    resp = requests.get(url, timeout=60, stream=True)
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)
    print(f"  {Fore.GREEN}Saved {out_path.stat().st_size // 1024} KB → {out_path}{Style.RESET_ALL}")
    return str(out_path)


def main():
    parser = argparse.ArgumentParser(description="Fasal Doctor PDF Extractor")
    parser.add_argument("--pdf",    help="Single PDF file path")
    parser.add_argument("--folder", help="Folder containing PDFs")
    parser.add_argument("--url",    help="URL to download and process")
    parser.add_argument("--source", default="", help="Source institution name")
    parser.add_argument("--out",    default="data/processed/extracted.json")
    parser.add_argument("--append", action="store_true")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print(f"{Fore.RED}ERROR: Set GEMINI_API_KEY environment variable{Style.RESET_ALL}")
        print("  export GEMINI_API_KEY='your_key_here'")
        sys.exit(1)

    Path("logs").mkdir(exist_ok=True)
    extractor = PDFExtractor(api_key)
    records   = []

    if args.url:
        pdf_path = download_pdf(args.url)
        records  = extractor.process_pdf(pdf_path, args.source)
    elif args.pdf:
        records = extractor.process_pdf(args.pdf, args.source)
    elif args.folder:
        records = extractor.process_folder(args.folder)
    else:
        parser.print_help()
        sys.exit(1)

    out_path = Path(args.out)
    existing = []
    if args.append and out_path.exists():
        with open(out_path) as f:
            existing = json.load(f)
        print(f"  Loaded {len(existing)} existing records to merge")

    all_records = extractor.assign_ids(existing + records, start=1)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)

    extractor.print_summary()
    print(f"{Fore.GREEN}Saved {len(all_records)} total records → {out_path}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
