"""
FASAL DOCTOR — Add Crops Script (TASK 1)
========================================
Adds missing important Pakistan crops to the dataset:
Potato, Tomato, Mango, Onion, Chickpea.
"""

import json
import os
import subprocess
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

MASTER_JSON = "data/processed/master_dataset.json"

NEW_RECORDS = [
    # --- POTATO (آلو) ---
    {
        "crop_name_en": "Potato", "crop_name_ur": "آلو",
        "disease_name_en": "Late Blight", "disease_name_ur": "لیٹ بلائٹ (پچھیتا جھلساؤ)",
        "pathogen_type": "Fungus (Oomycete)",
        "symptoms_en": "Water-soaked spots on leaves turning brown/black with white fuzzy growth on undersides. Rapid wilting.",
        "symptoms_ur": "پتوں پر پانی بھرے دھبے جو بھورے/کالے ہو جاتے ہیں۔ پتوں کے نیچے سفید پھپھوندی۔",
        "affected_part": "Leaves, Stem, Tubers", "season": "Winter/Spring",
        "region_pakistan": "Punjab, KP", "climate_trigger": "Cool and wet/humid (Rainy, Foggy)",
        "severity_level": "Critical",
        "spray_chemical_en": "Mancozeb + Metalaxyl", "brand_name_pakistan": "Ridomil Gold MZ (Syngenta PK)",
        "dose_per_acre": "1000g / acre", "spray_timing": "At first sign of disease, repeat after 7-10 days",
        "safety_precautions_ur": "ماسک اور دستانے پہنیں۔ سپرے کے بعد 7 دن تک فصل استعمال نہ کریں۔ ہوا کے مخالف سپرے نہ کریں۔",
        "biological_control": "Plant resistant varieties. Ensure good drainage.",
        "economic_loss_pct": "Up to 100%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Potato", "crop_name_ur": "آلو",
        "disease_name_en": "Early Blight", "disease_name_ur": "ارلی بلائٹ (اگیتا جھلساؤ)",
        "pathogen_type": "Fungus",
        "symptoms_en": "Dark brown to black spots with concentric rings (target board pattern) on older leaves.",
        "symptoms_ur": "پرانے پتوں پر گہرے بھورے یا کالے دھبے جن میں دائرے (ٹارگٹ بورڈ کی طرح) ہوتے ہیں۔",
        "affected_part": "Leaves", "season": "Winter/Spring",
        "region_pakistan": "Punjab, KP, Balochistan", "climate_trigger": "Warm and humid",
        "severity_level": "High",
        "spray_chemical_en": "Mancozeb", "brand_name_pakistan": "Dithane M-45 (Corteva PK)",
        "dose_per_acre": "1000g / acre", "spray_timing": "Preventative or at early symptoms",
        "safety_precautions_ur": "سپرے کے وقت حفاظتی لباس پہنیں۔ بچوں کو دور رکھیں۔",
        "biological_control": "Crop rotation, remove infected debris.",
        "economic_loss_pct": "20-50%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Potato", "crop_name_ur": "آلو",
        "disease_name_en": "Black Scurf", "disease_name_ur": "بلیک سکرَف",
        "pathogen_type": "Fungus",
        "symptoms_en": "Hard, black resting bodies (sclerotia) on tubers that look like dirt but won't wash off.",
        "symptoms_ur": "آلو پر کالے، سخت دھبے جو مٹی کی طرح لگتے ہیں لیکن دھونے سے صاف نہیں ہوتے۔",
        "affected_part": "Tubers, Roots", "season": "Winter/Spring",
        "region_pakistan": "Punjab, KP", "climate_trigger": "Cool, wet soils",
        "severity_level": "Medium",
        "spray_chemical_en": "Pencycuron", "brand_name_pakistan": "Monceren 250FS (Bayer PK)",
        "dose_per_acre": "Seed treatment: 250ml / 100kg seed", "spray_timing": "Before planting (Seed treatment)",
        "safety_precautions_ur": "بیج کو زہر لگاتے وقت دستانے ضرور پہنیں۔ زہر لگا بیج جانوروں کو نہ کھلائیں۔",
        "biological_control": "Use healthy, certified seeds. Late planting in warmer soils.",
        "economic_loss_pct": "10-30%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Potato", "crop_name_ur": "آلو",
        "disease_name_en": "Common Scab", "disease_name_ur": "کامن سکیب (کھرنڈ)",
        "pathogen_type": "Bacteria",
        "symptoms_en": "Cork-like, raised or sunken lesions on the skin of tubers.",
        "symptoms_ur": "آلو کی جلد پر کھردرے، ابھرے ہوئے یا دھنسے ہوئے دھبے (کھرنڈ)۔",
        "affected_part": "Tubers", "season": "Winter",
        "region_pakistan": "Punjab, Sindh", "climate_trigger": "Dry, alkaline soils",
        "severity_level": "Medium",
        "spray_chemical_en": "Not applicable (Soil/Seed borne)", "brand_name_pakistan": "None",
        "dose_per_acre": "N/A", "spray_timing": "N/A",
        "safety_precautions_ur": "پانی کی مناسب مقدار دیں۔",
        "biological_control": "Lower soil pH. Maintain adequate soil moisture during tuber formation.",
        "economic_loss_pct": "10-40% (mostly quality loss)", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Potato", "crop_name_ur": "آلو",
        "disease_name_en": "Viral Mosaic", "disease_name_ur": "وائرل موزیک",
        "pathogen_type": "Virus",
        "symptoms_en": "Mottling, yellowing, and wrinkling of leaves. Stunted plant growth.",
        "symptoms_ur": "پتوں پر پیلے اور ہرے دھبے، پتوں کا مڑنا اور پودے کا چھوٹا رہ جانا۔",
        "affected_part": "Leaves, Whole Plant", "season": "All Seasons",
        "region_pakistan": "All Regions", "climate_trigger": "High aphid population",
        "severity_level": "High",
        "spray_chemical_en": "Imidacloprid (for Aphid control)", "brand_name_pakistan": "Confidor (Bayer PK)",
        "dose_per_acre": "250ml / acre", "spray_timing": "At first sight of aphids",
        "safety_precautions_ur": "وائرس کا کوئی علاج نہیں، صرف رس چوسنے والے کیڑوں کو ماریں۔",
        "biological_control": "Use certified virus-free seed. Remove infected plants.",
        "economic_loss_pct": "30-60%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Potato", "crop_name_ur": "آلو",
        "disease_name_en": "Root Rot", "disease_name_ur": "جڑ کا سڑنا (روٹ روٹ)",
        "pathogen_type": "Fungus",
        "symptoms_en": "Yellowing of leaves, wilting, and decaying brown roots.",
        "symptoms_ur": "پتوں کا پیلا ہونا، پودے کا مرجھانا اور جڑوں کا بھورا ہو کر گلنا۔",
        "affected_part": "Roots, Base Stem", "season": "Spring",
        "region_pakistan": "Punjab", "climate_trigger": "Over-watering, poor drainage",
        "severity_level": "High",
        "spray_chemical_en": "Thiophanate Methyl", "brand_name_pakistan": "Topsin-M 70WP",
        "dose_per_acre": "400g / acre (Drenching)", "spray_timing": "Early stages of disease",
        "safety_precautions_ur": "کھیت میں پانی کھڑا نہ ہونے دیں۔",
        "biological_control": "Improve drainage, Trichoderma application.",
        "economic_loss_pct": "20-50%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },

    # --- TOMATO (ٹماٹر) ---
    {
        "crop_name_en": "Tomato", "crop_name_ur": "ٹماٹر",
        "disease_name_en": "Early Blight", "disease_name_ur": "ارلی بلائٹ (اگیتا جھلساؤ)",
        "pathogen_type": "Fungus",
        "symptoms_en": "Brown spots with concentric rings on lower leaves, stems, and fruit.",
        "symptoms_ur": "نچلے پتوں اور پھل پر گول دائروں والے بھورے دھبے۔",
        "affected_part": "Leaves, Fruit, Stem", "season": "Spring/Summer",
        "region_pakistan": "Punjab, Sindh", "climate_trigger": "Warm, humid, rainy",
        "severity_level": "High",
        "spray_chemical_en": "Chlorothalonil", "brand_name_pakistan": "Bravo 500SC (Syngenta PK)",
        "dose_per_acre": "500ml / acre", "spray_timing": "Preventative or at early symptoms",
        "safety_precautions_ur": "سپرے کے 3 دن بعد تک ٹماٹر نہ توڑیں۔",
        "biological_control": "Mulching, bottom watering, remove affected leaves.",
        "economic_loss_pct": "30-50%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Tomato", "crop_name_ur": "ٹماٹر",
        "disease_name_en": "Late Blight", "disease_name_ur": "لیٹ بلائٹ",
        "pathogen_type": "Fungus (Oomycete)",
        "symptoms_en": "Irregular greasy, water-soaked patches on leaves. Fruits show rough, firm brown spots.",
        "symptoms_ur": "پتوں پر پانی بھرے دھبے اور پھل پر سخت بھورے دھبے۔",
        "affected_part": "Leaves, Fruit", "season": "Winter/Spring",
        "region_pakistan": "Punjab, KP", "climate_trigger": "Cool and wet",
        "severity_level": "Critical",
        "spray_chemical_en": "Mancozeb", "brand_name_pakistan": "Dithane M-45",
        "dose_per_acre": "1000g / acre", "spray_timing": "Immediate on symptom appearance",
        "safety_precautions_ur": "فوری سپرے کریں، بیماری تیزی سے پھیلتی ہے۔ ماسک پہنیں۔",
        "biological_control": "Keep foliage dry, proper spacing.",
        "economic_loss_pct": "Up to 100%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Tomato", "crop_name_ur": "ٹماٹر",
        "disease_name_en": "Leaf Curl", "disease_name_ur": "پتہ مروڑ وائرس (لیف کرل)",
        "pathogen_type": "Virus",
        "symptoms_en": "Upward curling, puckering, and yellowing of leaves. Stunted plant.",
        "symptoms_ur": "پتوں کا اوپر کی طرف مڑنا، پیلا ہونا اور پودے کا قد چھوٹا رہ جانا۔",
        "affected_part": "Leaves", "season": "Summer/Autumn",
        "region_pakistan": "Punjab, Sindh", "climate_trigger": "High Whitefly population",
        "severity_level": "Critical",
        "spray_chemical_en": "Pyriproxyfen (for Whitefly)", "brand_name_pakistan": "Priority (Bayer PK)",
        "dose_per_acre": "500ml / acre", "spray_timing": "At first sight of whitefly",
        "safety_precautions_ur": "وائرس زدہ پودے اکھاڑ کر دبا دیں۔ سفید مکھی کا سپرے کریں۔",
        "biological_control": "Yellow sticky traps, disease-resistant varieties.",
        "economic_loss_pct": "50-90%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Tomato", "crop_name_ur": "ٹماٹر",
        "disease_name_en": "Fusarium Wilt", "disease_name_ur": "فیوزیریم ولٹ (مرجھاؤ)",
        "pathogen_type": "Fungus",
        "symptoms_en": "Yellowing and wilting of leaves often starting on one side of the plant. Brown vascular tissue inside stem.",
        "symptoms_ur": "پودے کے ایک طرف کے پتوں کا پیلا ہو کر مرجھانا۔ تنے کے اندر سے بھورا ہونا۔",
        "affected_part": "Roots, Stem, Whole Plant", "season": "Spring/Summer",
        "region_pakistan": "Punjab", "climate_trigger": "Warm soils",
        "severity_level": "High",
        "spray_chemical_en": "Carbendazim", "brand_name_pakistan": "Bavistin 50WP (BASF PK)",
        "dose_per_acre": "400g / acre (Drenching)", "spray_timing": "At early wilting",
        "safety_precautions_ur": "متاثرہ کھیت میں اگلے سال ٹماٹر نہ لگائیں۔",
        "biological_control": "Crop rotation, resistant varieties.",
        "economic_loss_pct": "30-70%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Tomato", "crop_name_ur": "ٹماٹر",
        "disease_name_en": "Bacterial Spot", "disease_name_ur": "بیکٹیریل سپاٹ",
        "pathogen_type": "Bacteria",
        "symptoms_en": "Small, dark, water-soaked spots on leaves and scabby spots on fruit.",
        "symptoms_ur": "پتوں پر چھوٹے گہرے پانی بھرے دھبے اور پھل پر کھردرے نشان۔",
        "affected_part": "Leaves, Fruit", "season": "Summer",
        "region_pakistan": "Punjab", "climate_trigger": "High humidity, heavy rain",
        "severity_level": "Medium",
        "spray_chemical_en": "Copper Oxychloride", "brand_name_pakistan": "Cobox (BASF PK)",
        "dose_per_acre": "500g / acre", "spray_timing": "Preventative before rain",
        "safety_precautions_ur": "تانبے والے سپرے گرمی میں احتیاط سے کریں۔",
        "biological_control": "Avoid overhead watering.",
        "economic_loss_pct": "10-30%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Tomato", "crop_name_ur": "ٹماٹر",
        "disease_name_en": "Blossom End Rot", "disease_name_ur": "بلاسَم اینڈ روٹ",
        "pathogen_type": "Physiological (Calcium deficiency)",
        "symptoms_en": "Dark, sunken, leathery spots at the bottom (blossom end) of the fruit.",
        "symptoms_ur": "ٹماٹر کے نچلے حصے پر کالا، دھنسا ہوا اور سخت دھبہ۔",
        "affected_part": "Fruit", "season": "Summer",
        "region_pakistan": "All Regions", "climate_trigger": "Fluctuating watering, drought",
        "severity_level": "Medium",
        "spray_chemical_en": "Calcium Foliar Spray", "brand_name_pakistan": "Any good liquid Calcium",
        "dose_per_acre": "As per product label", "spray_timing": "When fruits begin to form",
        "safety_precautions_ur": "پانی باقاعدگی سے دیں، مٹی کو زیادہ خشک یا گیلا نہ ہونے دیں۔",
        "biological_control": "Consistent watering, maintain soil pH.",
        "economic_loss_pct": "10-20%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },

    # --- MANGO (آم) ---
    {
        "crop_name_en": "Mango", "crop_name_ur": "آم",
        "disease_name_en": "Anthracnose", "disease_name_ur": "انتھراکنوز (پتوں اور پھل کے دھبے)",
        "pathogen_type": "Fungus",
        "symptoms_en": "Dark brown to black irregular spots on leaves, blossoms, and fruit. Fruit rots after ripening.",
        "symptoms_ur": "پتوں، پھولوں اور پھل پر گہرے کالے/بھورے بے قاعدہ دھبے۔ پھل پکنے پر گلنے لگتا ہے۔",
        "affected_part": "Leaves, Fruit, Flowers", "season": "Spring/Summer",
        "region_pakistan": "Punjab (Multan), Sindh", "climate_trigger": "Humid, misty weather",
        "severity_level": "High",
        "spray_chemical_en": "Difenoconazole", "brand_name_pakistan": "Score 250EC (Syngenta PK)",
        "dose_per_acre": "100ml / 100 liters water", "spray_timing": "Before flowering and at fruit setting",
        "safety_precautions_ur": "درختوں کی کانٹ چھانٹ کریں تاکہ ہوا گزر سکے۔ سپرے کے وقت دستانے پہنیں۔",
        "biological_control": "Pruning for air circulation.",
        "economic_loss_pct": "30-60%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Mango", "crop_name_ur": "آم",
        "disease_name_en": "Powdery Mildew", "disease_name_ur": "پاؤڈری ملڈیو (سفید سفوفی بیماری)",
        "pathogen_type": "Fungus",
        "symptoms_en": "White powdery coating on flowers, young leaves, and very young fruit. Causes flower drop.",
        "symptoms_ur": "پھولوں (بور) اور نئے پتوں پر سفید پاؤڈر نما تہہ۔ بور کا گرنا۔",
        "affected_part": "Flowers, Leaves", "season": "Spring (Feb-March)",
        "region_pakistan": "Punjab, Sindh", "climate_trigger": "Cool nights, warm dry days",
        "severity_level": "Critical",
        "spray_chemical_en": "Myclobutanil", "brand_name_pakistan": "Systhane (Corteva PK)",
        "dose_per_acre": "100ml / 100 liters water", "spray_timing": "At panicle emergence (بور نکلنے پر)",
        "safety_precautions_ur": "بور نکلتے وقت احتیاطی سپرے لازمی کریں۔",
        "biological_control": "Neem oil spray early.",
        "economic_loss_pct": "Up to 80%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Mango", "crop_name_ur": "آم",
        "disease_name_en": "Malformation", "disease_name_ur": "مینگو مالفارمیشن (بور کا گچھا بننا)",
        "pathogen_type": "Fungus (Fusarium)",
        "symptoms_en": "Flowers form compact, sterile bunches instead of normal panicles. Vegetative shoots become bunched.",
        "symptoms_ur": "پھولوں (بور) کا نارمل ہونے کی بجائے گچھا بن جانا۔ اس پر پھل نہیں لگتا۔",
        "affected_part": "Flowers, Shoots", "season": "Spring",
        "region_pakistan": "Punjab", "climate_trigger": "Cool temperatures during floral bud development",
        "severity_level": "High",
        "spray_chemical_en": "NAA (Plant Growth Regulator)", "brand_name_pakistan": "Planofix (Bayer PK)",
        "dose_per_acre": "As per label", "spray_timing": "Oct-Nov",
        "safety_precautions_ur": "متاثرہ بور کو کاٹ کر جلا دیں۔",
        "biological_control": "Prune and destroy affected panicles.",
        "economic_loss_pct": "20-50%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Mango", "crop_name_ur": "آم",
        "disease_name_en": "Bacterial Canker", "disease_name_ur": "بیکٹیریل کینکر",
        "pathogen_type": "Bacteria",
        "symptoms_en": "Raised, rough, dark brown to black lesions on fruit, stems, and leaves with cracking.",
        "symptoms_ur": "پھل، تنوں اور پتوں پر ابھرے ہوئے کھردرے کالے دھبے اور دراڑیں۔",
        "affected_part": "Fruit, Stem, Leaves", "season": "Summer",
        "region_pakistan": "Sindh, Punjab", "climate_trigger": "High wind and rain",
        "severity_level": "Medium",
        "spray_chemical_en": "Copper Oxychloride + Kasugamycin", "brand_name_pakistan": "Kasumin / Cobox",
        "dose_per_acre": "300g / 100 liters water", "spray_timing": "After pruning or storm damage",
        "safety_precautions_ur": "تیز ہواؤں کے بعد حفاظتی سپرے کریں۔",
        "biological_control": "Windbreaks, clean tools.",
        "economic_loss_pct": "10-20%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Mango", "crop_name_ur": "آم",
        "disease_name_en": "Sooty Mold", "disease_name_ur": "سوٹی مولڈ (کالی پھپھوندی)",
        "pathogen_type": "Fungus",
        "symptoms_en": "Black soot-like covering on leaves and fruit, developing on honeydew from insects.",
        "symptoms_ur": "پتوں اور پھل پر کالے دھویں یا راکھ جیسی تہہ (تیلے کی وجہ سے)۔",
        "affected_part": "Leaves, Fruit", "season": "Summer",
        "region_pakistan": "All Regions", "climate_trigger": "High hopper/mealybug infestation",
        "severity_level": "Medium",
        "spray_chemical_en": "Insecticide (Imidacloprid) + Fungicide", "brand_name_pakistan": "Confidor + any basic fungicide",
        "dose_per_acre": "Target insects first", "spray_timing": "When hoppers are seen",
        "safety_precautions_ur": "رس چوسنے والے کیڑوں کا خاتمہ کریں تاکہ یہ بیماری نہ پھیلے۔",
        "biological_control": "Control insect vectors.",
        "economic_loss_pct": "10-15%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },

    # --- ONION (پیاز) ---
    {
        "crop_name_en": "Onion", "crop_name_ur": "پیاز",
        "disease_name_en": "Purple Blotch", "disease_name_ur": "پرپل بلاچ (جامنی دھبے)",
        "pathogen_type": "Fungus",
        "symptoms_en": "Small whitish, sunken spots that turn purple/brown with yellow halos on leaves.",
        "symptoms_ur": "پتوں پر سفید دھنسے ہوئے دھبے جو بعد میں جامنی یا بھورے ہو جاتے ہیں، جن کے گرد پیلا حلقہ ہوتا ہے۔",
        "affected_part": "Leaves", "season": "Winter/Spring",
        "region_pakistan": "Sindh, Punjab", "climate_trigger": "High humidity, warm weather",
        "severity_level": "High",
        "spray_chemical_en": "Iprodione", "brand_name_pakistan": "Rovral 50WP (Bayer PK)",
        "dose_per_acre": "500g / acre", "spray_timing": "Early symptom appearance",
        "safety_precautions_ur": "کھیت میں جڑی بوٹیاں ختم کریں۔",
        "biological_control": "Crop rotation, avoid dense planting.",
        "economic_loss_pct": "20-50%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Onion", "crop_name_ur": "پیاز",
        "disease_name_en": "Stemphylium Blight", "disease_name_ur": "اسٹیمفائلیم بلائٹ",
        "pathogen_type": "Fungus",
        "symptoms_en": "Light yellow/brown streaks on leaves that darken and coalesce. Leaves die back from tips.",
        "symptoms_ur": "پتوں پر پیلی/بھوری دھاریاں جو کالی ہو جاتی ہیں۔ پتے اوپر سے سوکھنا شروع ہوتے ہیں۔",
        "affected_part": "Leaves", "season": "Winter/Spring",
        "region_pakistan": "Sindh, Punjab", "climate_trigger": "Humid and warm",
        "severity_level": "High",
        "spray_chemical_en": "Mancozeb", "brand_name_pakistan": "Dithane M-45",
        "dose_per_acre": "1000g / acre", "spray_timing": "Preventative or at early symptoms",
        "safety_precautions_ur": "سپرے میں گوند (Sticker) ملا کر استعمال کریں۔",
        "biological_control": "Clean seeds, remove plant debris.",
        "economic_loss_pct": "30-50%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Onion", "crop_name_ur": "پیاز",
        "disease_name_en": "Basal Rot", "disease_name_ur": "بیسل روٹ (جڑ کا گلنا)",
        "pathogen_type": "Fungus (Fusarium)",
        "symptoms_en": "Yellowing of leaves, dying from tips downwards. Roots rot and basal plate turns brown/pink.",
        "symptoms_ur": "پتوں کا اوپر سے پیلا ہو کر سوکھنا۔ پیاز کا نچلا حصہ (جڑ) بھورا یا گلابی ہو کر گل جاتا ہے۔",
        "affected_part": "Roots, Bulb", "season": "Summer",
        "region_pakistan": "All Regions", "climate_trigger": "Warm soils, root injury",
        "severity_level": "Medium",
        "spray_chemical_en": "Carbendazim (Seed/Seedling treatment)", "brand_name_pakistan": "Bavistin 50WP",
        "dose_per_acre": "Dipping seedlings before transplanting", "spray_timing": "At transplanting",
        "safety_precautions_ur": "پنیری منتقل کرتے وقت جڑوں کو زہر والے پانی میں ڈبوئیں۔",
        "biological_control": "Crop rotation (no onions for 3-4 years).",
        "economic_loss_pct": "10-30%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Onion", "crop_name_ur": "پیاز",
        "disease_name_en": "Downy Mildew", "disease_name_ur": "ڈاؤنی ملڈیو (پھپھوندی)",
        "pathogen_type": "Fungus (Oomycete)",
        "symptoms_en": "Pale green/yellow oval spots on leaves. Grey-purple fuzz appears in high humidity.",
        "symptoms_ur": "پتوں پر ہلکے سبز یا پیلے دھبے۔ نمی میں ان پر خاکستری/جامنی پھپھوندی لگ جاتی ہے۔",
        "affected_part": "Leaves", "season": "Winter",
        "region_pakistan": "KP, Punjab", "climate_trigger": "Cool, wet, humid",
        "severity_level": "High",
        "spray_chemical_en": "Metalaxyl + Mancozeb", "brand_name_pakistan": "Ridomil Gold MZ",
        "dose_per_acre": "1000g / acre", "spray_timing": "At first sign of disease",
        "safety_precautions_ur": "صبح سویرے اوس کے وقت سپرے نہ کریں۔",
        "biological_control": "Wider spacing for ventilation.",
        "economic_loss_pct": "20-40%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },

    # --- CHICKPEA (چنا) ---
    {
        "crop_name_en": "Chickpea", "crop_name_ur": "چنا",
        "disease_name_en": "Ascochyta Blight", "disease_name_ur": "اسکوکائٹا بلائٹ (چنے کا جھلساؤ)",
        "pathogen_type": "Fungus",
        "symptoms_en": "Circular brown spots with dark margins and tiny black dots in center on leaves, stems, pods.",
        "symptoms_ur": "پتوں، تنوں اور پھلیوں پر گول بھورے دھبے جن کے کنارے گہرے اور درمیان میں کالے نقطے ہوتے ہیں۔",
        "affected_part": "Whole Plant", "season": "Winter/Spring",
        "region_pakistan": "Thal, Potohar (Punjab)", "climate_trigger": "Rainy, cool weather",
        "severity_level": "Critical",
        "spray_chemical_en": "Carbendazim or Chlorothalonil", "brand_name_pakistan": "Bavistin 50WP (BASF PK)",
        "dose_per_acre": "400g / acre", "spray_timing": "Before rainfall or at first symptoms",
        "safety_precautions_ur": "بیماری شروع ہوتے ہی فوراً سپرے کریں۔",
        "biological_control": "Plant resistant varieties, deep ploughing.",
        "economic_loss_pct": "50-100%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Chickpea", "crop_name_ur": "چنا",
        "disease_name_en": "Fusarium Wilt", "disease_name_ur": "مرجھاؤ (ولٹ)",
        "pathogen_type": "Fungus",
        "symptoms_en": "Drooping of leaves and stems. Entire plant yellows and dries up. Internal roots/stem turn black/brown.",
        "symptoms_ur": "پتوں اور تنوں کا لٹک جانا، پورا پودا پیلا ہو کر سوکھ جاتا ہے۔ جڑیں اندر سے کالی/بھوری۔",
        "affected_part": "Roots, Whole Plant", "season": "Spring",
        "region_pakistan": "Punjab, Sindh", "climate_trigger": "Warm, dry soil after rain",
        "severity_level": "High",
        "spray_chemical_en": "Thiophanate Methyl (Seed treatment)", "brand_name_pakistan": "Topsin-M 70WP",
        "dose_per_acre": "2g / kg seed", "spray_timing": "Before planting",
        "safety_precautions_ur": "بیج کو زہر لگا کر کاشت کریں۔ بیماری آنے پر سپرے کام نہیں کرتا۔",
        "biological_control": "Late sowing, resistant varieties.",
        "economic_loss_pct": "20-60%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Chickpea", "crop_name_ur": "چنا",
        "disease_name_en": "Botrytis Gray Mold", "disease_name_ur": "گرے مولڈ (سرمئی پھپھوندی)",
        "pathogen_type": "Fungus",
        "symptoms_en": "Gray fungal mass on flowers, pods, and branches. Causes flower drop.",
        "symptoms_ur": "پھولوں، پھلیوں اور شاخوں پر سرمئی رنگ کی پھپھوندی۔ پھول گر جاتے ہیں۔",
        "affected_part": "Flowers, Pods", "season": "Spring",
        "region_pakistan": "Punjab", "climate_trigger": "Very dense crop, high humidity",
        "severity_level": "Medium",
        "spray_chemical_en": "Mancozeb", "brand_name_pakistan": "Dithane M-45",
        "dose_per_acre": "1000g / acre", "spray_timing": "At flowering stage",
        "safety_precautions_ur": "فصل کو زیادہ گھنا نہ ہونے دیں۔",
        "biological_control": "Avoid excessive seed rate, wide spacing.",
        "economic_loss_pct": "10-30%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    },
    {
        "crop_name_en": "Chickpea", "crop_name_ur": "چنا",
        "disease_name_en": "Root Rot", "disease_name_ur": "جڑ کا سڑنا (روٹ روٹ)",
        "pathogen_type": "Fungus",
        "symptoms_en": "Seedlings die early. Roots show black/brown decaying lesions.",
        "symptoms_ur": "چھوٹے پودوں کا مرنا۔ جڑوں پر کالے/بھورے گلنے کے نشانات۔",
        "affected_part": "Roots", "season": "Winter",
        "region_pakistan": "All Regions", "climate_trigger": "High soil moisture, cool soil",
        "severity_level": "Medium",
        "spray_chemical_en": "Fungicide Seed Treatment", "brand_name_pakistan": "Aliette / Topsin-M",
        "dose_per_acre": "Seed treatment", "spray_timing": "Before planting",
        "safety_precautions_ur": "کھیت میں پانی کھڑا نہ ہونے دیں۔",
        "biological_control": "Good drainage, delay sowing if soil is too wet.",
        "economic_loss_pct": "10-20%", "data_source": "Manual Addition", "verified_year": 2024,
        "country_code": "PK", "confidence": "High"
    }
]

def add_crops():
    print(f"\n{Fore.CYAN}--- FASAL DOCTOR: ADDING MISSING CROPS ---{Style.RESET_ALL}")
    
    # 1. Load existing dataset
    if not os.path.exists(MASTER_JSON):
        print(f"{Fore.RED}Error: {MASTER_JSON} not found.{Style.RESET_ALL}")
        return

    with open(MASTER_JSON, "r", encoding="utf-8") as f:
        master_data = json.load(f)
    
    print(f"Loaded existing master dataset: {len(master_data)} records.")

    # 2. Extract existing crop+disease names to prevent duplicates
    existing_keys = {f"{r.get('crop_name_en','').lower()}|{r.get('disease_name_en','').lower()}" for r in master_data}

    # 3. Append new records safely
    added_count = 0
    for new_rec in NEW_RECORDS:
        key = f"{new_rec['crop_name_en'].lower()}|{new_rec['disease_name_en'].lower()}"
        if key not in existing_keys:
            master_data.append(new_rec)
            existing_keys.add(key)
            added_count += 1
            print(f"  {Fore.GREEN}+ Added: {new_rec['crop_name_en']} - {new_rec['disease_name_en']}{Style.RESET_ALL}")
        else:
            print(f"  {Fore.YELLOW}- Skipped (exists): {new_rec['crop_name_en']} - {new_rec['disease_name_en']}{Style.RESET_ALL}")

    # 4. Re-assign IDs (PK-001, PK-002, ...)
    print(f"\n{Fore.CYAN}Re-assigning IDs...{Style.RESET_ALL}")
    for idx, rec in enumerate(master_data, 1):
        rec["id"] = f"PK-{idx:03d}"

    # 5. Save back to master_dataset.json
    with open(MASTER_JSON, "w", encoding="utf-8") as f:
        json.dump(master_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n{Fore.GREEN}Success! Total records now: {len(master_data)}{Style.RESET_ALL}")
    print(f"New records added this run: {added_count}")

    # 6. Re-embed into ChromaDB
    print(f"\n{Fore.CYAN}Running src/embedder.py to update ChromaDB...{Style.RESET_ALL}")
    try:
        subprocess.run(["python", "src/embedder.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Error running embedder.py: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    add_crops()
