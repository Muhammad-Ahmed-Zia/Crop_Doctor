/**
 * search-data.js — Global Search Index
 * Include this on every page before the search script.
 */
window.SEARCH_DATA = [
  // ── Pages ──
  { icon:'🏠', title:'Home', sub:'Welcome page', url:'index.html', text:'home fasal doctor welcome', ur:'' },
  { icon:'🌾', title:'All Crops', sub:'Browse 19 crops with diseases', url:'crops.html', text:'crops browse all crops list', ur:'فصلیں' },
  { icon:'🔬', title:'Diagnose Now', sub:'AI crop disease diagnosis', url:'diagnosis.html', text:'diagnose disease diagnosis symptoms', ur:'تشخیص' },
  { icon:'⭐', title:'Farmer Reviews', sub:'Read & share experiences', url:'reviews.html', text:'reviews testimonials farmers feedback', ur:'تجربات' },
  { icon:'ℹ️', title:'About Fasal Doctor', sub:'Tech stack, PARC data, mission', url:'about.html', text:'about mission parc gemini chromadb technology', ur:'بارے میں' },

  // ── Crops ──
  { icon:'🌾', title:'Wheat — گندم', sub:'85 diseases · Rabi · Punjab, KPK', url:'crops.html?crop=Wheat', text:'wheat yellow rust brown rust loose smut karnal bunt powdery mildew septoria root rot rabi', ur:'گندم پیلا زنگ' },
  { icon:'🌿', title:'Cotton — کپاس', sub:'62 diseases · Kharif · Punjab, Sindh', url:'crops.html?crop=Cotton', text:'cotton clcuv leaf curl virus bacterial blight fusarium wilt bollworm whitefly kharif', ur:'کپاس بیماری' },
  { icon:'🍚', title:'Rice — چاول', sub:'48 diseases · Kharif · Punjab, Sindh', url:'crops.html?crop=Rice', text:'rice blast bacterial leaf blight brown spot sheath blight basmati kharif', ur:'چاول بلاسٹ' },
  { icon:'🎋', title:'Sugarcane — گنا', sub:'35 diseases · Both seasons', url:'crops.html?crop=Sugarcane', text:'sugarcane red rot smut ratoon stunting grassy shoot rabi kharif', ur:'گنا سرخ سڑن' },
  { icon:'🌽', title:'Maize — مکئی', sub:'42 diseases · Kharif · KPK, Punjab', url:'crops.html?crop=Maize', text:'maize corn streak virus northern leaf blight ear rot stalk rot kharif', ur:'مکئی بیماری' },
  { icon:'🌱', title:'Brassica — سرسوں', sub:'28 diseases · Rabi · Punjab', url:'crops.html?crop=Brassica', text:'brassica mustard alternaria blight sclerotinia white rust powdery mildew rabi', ur:'سرسوں بیماری' },
  { icon:'🫘', title:'Gram — چنا', sub:'32 diseases · Rabi', url:'crops.html?crop=Gram', text:'gram chickpea ascochyta blight fusarium wilt collar rot rabi legume', ur:'چنا بیماری' },
  { icon:'🥜', title:'Groundnut — مونگ پھلی', sub:'24 diseases · Kharif', url:'crops.html?crop=Groundnut', text:'groundnut peanut leaf spot rust aflatoxin aspergillus collar rot kharif', ur:'مونگ پھلی' },
  { icon:'🌾', title:'Barley — جَو', sub:'22 diseases · Rabi', url:'crops.html?crop=Barley', text:'barley powdery mildew stripe net blotch scald loose smut rabi', ur:'جو بیماری' },
  { icon:'🌿', title:'Lentil — مسور', sub:'18 diseases · Rabi', url:'crops.html?crop=Lentil', text:'lentil stemphylium blight collar rot botrytis ascochyta rabi legume', ur:'مسور بیماری' },
  { icon:'🌾', title:'Sorghum — جوار', sub:'20 diseases · Kharif', url:'crops.html?crop=Sorghum', text:'sorghum grain mould head smut anthracnose downy mildew kharif', ur:'جوار بیماری' },
  { icon:'🌾', title:'Millet — باجرہ', sub:'15 diseases · Kharif', url:'crops.html?crop=Millet', text:'millet bajra downy mildew ergot rust smut mosaic kharif', ur:'باجرہ بیماری' },
  { icon:'🌿', title:'Coriander — دھنیا', sub:'12 diseases · Rabi', url:'crops.html?crop=Coriander', text:'coriander dhania wilt root rot alternaria powdery mildew rabi spice', ur:'دھنیا بیماری' },
  { icon:'🌾', title:'Paddy — دھان', sub:'30 diseases · Kharif', url:'crops.html?crop=Paddy', text:'paddy rice blast bacterial blight sheath blight stem borer kharif', ur:'دھان بیماری' },
  { icon:'🌿', title:'Vegetables', sub:'Kharif & Rabi', url:'crops.html?crop=Vegetables', text:'vegetables tomato potato onion fungal diseases', ur:'سبزیاں' },

  // ── Common diseases (searchable) ──
  { icon:'🦠', title:'Yellow Rust (Stripe Rust)', sub:'Wheat — High severity', url:'diagnosis.html', text:'yellow rust stripe rust wheat pustules powdery propiconazole tilt 250', ur:'پیلا زنگ گندم' },
  { icon:'🦠', title:'Cotton Leaf Curl Virus (CLCuV)', sub:'Cotton — Critical', url:'diagnosis.html', text:'cotton leaf curl virus clcuv whitefly curling leaves viral', ur:'کپاس پتہ مڑنا' },
  { icon:'🦠', title:'Rice Blast', sub:'Rice — High severity', url:'diagnosis.html', text:'rice blast pyricularia oryzae lesions tricyclazole', ur:'چاول بلاسٹ' },
  { icon:'🦠', title:'Ascochyta Blight', sub:'Gram — Critical in cool wet weather', url:'diagnosis.html', text:'ascochyta blight gram chickpea lesions wet cool vitavax', ur:'چنا آسکوکائٹا' },
  { icon:'🦠', title:'Karnal Bunt', sub:'Wheat — Seed-borne', url:'diagnosis.html', text:'karnal bunt wheat teliospores quarantine partial bunt', ur:'کرنال بنٹ' },
  { icon:'🦠', title:'Alternaria Blight', sub:'Brassica / Mustard', url:'diagnosis.html', text:'alternaria blight brassica mustard black spots score rovral', ur:'سرسوں الٹرنیریا' },
  { icon:'🦠', title:'Red Rot', sub:'Sugarcane — Very destructive', url:'diagnosis.html', text:'red rot sugarcane glomerella cane stalks reddening', ur:'گنا سرخ سڑن' },
  { icon:'🦠', title:'Powdery Mildew', sub:'Multiple crops', url:'diagnosis.html', text:'powdery mildew white powder sulphur systhane wheat barley gram', ur:'پاؤڈری پھپھوندی' },
  { icon:'🦠', title:'Fusarium Wilt', sub:'Cotton / Gram', url:'diagnosis.html', text:'fusarium wilt yellowing vascular browning soil borne cotton gram', ur:'فیوزاریم ولٹ' },
  { icon:'🦠', title:'Bacterial Blight', sub:'Cotton — Boll damage', url:'diagnosis.html', text:'bacterial blight cotton angular leaf spots boll rot copper oxychloride', ur:'کپاس بیکٹیریل' },
];
