"""
download_images.py — Fasal Doctor Image Downloader v3
Verified working URLs — run from project root: python download_images.py
"""
import os, sys, time, requests
from pathlib import Path

HERE = Path(__file__).resolve().parent
FRONTEND = HERE / "frontend" if (HERE / "frontend").exists() else HERE
BASE = FRONTEND / "images"
for f in [BASE, BASE/"crops", BASE/"features"]:
    f.mkdir(parents=True, exist_ok=True)

print(f"\n🌾 Fasal Doctor Image Downloader v3")
print(f"Saving to: {BASE}\n")

IMAGES = [
    # Hero
    (BASE/"hero-bg.jpg",        "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1920&q=80", "Hero wheat field"),
    # Crops — carefully verified IDs
    (BASE/"crops"/"wheat.jpg",       "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=600&q=80", "Wheat grains"),
    (BASE/"crops"/"cotton.jpg",      "https://images.unsplash.com/photo-1611735341450-74d61e660ad2?w=600&q=80", "Cotton bolls"),
    (BASE/"crops"/"rice.jpg",        "https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=600&q=80", "Rice paddy field"),
    (BASE/"crops"/"sugarcane.jpg",   "https://images.unsplash.com/photo-1604187351574-c75ca79f5807?w=600&q=80", "Sugarcane field"),
    (BASE/"crops"/"maize.jpg",       "https://images.unsplash.com/photo-1543257580-7269da773bf5?w=600&q=80", "Maize corn field"),
    (BASE/"crops"/"brassica.jpg",    "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=600&q=80", "Yellow mustard field"),
    (BASE/"crops"/"gram.jpg",        "https://images.unsplash.com/photo-1622623746005-f85c04e3d0a1?w=600&q=80", "Chickpea pods"),
    (BASE/"crops"/"groundnut.jpg",   "https://images.unsplash.com/photo-1567599872-5d39a37aadc1?w=600&q=80", "Groundnut peanuts"),
    (BASE/"crops"/"barley.jpg",      "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=600&q=80", "Barley field"),
    (BASE/"crops"/"lentil.jpg",      "https://images.unsplash.com/photo-1634205071832-0e08a34ab1a0?w=600&q=80", "Lentils"),
    (BASE/"crops"/"sorghum.jpg",     "https://images.unsplash.com/photo-1618944848704-2f22e5c7c86d?w=600&q=80", "Sorghum plants"),
    (BASE/"crops"/"millet.jpg",      "https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?w=600&q=80", "Millet stalks"),
    (BASE/"crops"/"coriander.jpg",   "https://images.unsplash.com/photo-1600565193348-f74bd3960d1b?w=600&q=80", "Coriander herb"),
    (BASE/"crops"/"paddy.jpg",       "https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=600&q=80", "Paddy rice field"),
    (BASE/"crops"/"vegetables.jpg",  "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&q=80", "Mixed vegetables"),
    (BASE/"crops"/"tomato.jpg",      "https://images.unsplash.com/photo-1582284540020-8acbe03f4924?w=600&q=80", "Tomatoes on vine"),
    (BASE/"crops"/"potato.jpg",      "https://images.unsplash.com/photo-1590165482129-1b8b27698780?w=600&q=80", "Fresh potatoes"),
    (BASE/"crops"/"onion.jpg",       "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=600&q=80", "Red and white onions"),
    (BASE/"crops"/"chilies.jpg",     "https://images.unsplash.com/photo-1526346698789-22fd84314424?w=600&q=80", "Red chili peppers"),
    # Features
    (BASE/"features"/"ai-diagnosis.jpg", "https://images.unsplash.com/photo-1532187643603-ba119ca4109e?w=600&q=80", "Lab microscope"),
    (BASE/"features"/"pk-brands.jpg",    "https://images.unsplash.com/photo-1574943320219-553eb213f72d?w=600&q=80", "Crop spraying"),
    (BASE/"features"/"bio-control.jpg",  "https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=600&q=80", "Natural farming"),
    (BASE/"features"/"severity.jpg",     "https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=600&q=80", "Diseased crop"),
    (BASE/"features"/"urdu.jpg",         "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=600&q=80", "Mobile phone"),
    (BASE/"features"/"safety.jpg",       "https://images.unsplash.com/photo-1574943320219-553eb213f72d?w=600&q=80", "Safety gear"),
]

H = {"User-Agent":"FasalDoctor/3.0"}
ok=fail=skip=0
for path,url,desc in IMAGES:
    if path.exists() and path.stat().st_size>5000:
        print(f"  ✓  {path.name:<28}(exists)")
        skip+=1; continue
    try:
        r=requests.get(url,timeout=20,headers=H); r.raise_for_status()
        path.write_bytes(r.content)
        print(f"  ✅ {path.name:<28}({len(r.content)//1024}KB)")
        ok+=1; time.sleep(0.4)
    except Exception as e:
        print(f"  ❌ {path.name:<28}FAILED: {e}")
        fail+=1

print(f"\n✅ {ok} downloaded  ✓ {skip} existed  ❌ {fail} failed")
if fail:
    print("\nFor failed images, search unsplash.com and save to frontend/images/crops/[name].jpg")
print(f"\nDone! Images at: {BASE}\n")
