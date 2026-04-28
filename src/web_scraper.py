"""
FASAL DOCTOR — Web Scraper for Pakistan Agricultural Sources
=============================================================
Scrapes disease information from free online sources:
- PlantwisePlus (CABI) — disease fact sheets
- FAO crop protection pages
- Agri.Punjab.gov.pk extension advisories

Usage:
    python src/web_scraper.py --crop wheat --country PK
    python src/web_scraper.py --all-crops
"""

import os, sys, json, time, argparse
from pathlib import Path

try:
    import requests
    from colorama import Fore, Style, init
    import google.generativeai as genai
    init(autoreset=True)
except ImportError as e:
    print(f"Missing package: {e}. Run: pip install requests google-generativeai colorama")
    sys.exit(1)

PK_CROPS = [
    "wheat", "cotton", "rice", "sugarcane", "maize",
    "potato", "tomato", "mango", "onion", "chickpea",
]

PLANTWISEPLUS_URLS = {
    "wheat":     "https://www.plantwise.org/KnowledgeBank/Datasheet/51928",
    "cotton":    "https://www.plantwise.org/KnowledgeBank/Datasheet/15771",
    "rice":      "https://www.plantwise.org/KnowledgeBank/Datasheet/46529",
    "maize":     "https://www.plantwise.org/KnowledgeBank/Datasheet/33066",
    "potato":    "https://www.plantwise.org/KnowledgeBank/Datasheet/40597",
    "tomato":    "https://www.plantwise.org/KnowledgeBank/Datasheet/49492",
}

PARC_PDF_URLS = [
    "https://parc.gov.pk/publications/wheat-diseases",
    "https://aari.res.pk/publications",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Educational Research Bot for Agricultural Data)"
}

STRUCTURE_PROMPT = """
You are an agricultural data extraction expert. Extract ALL crop disease
information from the following web page text and return ONLY a valid JSON array.

Each item must have:
{{
  "crop_name_en": "crop name",
  "crop_name_ur": "",
  "disease_name_en": "disease name",
  "disease_name_ur": "",
  "pathogen_type": "Fungal|Bacterial|Viral|Insect Pest|Unknown",
  "symptoms_en": "symptoms description",
  "symptoms_ur": "",
  "affected_part": "affected plant parts",
  "season": "Rabi|Kharif|Both|Unknown",
  "region_pakistan": "Punjab|Sindh|KPK|Balochistan|All|Unknown",
  "climate_trigger": "climate conditions",
  "severity_level": "Critical|High|Medium|Low|Unknown",
  "spray_chemical_en": "chemical treatment",
  "brand_name_pakistan": "",
  "dose_per_acre": "",
  "spray_timing": "when to spray",
  "safety_precautions_ur": "",
  "biological_control": "resistant varieties or biocontrol",
  "economic_loss_pct": "",
  "data_source": "web: {url}",
  "verified_year": 2024,
  "country_code": "PK",
  "confidence": "Medium",
  "extraction_notes": "scraped from web — verify with local sources"
}}

If no disease info found, return empty array [].
Return ONLY JSON. No other text.

WEB PAGE TEXT:
{text}
"""


class WebScraper:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def fetch_page(self, url: str) -> str:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            from html.parser import HTMLParser

            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text_parts = []
                    self.skip_tags  = {"script","style","nav","footer","header"}
                    self.current_skip = 0
                def handle_starttag(self, tag, attrs):
                    if tag in self.skip_tags: self.current_skip += 1
                def handle_endtag(self, tag):
                    if tag in self.skip_tags: self.current_skip = max(0, self.current_skip-1)
                def handle_data(self, data):
                    if self.current_skip == 0:
                        text = data.strip()
                        if len(text) > 20:
                            self.text_parts.append(text)

            extractor = TextExtractor()
            extractor.feed(resp.text)
            return " ".join(extractor.text_parts)[:8000]
        except Exception as e:
            print(f"  {Fore.RED}Fetch failed: {e}{Style.RESET_ALL}")
            return ""

    def extract_from_text(self, text: str, url: str) -> list:
        if not text or len(text) < 200:
            return []
        prompt = STRUCTURE_PROMPT.format(text=text[:6000], url=url)
        try:
            resp = self.model.generate_content(prompt)
            raw  = resp.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"): raw = raw[4:]
            return json.loads(raw.strip())
        except Exception as e:
            print(f"  {Fore.YELLOW}Parse error: {e}{Style.RESET_ALL}")
            return []

    def scrape_crop(self, crop: str) -> list:
        print(f"\n{Fore.CYAN}Scraping disease data for: {crop.upper()}{Style.RESET_ALL}")
        all_records = []

        # Try PlantWisePlus
        if crop in PLANTWISEPLUS_URLS:
            url  = PLANTWISEPLUS_URLS[crop]
            print(f"  Fetching {url}...", end=" ", flush=True)
            text = self.fetch_page(url)
            recs = self.extract_from_text(text, url)
            print(f"{Fore.GREEN}+{len(recs)} records{Style.RESET_ALL}")
            all_records.extend(recs)
            time.sleep(2)

        return all_records

    def scrape_all(self) -> list:
        all_records = []
        for crop in PK_CROPS:
            recs = self.scrape_crop(crop)
            all_records.extend(recs)
        return all_records


def main():
    parser = argparse.ArgumentParser(description="Fasal Doctor Web Scraper")
    parser.add_argument("--crop",      help="Specific crop to scrape")
    parser.add_argument("--all-crops", action="store_true")
    parser.add_argument("--out",       default="data/processed/scraped.json")
    parser.add_argument("--append",    action="store_true")
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print(f"{Fore.RED}Set GEMINI_API_KEY first{Style.RESET_ALL}")
        sys.exit(1)

    scraper = WebScraper(api_key)
    records = []

    if args.all_crops:
        records = scraper.scrape_all()
    elif args.crop:
        records = scraper.scrape_crop(args.crop)
    else:
        parser.print_help()
        sys.exit(1)

    out_path = Path(args.out)
    existing = []
    if args.append and out_path.exists():
        with open(out_path) as f:
            existing = json.load(f)

    all_records = existing + records
    for i, r in enumerate(all_records, 1):
        r["id"] = f"PK-WEB-{i:03d}"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)

    print(f"\n{Fore.GREEN}Saved {len(all_records)} records → {out_path}{Style.RESET_ALL}")
    print(f"Run reviewer: python src/reviewer.py --input {out_path}")


if __name__ == "__main__":
    main()
