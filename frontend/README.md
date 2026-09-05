# TerraMind Frontend Workspace

> **Assigned Owner:** Member 1 — Frontend Engineer  
> **Deployment:** [sih-panchayat-project.vercel.app](https://sih-panchayat-project.vercel.app) (Vercel)

---

## 1. Overview

The TerraMind frontend is a React 18 single-page application built with Vite and Leaflet. It delivers localized, 5-day agro-meteorological advisories in Bengali and English for the 8 panchayats in Amdanga Block, North 24 Parganas, West Bengal.

---

## 2. Quick Start

### Installation
```bash
cd frontend
npm install
```

### Run Locally (Development)
```bash
npm run dev
```
Runs at: **http://localhost:5173**

### Build for Production
```bash
npm run build
```

---

## 3. Environment Configuration

Create or update `.env` in the `frontend/` folder:

* **To connect to local backend:**
  ```env
  VITE_API_BASE_URL=http://127.0.0.1:8000
  ```

* **To connect to live cloud backend (Render):**
  ```env
  VITE_API_BASE_URL=https://sih-panchayat-project.onrender.com
  ```

---

## 4. Key Components

* `src/App.jsx`: Main interface managing panchayat selection (`A1` to `A8`), crop selection (`paddy` or `vegetables`), 5-day weather forecast cards, and the active bilingual advisory banner.
* `src/ComparisonMap.jsx`: Leaflet map visualization displaying all 8 panchayats with GPS coordinates across Amdanga Block.
* `src/App.css`: High-contrast styling designed for readability under direct outdoor sunlight on low-cost mobile devices.
* `vercel.json`: Single Page Application (SPA) client-side rewrite rules for Vercel hosting.

---

## 5. Active Frontend Feature Roadmap (Priority 1)

1. [ ] **Bengali Text-to-Speech ("অডিও শুনুন"):**
   * Add a speaker icon button on advisory cards using browser `window.speechSynthesis` or Bhashini API for voice advisories.
2. [ ] **One-Click WhatsApp Share Button:**
   * Pre-format today's advisory into a WhatsApp link (`https://wa.me/?text=...`) for instant forwarding to local farmer groups.
3. [ ] **Offline PWA Support:**
   * Integrate `vite-plugin-pwa` with a service worker to cache the last fetched forecast for offline access when rural connectivity drops.
