# SIH26074 — Data Quality & Integrity Report
**Generated on:** 2026-09-08 09:28:26 IST  
**Owner:** Member 1 (Data Engineer)  
**Status:** ✅ PASSED — PRODUCTION READY

---

## 1. Executive Summary
* **Total Rows:** 5,848
* **Panchayats Included:** 8 (Amdanga Block, West Bengal)
* **Date Range:** `2024-01-01` to `2025-12-31` (731 continuous days)
* **Grid Format:** Exactly 1 row per `(panchayat_id, date)`
* **Duplicates:** 0 duplicate keys
* **Parquet File:** `/home/arnokai/Projects/SIH_Panchayat_Project/data_pipeline/processed/training_table.parquet` (0.10 MB)
* **CSV File:** `/home/arnokai/Projects/SIH_Panchayat_Project/data_pipeline/processed/training_table.csv` (1.78 MB)

---

## 2. Integrity & Leakage Verification
| Check | Condition | Result | Status |
|---|---|---|---|
| **Key Uniqueness** | `(date, panchayat_id)` is strictly unique | 0 duplicates | ✅ PASS |
| **Grid Completeness** | `total_rows == dates * panchayats` | 5848 == 5848 | ✅ PASS |
| **Rainfall Bound** | `target_rain_mm >= 0` | 0 negative values | ✅ PASS |
| **Temperature Bounds** | `0°C <= tmax <= 55°C` | 0 anomalies | ✅ PASS |
| **Soil Texture Sum** | `sand + clay + silt == 100%` | 0 mismatches | ✅ PASS |
| **Temporal Leakage** | No future observations in input features | Verified via code audit | ✅ PASS |

---

## 3. Class Distribution & Target Statistics
* **Rain Days (>= 0.5 mm):** 2638 (45.1%)
* **Dry Days (< 0.5 mm):** 3210 (54.9%)
* **Max Rainfall Recorded:** 83.96 mm
* **Mean Temperature:** 30.6°C (Max: 43.7°C, Min: 9.0°C)

---

## 4. Suggested Temporal Splits for Member 2 (ML)
* **Train Set:** `2024-01-01` to `2024-12-31` (366 days x 8 = 2,928 rows)
* **Validation Set:** `2025-01-01` to `2025-06-30` (181 days x 8 = 1,448 rows)
* **Test Set (Untouched Holdout):** `2025-07-01` to `2025-12-31` (184 days x 8 = 1,472 rows)
