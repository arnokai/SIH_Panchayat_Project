# TerraMind Frontend Workspace & Technical Roadmap

> **Assigned Owner:** Member 1 — Frontend Engineer  
> **Workspace:** `frontend/`  
> **Live Deployment (Vercel):** [https://sih-panchayat-project.vercel.app](https://sih-panchayat-project.vercel.app)  
> **Backend API (Render):** [https://sih-panchayat-project.onrender.com](https://sih-panchayat-project.onrender.com)  
> **Problem Statement:** SIH26074 (Ministry of Earth Sciences — Downscaling Weather Forecasts for Agro-Meteorological Advisory Services)  
> **Status:** React 18 + Vite live in production. Core 5-day cards and comparison map operational. Priority 1 user features in active development.

---

## 1. Executive Summary & Role Mission

As the **Frontend Engineer (Member 1)**, you are the bridge between advanced meteorological AI and rural farmers. You own the complete user interface and client experience. Your mission is to build an intuitive, high-contrast, accessible, and offline-capable dashboard that turns complex multi-variable weather predictions into simple, actionable farming decisions.

### Key Success Criteria for SIH Presentation:
1. **Extreme Usability for Rural Farmers:** Illiterate and elderly farmers must be able to listen to advisories via Bengali Voice/TTS with a single tap.
2. **Instant Community Dissemination:** One-click WhatsApp sharing to local farmer groups (*Krishi Dal*).
3. **Offline Resilience:** PWA caching ensuring forecasts remain viewable even when rural 4G/2G signals drop.
4. **Spatial Clarity:** Interactive Leaflet map displaying real-time microclimate differences across the 8 panchayats in Amdanga Block.

---

## 2. Directory Structure & Key Files

```text
frontend/
├── index.html                      # HTML entry point, PWA meta tags, fonts
├── package.json                    # Dependencies: React 18, Vite, Leaflet, Lucide icons
├── vite.config.js                  # Vite configuration & PWA plugin settings
├── vercel.json                     # Vercel SPA routing and cache headers
├── .env                            # Local / cloud API base URL
├── src/
│   ├── main.jsx                    # React root render
│   ├── App.jsx                     # Core state: panchayat selector, language toggle, forecast view
│   ├── App.css                     # Mobile-first high-contrast styling (outdoor sunlight readable)
│   ├── components/
│   │   ├── ForecastCard.jsx        # Individual daily weather & advisory card
│   │   ├── ComparisonMap.jsx       # Interactive Leaflet map of the 8 Amdanga Panchayats
│   │   ├── AudioAdvisory.jsx       # Bengali Text-to-Speech audio player component
│   │   ├── WhatsAppShare.jsx       # One-click WhatsApp share button and formatter
│   │   ├── UncertaintyBar.jsx      # P10 / P50 / P90 rainfall uncertainty visualizer
│   │   ├── CropSelector.jsx        # Crop stage and crop selection dropdown
│   │   └── OfflineBanner.jsx       # Network status indicator and cached data alert
│   └── services/
│       ├── api.js                  # Axios / Fetch client calling backend endpoints
│       └── cacheService.js         # LocalStorage / IndexedDB offline cache manager
└── README.md                       # (This workspace guide & technical backlog)
```

---

## 3. Detailed Action Plan & Task Checklist

### Phase 1: High-Impact Jury Features (Priority 1)
- [ ] **1.1 Bengali Voice / Text-to-Speech ("অডিও শুনুন"):**
  - Add a dedicated audio play button on every daily forecast and active advisory card.
  - Implement two-tier audio delivery:
    - *Tier 1 (Client Native):* Use Web Speech API (`window.speechSynthesis`) targeting Bengali (`bn-IN` / `bn-BD`).
    - *Tier 2 (Cloud / Backend Stream):* Fallback to backend `GET /v1/tts/synthesize?panchayat_id=A1&lang=bn` streaming high-quality neural Bengali audio.
  - Provide visual audio state: animated waveform or pulsing speaker icon during playback.
- [ ] **1.2 One-Click WhatsApp Share Button ("হোয়াটসঅ্যাপে শেয়ার করুন"):**
  - Add a distinct green WhatsApp button on the advisory banner.
  - Format message using standard WhatsApp markdown:
    ```text
    🌾 *টেরামাইন্ড পঞ্চায়েত কৃষি বার্তা* 🌾
    📍 পঞ্চায়েত: আমডাঙা (A2) | তারিখ: ০৫/০৯/২০২৬
    🌧️ আজ: হালকা বৃষ্টি (২.৪ মিমি) | সর্বোচ্চ তাপমাত্রা: ৩২°C
    ⚠️ কৃষি পরামর্শ:
    ইউরিয়া সার প্রয়োগ করবেন না। জমিতে জল নিষ্কাশনের ব্যবস্থা রাখুন।
    🔗 বিস্তারিত দেখুন: https://sih-panchayat-project.vercel.app
    ```
  - Trigger via `window.open(`https://api.whatsapp.com/send?text=${encodedText}`, '_blank')`.
- [ ] **1.3 Offline-First Progressive Web App (PWA):**
  - Install and configure `vite-plugin-pwa`.
  - Add `manifest.json` with high-res green agri icons, `theme_color: "#2e7d32"", and `display: "standalone"`.
  - Implement service worker caching strategy (`StaleWhileRevalidate`) for API requests to `/v1/forecast`.
  - Display an "Offline Mode — Showing Cached Forecast" banner when `navigator.onLine === false`.

---

### Phase 2: Scientific Rigor & Data Visualization
- [ ] **2.1 Quantile Uncertainty Visualization (P10 / P50 / P90):**
  - Move beyond single deterministic numbers (e.g. "28 mm").
  - Render an intuitive confidence bar showing:
    - **P10 (Minimum likely rain):** e.g., 12 mm
    - **P50 (Expected median):** e.g., 24 mm
    - **P90 (Worst-case heavy downpour):** e.g., 48 mm
  - Helps farmers make risk-managed decisions (e.g., whether to dig drainage trenches).
- [ ] **2.2 Single-Call Spatial Map Integration:**
  - Update `src/ComparisonMap.jsx` to consume the new batch endpoint `GET /v1/block/overview` in a single network call.
  - Dynamically color-code all 8 panchayats on the Leaflet map:
    - 🔴 **Red Marker:** High/Critical Warning (Pest alert, severe rain, heat stress).
    - 🟡 **Yellow Marker:** Moderate Advisory (Moderate rain, delay spray).
    - 🟢 **Green Marker:** Normal / Safe Farming Operations.
  - Clicking any panchayat marker smoothly switches the active dashboard to that panchayat.
- [ ] **2.3 Operational Agronomic Badges:**
  - Render clear, color-coded status pills:
    - 🚫 **Urea Application:** *Avoid for 48 hrs (Runoff risk)*
    - 🚜 **Field Spraying:** *Safe tomorrow 8:00 AM – 11:00 AM*
    - 💧 **Irrigation:** *Not needed (Rain expected)*

---

### Phase 3: Accessibility & Design Polish
- [ ] **3.1 High-Contrast Sunlight Theme:**
  - Farmers use mobile phones in broad daylight in the fields. Ensure bold contrast (WCAG AAA compliant), large bold typography, and minimum 48×48px tap targets.
- [ ] **3.2 Language Persistence:**
  - Support instant Bengali (`বাংলা`) and English (`English`) toggle.
  - Store selected language in `localStorage` so it persists across sessions.
- [ ] **3.3 Printable Notice Board View:**
  - Add a "Print Notice Board Bulletin" button triggering a print-optimized CSS layout for Gram Panchayat offices and Common Service Centres (CSCs).

---

## 4. Local Development & Deployment

```bash
cd frontend
npm install
npm run dev        # Runs local dev server on http://localhost:5173
npm run build      # Generates production build in frontend/dist
```

### Environment Setup (`.env`)
```env
# Connect to local backend:
VITE_API_BASE_URL=http://127.0.0.1:8000

# Connect to production Render cloud backend:
# VITE_API_BASE_URL=https://sih-panchayat-project.onrender.com
```
