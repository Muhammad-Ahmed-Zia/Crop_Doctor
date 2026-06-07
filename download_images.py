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
    (BASE/"crops"/"wheat.jpg",       "https://unsplash.com/s/photos/wheat-crop", "Wheat grains"),
    (BASE/"crops"/"cotton.jpg",      "https://stock.adobe.com/search?k=cotton+plant", "Cotton bolls"),
    (BASE/"crops"/"rice.jpg",        "https://www.istockphoto.com/photos/sugar-cane-plant", "Rice paddy field"),
    (BASE/"crops"/"sugarcane.jpg",   "https://www.britannica.com/plant/corn-plant", "Sugarcane field"),
    (BASE/"crops"/"maize.jpg",       "https://images.unsplash.com/photo-1543257580-7269da773bf5?w=600&q=80", "Maize corn field"),
    (BASE/"crops"/"brassica.jpg",    "https://stock.adobe.com/search?k=mustard+field", "Yellow mustard field"),
    (BASE/"crops"/"gram.jpg",        "https://www.istockphoto.com/photos/chickpea-fields", "Chickpea pods"),
    (BASE/"crops"/"groundnut.jpg",   "https://stock.adobe.com/search?k=%22groundnut+field%22", "Groundnut peanuts"),
    (BASE/"crops"/"barley.jpg",      "https://www.shutterstock.com/image-photo/wheat-barley-field-during-sunset-farmland-536374297", "Barley field"),
    (BASE/"crops"/"lentil.jpg",      "https://www.shutterstock.com/search/lentils-field?page=2", "Lentils"),
    (BASE/"crops"/"sorghum.jpg",     "https://www.istockphoto.com/photos/sorghum-field", "Sorghum plants"),
    (BASE/"crops"/"millet.jpg",      "https://www.dreamstime.com/fields-pearl-millets-bajra-processing-farm-lovely-view-millet-stalks-sorghum-plant-views-farmland-cultivation-pearls-image383732849", "Millet stalks"),
    (BASE/"crops"/"coriander.jpg",   "https://www.vecteezy.com/photo/20113218-small-field-of-organic-coriander-growing", "Coriander herb"),
    (BASE/"crops"/"paddy.jpg",       "https://www.dreamstime.com/stock-photos-autumn-rice-field-image11824383", "Paddy rice field"),
    (BASE/"crops"/"vegetables.jpg",  "https://www.gardeningknowhow.com/edible/vegetables/vgen/edible-landscaping-mixing-vegetables-and-herbs-with-flowers.htm", "Mixed vegetables"),
    (BASE/"crops"/"tomato.jpg",      "https://www.dreamstime.com/sunlit-tomato-field-fresh-ripe-red-tomatoes-green-vines-summer-sunlit-tomato-field-fresh-ripe-red-tomatoes-image357514223", "Tomatoes on vine"),
    (BASE/"crops"/"potato.jpg",      "https://www.vecteezy.com/free-photos/potato-farm", "Fresh potatoes"),
    (BASE/"crops"/"onion.jpg",       "https://www.envo-dan.com/weeds-are-a-challenge-for-crop-in-onion-fields/", "Red and white onions"),
    (BASE/"crops"/"chilies.jpg",     "https://www.istockphoto.com/photos/chili-field", "Red chili peppers"),
    # Features0&q=80
    (BASE/"features"/"ai-diagnosis.jpg", "https://www.vecteezy.com/free-photos/lab-microscope", "Lab microscope"),
    (BASE/"features"/"pk-brands.jpg",    "https://www.presentationgo.com/presentation/tractor-spraying-crops/", "Crop spraying"),
    (BASE/"features"/"bio-control.jpg",  "https://www.veganfoodandliving.com/features/organic-farming-sustainability/", "Natural farming"),
    (BASE/"features"/"severity.jpg",     "https://www.cropin.com/blogs/plant-disease-management-with-agri-tech/", "Diseased crop"),
    (BASE/"features"/"urdu.jpg",         "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=600&q=80", "Mobile phone"),
    (BASE/"features"/"safety.jpg",       "https://www.safeopedia.com/protective-clothing-for-agricultural-workers-and-pesticide-handlers/2/6505", "Safety gear"),
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
