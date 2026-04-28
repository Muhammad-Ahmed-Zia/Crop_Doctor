"""
FASAL DOCTOR — Demo Extractor (No PDF needed)
===============================================
Simulates extraction from real PARC/AARI bulletin content.
Runs against sample text so you can test the full pipeline
without needing a PDF or API key.

Run: python src/demo_extractor.py
"""

import json, sys, os
from pathlib import Path

# -- Realistic sample text mimicking a PARC wheat disease bulletin --
SAMPLE_BULLETIN_TEXT = """
PAKISTAN AGRICULTURAL RESEARCH COUNCIL
Wheat Disease Management Bulletin 2024
Ayub Agricultural Research Institute, Faisalabad

WHEAT DISEASES OF PUNJAB — IDENTIFICATION AND CONTROL

1. YELLOW RUST (STRIPE RUST) — Puccinia striiformis

Yellow rust, locally known as Pili Kangi, is the most destructive wheat disease
in Pakistan. It appears as yellow to orange powdery stripes running parallel to
leaf veins on leaves and stems. In severe infections, entire leaves turn yellow
and the grain shrivels significantly.

The disease is favored by cool wet weather between 10-15 degrees Celsius with
relative humidity above 80%. Primary attacks occur during Rabi season
(November to March) mainly in Punjab and KPK regions.

Economic losses can reach 30-50% of total yield if left untreated.

Chemical Control:
Apply Propiconazole 25% EC (Tilt 250EC by Syngenta Pakistan) at 200ml per acre
dissolved in 100 liters of water. Alternatively, Tebuconazole 250 EW (Folicur
250EW by Bayer CropScience Pakistan) may be used. Apply at first sign of disease
and repeat after 14-21 days if conditions remain favorable.

SAFETY: Wear gloves and mask. Keep away from children. Wash hands thoroughly
after spraying. Do not spray near water bodies.

Biological Control: Plant resistant varieties such as Faisalabad-2008,
NARC-2011, or Pakistan-2013 which show moderate resistance to yellow rust.

2. BROWN RUST (LEAF RUST) — Puccinia recondita

Brown rust appears as round to oval orange-brown pustules scattered randomly
on the upper leaf surface. Unlike yellow rust, the pustules are darker and
distributed randomly rather than in stripes. Severe infection leads to
premature leaf death and reduced grain weight.

Favorable conditions: Warm humid weather between 15-22 degrees Celsius with
leaf wetness for more than 6 hours. Common in Punjab and Sindh during
February to April.

Yield losses of 20-40% reported in severely infected fields.

Treatment: Propiconazole 25% EC (Tilt 250EC, Syngenta) at 200ml per acre.
Also effective: Mancozeb 80% WP (Dithane M-45, Dow AgroSciences Pakistan)
at 600g per acre as preventive spray.

Resistant varieties: Seher-2006, Lasani-2008, Millat-2011.

3. LOOSE SMUT — Ustilago tritici

Loose smut is a seed-borne disease where entire grain is replaced by black
powdery mass of spores. Black smutted heads appear before healthy ears emerge.
Spores disperse at flowering and infect developing grains for next season.

The disease spreads through infected seed. All wheat growing regions of Pakistan
are affected.

Control: Mandatory seed treatment with Carboxin + Thiram (Vitavax 200FF by
Bayer Pakistan) at 2.5ml per kg of seed before every sowing. Also effective:
Tebuconazole 2DS (Raxil 2DS, Bayer) as dry seed dressing at 1.5g per kg seed.

Economic impact: 5-30% yield loss depending on severity of seed infection.

COTTON DISEASES — CCRI MULTAN ADVISORY

4. COTTON LEAF CURL VIRUS DISEASE (CLCuVD)

Cotton Leaf Curl Virus Disease, locally called Patta Murr Bimari, is the single
most devastating disease of cotton in Pakistan. Symptoms include upward or
downward curling of leaves, thickening of veins, and development of leaf-like
enations on undersides of leaves. Infected plants remain stunted and do not
produce bolls.

The disease is transmitted by whitefly (Bemisia tabaci). Hot dry conditions
favoring whitefly populations (30-40 degrees Celsius) lead to epidemic outbreaks.
All cotton growing areas of Punjab and Sindh are affected during Kharif season.

Losses can reach 40-70% and were near 100% during epidemic years in 1990s.

Management: Use CLCuD-resistant varieties — CIM-598, MNH-886, IUB-13. For
whitefly control apply Imidacloprid 70% WS (Gaucho 70WS, Bayer) as seed
treatment at 7g per kg seed. For foliar application use Thiamethoxam 25% WG
(Actara 25WG, Syngenta Pakistan) at 80g per acre.

CAUTION: Actara is highly toxic to honeybees. Do not apply during flowering.

5. AMERICAN BOLLWORM — Helicoverpa armigera

The American bollworm is the most economically important pest of cotton.
Larvae bore into flower buds (squares), flowers and bolls. Entry holes with
frass (excrement) are visible on damaged bolls. Infested bolls rot and fall
prematurely. Larvae are yellowish-green with dark stripes.

Peak attack during July to October in Punjab and Sindh. Temperature of
25-35 degrees Celsius with dry weather favors moth activity.

Spray: Chlorpyrifos 40% EC + Cypermethrin (Nurelle D, Syngenta Pakistan)
at 750ml per acre. Alternatively Spinosad 48% SC (Tracer 480SC, Dow/Corteva
Pakistan) at 80ml per acre. Rotate between chemical classes to prevent
resistance development.

WARNING: Chlorpyrifos is extremely toxic to fish and aquatic life. Never
spray near ponds, rivers or irrigation channels.

Biological control: Use Bt cotton varieties. Deploy pheromone traps at 1 per acre.
Natural enemies include Trichogramma parasitoids — release 50,000 per acre.
"""

def run_demo():
    print("\n" + "="*60)
    print("FASAL DOCTOR — Demo Extraction (No API Key Required)")
    print("="*60)
    print("\nSimulating Gemini API extraction from PARC bulletin text...")
    print("(In real use, this calls Gemini API on your actual PDF)\n")

    # Simulate what Gemini would return
    simulated_records = [
        {
            "id": "PK-001",
            "crop_name_en": "Wheat",
            "crop_name_ur": "گندم",
            "disease_name_en": "Yellow Rust (Stripe Rust)",
            "disease_name_ur": "پیلی کنگی",
            "pathogen_type": "Fungal",
            "symptoms_en": "Yellow to orange powdery stripes running parallel to leaf veins on leaves and stems. In severe infections, entire leaves turn yellow and grain shrivels.",
            "symptoms_ur": "پتوں اور تنوں پر پیلی نارنجی دھاریاں جو رگوں کے ساتھ ساتھ چلتی ہیں۔ شدید حملے میں پتے پیلے ہو جاتے ہیں اور دانہ سکڑ جاتا ہے۔",
            "affected_part": "Leaves, Stem",
            "season": "Rabi",
            "region_pakistan": "Punjab, KPK",
            "climate_trigger": "Cool wet weather 10-15°C, humidity >80%, November to March",
            "severity_level": "Critical",
            "spray_chemical_en": "Propiconazole 25% EC / Tebuconazole 250 EW",
            "brand_name_pakistan": "Tilt 250EC (Syngenta PK) / Folicur 250EW (Bayer PK)",
            "dose_per_acre": "200ml per acre in 100L water",
            "spray_timing": "At first sign of disease; repeat after 14-21 days",
            "safety_precautions_ur": "دستانے اور ماسک پہنیں۔ بچوں سے دور رکھیں۔ اسپرے کے بعد ہاتھ اچھی طرح دھوئیں۔",
            "biological_control": "Resistant varieties: Faisalabad-2008, NARC-2011, Pakistan-2013",
            "economic_loss_pct": "30-50%",
            "data_source": "AARI Faisalabad / PARC Bulletin 2024",
            "verified_year": 2024,
            "country_code": "PK",
            "confidence": "High",
            "extraction_notes": "Complete data found in bulletin",
            "source_file": "PARC_Wheat_Bulletin_2024.pdf",
            "chunk_pages": "1-4"
        },
        {
            "id": "PK-002",
            "crop_name_en": "Wheat",
            "crop_name_ur": "گندم",
            "disease_name_en": "Brown Rust (Leaf Rust)",
            "disease_name_ur": "بھوری کنگی",
            "pathogen_type": "Fungal",
            "symptoms_en": "Round to oval orange-brown pustules scattered randomly on upper leaf surface. Pustules are darker than yellow rust and distributed randomly. Premature leaf death and reduced grain weight.",
            "symptoms_ur": "پتوں کی اوپری سطح پر بکھرے ہوئے گول نارنجی بھورے دھبے۔ پیلی کنگی سے گہرے رنگ کے۔ پتے وقت سے پہلے سوکھتے اور دانہ ہلکا ہوتا ہے۔",
            "affected_part": "Leaves",
            "season": "Rabi",
            "region_pakistan": "Punjab, Sindh",
            "climate_trigger": "Warm humid 15-22°C, leaf wetness >6 hours, February to April",
            "severity_level": "High",
            "spray_chemical_en": "Propiconazole 25% EC / Mancozeb 80% WP",
            "brand_name_pakistan": "Tilt 250EC (Syngenta PK) / Dithane M-45 (Dow AgroSciences PK)",
            "dose_per_acre": "200ml Tilt OR 600g Dithane per acre",
            "spray_timing": "Preventive in high-risk areas; curative at first pustule appearance",
            "safety_precautions_ur": "حفاظتی لباس پہنیں۔ ہوا کے رخ کھڑے ہو کر اسپرے کریں۔",
            "biological_control": "Resistant varieties: Seher-2006, Lasani-2008, Millat-2011",
            "economic_loss_pct": "20-40%",
            "data_source": "AARI Faisalabad / PARC Bulletin 2024",
            "verified_year": 2024,
            "country_code": "PK",
            "confidence": "High",
            "extraction_notes": "Good data coverage",
            "source_file": "PARC_Wheat_Bulletin_2024.pdf",
            "chunk_pages": "1-4"
        },
        {
            "id": "PK-003",
            "crop_name_en": "Wheat",
            "crop_name_ur": "گندم",
            "disease_name_en": "Loose Smut",
            "disease_name_ur": "ڈھیلی سمٹ",
            "pathogen_type": "Fungal",
            "symptoms_en": "Entire grain replaced by black powdery spore mass. Black smutted heads emerge before healthy ears. Spores disperse at flowering infecting next season's seed.",
            "symptoms_ur": "پورا دانہ کالے پاؤڈر میں بدل جاتا ہے۔ صحتمند بالیوں سے پہلے کالی بالیاں نمودار ہوتی ہیں۔",
            "affected_part": "Seed, Spike",
            "season": "Rabi",
            "region_pakistan": "All",
            "climate_trigger": "Seed-borne disease; spreads through infected planting material",
            "severity_level": "Medium",
            "spray_chemical_en": "Carboxin + Thiram (seed treatment) / Tebuconazole 2DS",
            "brand_name_pakistan": "Vitavax 200FF (Bayer PK) / Raxil 2DS (Bayer PK)",
            "dose_per_acre": "Vitavax: 2.5ml per kg seed; Raxil: 1.5g per kg seed",
            "spray_timing": "Mandatory seed treatment before every sowing",
            "safety_precautions_ur": "بیج اسپرے کریں اور اچھی طرح سوکھنے دیں۔ بچوں کی پہنچ سے دور رکھیں۔",
            "biological_control": "Use certified disease-free seed every season",
            "economic_loss_pct": "5-30%",
            "data_source": "NARC / UAF Bulletin 2024",
            "verified_year": 2024,
            "country_code": "PK",
            "confidence": "High",
            "extraction_notes": "Seed treatment data complete",
            "source_file": "PARC_Wheat_Bulletin_2024.pdf",
            "chunk_pages": "5-8"
        },
        {
            "id": "PK-004",
            "crop_name_en": "Cotton",
            "crop_name_ur": "کپاس",
            "disease_name_en": "Cotton Leaf Curl Virus Disease (CLCuVD)",
            "disease_name_ur": "کپاس پتا مروڑ بیماری",
            "pathogen_type": "Viral",
            "symptoms_en": "Upward or downward curling of leaves, thickening of veins, leaf-like enations on leaf undersides. Infected plants remain stunted and fail to produce bolls.",
            "symptoms_ur": "پتے اوپر یا نیچے کی طرف مڑ جاتے ہیں، رگیں موٹی ہو جاتی ہیں، پتوں کی نیچے کی سطح پر ابھار پیدا ہوتے ہیں۔ پودا بونا رہتا ہے اور ٹنڈے نہیں بنتے۔",
            "affected_part": "Leaves, Whole Plant",
            "season": "Kharif",
            "region_pakistan": "Punjab, Sindh",
            "climate_trigger": "Hot dry conditions 30-40°C favoring whitefly vector (Bemisia tabaci)",
            "severity_level": "Critical",
            "spray_chemical_en": "Imidacloprid 70% WS (seed treatment) / Thiamethoxam 25% WG (foliar for whitefly)",
            "brand_name_pakistan": "Gaucho 70WS (Bayer PK) seed / Actara 25WG (Syngenta PK) foliar",
            "dose_per_acre": "Gaucho: 7g per kg seed; Actara: 80g per acre",
            "spray_timing": "Seed treatment mandatory; foliar at whitefly threshold (5 adults per leaf)",
            "safety_precautions_ur": "اکٹارا شہد کی مکھیوں کے لیے انتہائی نقصاندہ ہے۔ پھول آنے پر استعمال نہ کریں۔",
            "biological_control": "Resistant varieties: CIM-598, MNH-886, IUB-13. Remove infected plants early.",
            "economic_loss_pct": "40-70% (near 100% in epidemic years)",
            "data_source": "CCRI Multan Advisory 2024",
            "verified_year": 2024,
            "country_code": "PK",
            "confidence": "High",
            "extraction_notes": "Complete viral disease record",
            "source_file": "CCRI_Cotton_Advisory_2024.pdf",
            "chunk_pages": "9-12"
        },
        {
            "id": "PK-005",
            "crop_name_en": "Cotton",
            "crop_name_ur": "کپاس",
            "disease_name_en": "American Bollworm",
            "disease_name_ur": "امریکی سنڈی",
            "pathogen_type": "Insect Pest",
            "symptoms_en": "Larvae bore into flower buds, flowers, and bolls. Entry holes with frass visible on damaged bolls. Infested bolls rot and fall prematurely. Larvae are yellowish-green with dark stripes.",
            "symptoms_ur": "لاروا پھولوں کی کلیوں، پھولوں اور ٹنڈوں میں سوراخ کرتا ہے۔ متاثرہ ٹنڈوں پر سوراخ اور گوبر نظر آتا ہے۔ ٹنڈے سڑ کر گر جاتے ہیں۔",
            "affected_part": "Fruit, Flower",
            "season": "Kharif",
            "region_pakistan": "Punjab, Sindh",
            "climate_trigger": "Hot dry conditions 25-35°C, July to October peak",
            "severity_level": "Critical",
            "spray_chemical_en": "Chlorpyrifos 40% EC + Cypermethrin / Spinosad 48% SC",
            "brand_name_pakistan": "Nurelle D (Syngenta PK) / Tracer 480SC (Dow/Corteva PK)",
            "dose_per_acre": "Nurelle D: 750ml per acre; Tracer: 80ml per acre",
            "spray_timing": "Apply at 5-10% infestation; rotate chemical classes to prevent resistance",
            "safety_precautions_ur": "کلورپائریفوس مچھلیوں اور آبی حیات کے لیے انتہائی خطرناک ہے۔ نہروں اور تالابوں کے قریب ہرگز نہ چھڑکیں۔",
            "biological_control": "Bt cotton varieties. Pheromone traps 1 per acre. Trichogramma parasitoid release 50,000 per acre.",
            "economic_loss_pct": "30-60%",
            "data_source": "CCRI Multan Advisory 2024",
            "verified_year": 2024,
            "country_code": "PK",
            "confidence": "High",
            "extraction_notes": "Complete pest record with biological control options",
            "source_file": "CCRI_Cotton_Advisory_2024.pdf",
            "chunk_pages": "13-16"
        },
    ]

    # Save output
    out_path = Path("data/processed/extracted.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(simulated_records, f, ensure_ascii=False, indent=2)

    print(f"✓ Extracted {len(simulated_records)} disease records")
    print(f"✓ Saved to {out_path}")
    print(f"\nCrops covered: Wheat (3 diseases), Cotton (2 diseases)")
    print(f"All records include: Urdu names, Pakistan brands, dosages, safety info")
    print(f"\nNext steps:")
    print(f"  python src/reviewer.py --input data/processed/extracted.json")
    print(f"  python src/reviewer.py --input data/processed/extracted.json --export")
    print(f"\nWith real PDFs:")
    print(f"  export GEMINI_API_KEY='your_key'")
    print(f"  python src/pdf_extractor.py --folder data/raw/ --append")

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    run_demo()
