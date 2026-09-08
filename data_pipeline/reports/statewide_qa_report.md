# SIH26074 — Statewide Data Quality & Integrity Report
**Generated on:** 2026-09-08 04:02:58 IST
**Owner:** Member 1 (Data Engineer)
**Scope:** All of West Bengal
**Status:** ✅ PASSED — PRODUCTION READY

---

## 1. Executive Summary
* **Total Rows:** 2,440,809
* **Gram Panchayats:** 3,339 across 22 districts
* **Date Range:** `2024-01-01` to `2025-12-31` (731 continuous days)
* **Grid Format:** 1 row per `(panchayat_id, date)`
* **Duplicates:** 0
* **Storage:** District-partitioned Parquet under `data_pipeline/processed/statewide/`

---

## 2. Integrity Verification
| Check | Condition | Result | Status |
|---|---|---|---|
| **Key Uniqueness** | `(date, panchayat_id)` unique | 0 duplicates | ✅ PASS |
| **Grid Completeness** | `rows == dates × GPs` | 2,440,809 == 2,440,809 | ✅ PASS |
| **Rainfall Bound** | `target_rain_mm >= 0` | 0 negative | ✅ PASS |
| **Soil Sum** | `sand + clay + silt == 100%` | 0 invalid | ✅ PASS |
| **Hurdle Consistency** | `binary == (rain >= 0.5)` | 0 mismatches | ✅ PASS |
| **Static Feature NaNs** | 0 NaNs in GIS columns | 0 NaNs | ✅ PASS |
| **Temporal Leakage** | No future obs in inputs | Code audit verified | ✅ PASS |

---

## 3. District Breakdown
| District | GPs | Rows | Rain Days (%) |
|---|---|---|---|
| Alipurduar | 66 | 48,246 | 56.2% |
| Bankura | 190 | 138,890 | 43.9% |
| Birbhum | 167 | 122,077 | 42.6% |
| Cooch Behar | 128 | 93,568 | 48.5% |
| Dakshin Dinajpur | 64 | 46,784 | 43.9% |
| Darjeeling | 80 | 58,480 | 57.7% |
| Hooghly | 207 | 151,317 | 47.5% |
| Howrah | 157 | 114,767 | 49.1% |
| Jalpaiguri | 80 | 58,480 | 49.9% |
| Jhargram | 79 | 57,749 | 46.8% |
| Kalimpong | 42 | 30,702 | 65.7% |
| Malda | 146 | 106,726 | 41.7% |
| Murshidabad | 255 | 186,405 | 42.8% |
| Nadia | 187 | 136,697 | 45.3% |
| North 24 Parganas | 200 | 146,200 | 48.0% |
| Paschim Bardhaman | 62 | 45,322 | 42.3% |
| Paschim Medinipur | 211 | 154,241 | 48.0% |
| Purba Bardhaman | 215 | 157,165 | 45.0% |
| Purba Medinipur | 223 | 163,013 | 49.3% |
| Purulia | 170 | 124,270 | 40.8% |
| South 24 Parganas | 312 | 228,072 | 37.1% |
| Uttar Dinajpur | 98 | 71,638 | 25.1% |

---

## 4. Target Statistics
* **Rain Days (>= 0.5 mm):** 1,098,175 (45.0%)
* **Dry Days (< 0.5 mm):** 1,342,634 (55.0%)
* **Max Rainfall:** 392.35 mm
* **Temperature Range:** -5.8°C to 46.2°C

---

## 5. Recommended Temporal Splits
* **Train:** `2024-01-01` to `2024-12-31`
* **Validation:** `2025-01-01` to `2025-06-30`
* **Test (Holdout):** `2025-07-01` to `2025-12-31`
