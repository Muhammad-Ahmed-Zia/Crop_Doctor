"""
FASAL DOCTOR — Urdu Enricher
==============================
Takes extracted records with empty Urdu fields and fills them
using Gemini API translation. Also adds common Pakistani spray
brand names by matching active ingredients.

Usage:
    python src/urdu_enricher.py --input data/processed/extracted.json
"""

import os, sys, json, time, argparse
from pathlib import Path
from dotenv import load_dotenv
from colorama import Fore, Style, init

from google import genai

init(autoreset=True)

# Known Pakistan spray brands indexed by active ingredient keyword
PAKISTAN_BRANDS = {
    "propiconazole":    "Tilt 250EC (Syngenta PK) / Orbit 250EC (Dow PK)",
    "tebuconazole":     "Folicur 250EW (Bayer PK) / Raxil 2DS (Bayer PK)",
    "mancozeb":         "Dithane M-45 (Corteva PK) / Penncozeb (UPL PK)",
    "carbendazim":      "Bavistin 50WP (BASF PK) / Derosal 500SC",
    "metalaxyl":        "Ridomil Gold MZ (Syngenta PK)",
    "chlorothalonil":   "Bravo 500SC (Syngenta PK) / Daconil (SDS)",
    "imidacloprid":     "Confidor 200SL (Bayer PK) / Gaucho 70WS (Bayer PK)",
    "thiamethoxam":     "Actara 25WG (Syngenta PK) / Cruiser (Syngenta PK)",
    "chlorpyrifos":     "Dursban 40EC (Dow/Corteva PK) / Lorsban 40EC",
    "cypermethrin":     "Ripcord 10EC (Syngenta PK) / Cymbush 10EC (FMC PK)",
    "spinosad":         "Tracer 480SC (Dow/Corteva PK)",
    "copper oxychloride":"Kocide 101 (FMC PK) / Cupravit (Bayer PK)",
    "tricyclazole":     "Beam 75WP (Corteva PK) / Trizole 75WP",
    "isoprothiolane":   "Fuji-One 40EC (Nihon Nohyaku / local PK distributors)",
    "cartap":           "Padan 50SP (Syngenta PK)",
    "sulphur":          "Kumulus DF (BASF PK) / Microthiol Special (UPL PK)",
    "abamectin":        "Vertimec 1.8EC (Syngenta PK) / Agri-Mek (Viqar Agri)",
    "emamectin":        "Proclaim 5SG (Syngenta PK)",
    "acetamiprid":      "Mospilan 20SP (Nippon Soda / Agritech PK)",
    "lambda-cyhalothrin":"Karate Zeon (Syngenta PK) / Icon 10CS (Syngenta PK)",
}

URDU_CROPS = {
    "wheat":"گندم","cotton":"کپاس","rice":"چاول","sugarcane":"گنا",
    "maize":"مکئی","corn":"مکئی","potato":"آلو","tomato":"ٹماٹر",
    "mango":"آم","onion":"پیاز","chickpea":"چنا","lentil":"مسور",
    "mustard":"سرسوں","sunflower":"سورج مکھی","soybean":"سویا بین",
    "groundnut":"مونگ پھلی","banana":"کیلا","citrus":"لیموں",
    "apple":"سیب","grape":"انگور","cauliflower":"گوبھی","spinach":"پالک",
}

TRANSLATE_PROMPT = """
You are an expert agricultural translator for Pakistani farmers.
Translate the following English disease information to Urdu.
Return ONLY a JSON object with these exact fields — no other text:
{{
  "disease_name_ur": "Urdu translation of the disease name",
  "symptoms_ur": "Urdu translation of the symptoms (2-3 sentences, simple language for farmers)",
  "safety_precautions_ur": "Urdu safety warnings for the spray (1-2 sentences)"
}}

Rules:
- Use simple Urdu that an uneducated farmer can understand
- Keep technical terms like spray names in English within the Urdu text
- For disease names, use common Urdu agricultural terms if they exist

Disease name: {disease_name}
Crop: {crop_name}
Symptoms: {symptoms}
Spray: {spray}
"""

def lookup_brands(spray_text: str) -> str:
    spray_lower = spray_text.lower()
    found = []
    for ingredient, brand in PAKISTAN_BRANDS.items():
        if ingredient in spray_lower:
            found.append(brand)
    return " / ".join(found) if found else ""

def enrich_urdu(rec: dict, client, model: str) -> dict:
    # Fill crop Urdu name from lookup table
    if not rec.get("crop_name_ur"):
        crop_lower = rec.get("crop_name_en", "").lower()
        rec["crop_name_ur"] = URDU_CROPS.get(crop_lower, "")

    # Fill brand names from ingredient lookup
    if not rec.get("brand_name_pakistan") and rec.get("spray_chemical_en"):
        brand = lookup_brands(rec["spray_chemical_en"])
        if brand:
            rec["brand_name_pakistan"] = brand

    # Use Gemini to translate disease name, symptoms, safety
    needs_translation = (
        not rec.get("disease_name_ur") or
        not rec.get("symptoms_ur") or
        not rec.get("safety_precautions_ur")
    )
    # Only call API if symptoms are meaningful (not just 'Consult agronomist')
    symptoms = rec.get("symptoms_en", "")
    junk = {"not specified", "not mentioned", "consult agronomist", "n/a", ""}
    symptoms_useful = symptoms and symptoms.lower().strip() not in junk

    if needs_translation and rec.get("disease_name_en") and symptoms_useful:
        prompt = TRANSLATE_PROMPT.format(
            disease_name = rec.get("disease_name_en", ""),
            crop_name    = rec.get("crop_name_en", ""),
            symptoms     = symptoms,
            spray        = rec.get("spray_chemical_en", ""),
        )
        for attempt in range(3):
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                raw = resp.text.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"): raw = raw[4:]
                raw = raw.strip()
                translated = json.loads(raw)
                if not rec.get("disease_name_ur"):
                    rec["disease_name_ur"] = translated.get("disease_name_ur", "")
                if not rec.get("symptoms_ur"):
                    rec["symptoms_ur"] = translated.get("symptoms_ur", "")
                if not rec.get("safety_precautions_ur"):
                    rec["safety_precautions_ur"] = translated.get("safety_precautions_ur", "")
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(3)
    return rec


def main():
    parser = argparse.ArgumentParser(description="Fasal Doctor Urdu Enricher")
    parser.add_argument("--input",  required=True)
    parser.add_argument("--out",    default="")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print(f"{Fore.RED}Set GEMINI_API_KEY first{Style.RESET_ALL}")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    model = "gemini-2.0-flash"

    with open(args.input, encoding="utf-8") as f:
        records = json.load(f)

    print(f"\n{Fore.CYAN}Enriching {len(records)} records with Urdu + Pakistan brands...{Style.RESET_ALL}")
    skipped = 0

    for i, rec in enumerate(records):
        disease_short = (rec.get('disease_name_en') or '?')[:35]
        print(f"  [{i+1}/{len(records)}] {rec.get('crop_name_en','?'):<12} — {disease_short:<35}", end=" ", flush=True)
        records[i] = enrich_urdu(rec, client, model)
        print(f"{Fore.GREEN}done{Style.RESET_ALL}")
        time.sleep(0.6)   # stay within free-tier rate limits

    out_path = args.out or args.input
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"\n{Fore.GREEN}✓ Saved enriched records → {out_path}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✓ Total records: {len(records)}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
