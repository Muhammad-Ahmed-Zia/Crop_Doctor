/**
 * api.js — Fasal Doctor Frontend API Client
 * ─────────────────────────────────────────
 * Set FASAL_API to your FastAPI server URL.
 *
 * Local dev:       http://localhost:8000
 * Production:      https://your-server.com
 *
 * If the server is unreachable the frontend
 * automatically shows a demo / offline response.
 */

const FASAL_API = "http://localhost:8000";

/**
 * POST /diagnose
 * @param {string} query        - symptom description (Urdu or English)
 * @param {string} cropFilter   - e.g. "Wheat" or "" for all crops
 * @param {string} language     - "both" | "english" | "urdu"
 * @returns {Promise<{success:boolean, response:string, error?:string}>}
 */
async function callDiagnose(query, cropFilter = "", language = "both") {
  try {
    const res = await fetch(`${FASAL_API}/diagnose`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        crop_filter: cropFilter || null,
        language,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Server error");
    }

    const data = await res.json();
    return { success: true, response: data.response };

  } catch (err) {
    console.warn("Fasal API unreachable, using demo response:", err.message);
    return { success: false, error: err.message, response: getDemoResponse(query) };
  }
}

/**
 * GET /status — check if the RAG engine is loaded
 */
async function checkServerStatus() {
  try {
    const res = await fetch(`${FASAL_API}/status`, { signal: AbortSignal.timeout(3000) });
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  }
}

// ── Demo fallback response ────────────────────────────────────────────────────
// Used when the FastAPI server is not reachable (e.g. static HTML demo).
function getDemoResponse(query) {
  const isUrdu = /[\u0600-\u06FF]/.test(query);

  return `
**Disease Name:** Yellow Rust (Stripe Rust)
**بیماری کا نام:** پیلا زنگ (گندم)

**Affected Crop:** Wheat
**متاثرہ فصل:** گندم

**Symptoms:**
**English:** Yellow-orange powdery pustules arranged in stripes along leaf veins. Leaves turn yellow and dry out rapidly. Pustules turn black as crop matures. Severe infections cause premature senescence of entire plant.
**اردو:** پتوں پر پیلے نارنجی رنگ کے پاؤڈر نما دھبے قطاروں میں ظاہر ہوتے ہیں۔ پتے پیلے پڑ کر تیزی سے خشک ہو جاتے ہیں۔ فصل پکنے پر دھبے کالے ہو جاتے ہیں۔ شدید انفیکشن میں پورا پودا قبل از وقت خشک ہو سکتا ہے۔

**Spray Chemical:** Propiconazole 25% EC
**Pakistan Brand:** Tilt 250 EC (Syngenta Pakistan)
**Dose per Acre:** 200–250 ml per acre mixed in 100 litres water
**Spray Timing:** At first sign of disease; repeat after 14 days if needed. Best applied early morning.

**Severity:** High — can cause critical losses if not controlled within 7 days of symptom appearance
**Yield Loss:** 30–70% if left untreated; early treatment limits losses to under 10%

---SAFETY WARNING---
سپرے کرتے وقت دستانے، ماسک اور آنکھوں کی حفاظت کا سامان پہنیں۔ سپرے کے بعد ہاتھ اور منہ اچھی طرح دھوئیں۔ بچوں اور جانوروں کو کھیت سے دور رکھیں۔ سپرے کیا ہوا چارہ کم از کم 7 دن تک جانوروں کو نہ دیں۔ دوائی کو اصل ڈبے میں بند اور بچوں کی پہنچ سے دور محفوظ رکھیں۔
---

---BIOLOGICAL CONTROL---
Use resistant wheat varieties such as NARC-2011, Punjab-2011, and Ujala-2016. Avoid overly dense crop canopies by following recommended seed rates. Crop rotation with non-cereal crops (e.g. legumes) helps reduce soil inoculum levels. Trichoderma harzianum-based biocontrol products can suppress secondary fungal infections.
---

> ⚠️ **Demo Mode** — Connect to the FastAPI backend for real AI diagnosis. See api.js to configure your server URL.
`.trim();
}
