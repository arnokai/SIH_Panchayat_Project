from pathlib import Path

import pandas as pd
import xarray as xr


# ==========================================
# 1. PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

PANCHAYAT_FILE = (
    BASE_DIR / "panchayats.csv"
)

IMD_2024_FILE = (
    BASE_DIR
    / "raw"
    / "imd"
    / "RF25_ind2024_rfp25.nc"
)

IMD_2025_FILE = (
    BASE_DIR
    / "raw"
    / "imd"
    / "RF25_ind2025_rfp25.nc"
)

OUTPUT_FILE = (
    BASE_DIR
    / "raw"
    / "imd_panchayat_rainfall.csv"
)


# ==========================================
# 2. LOAD PANCHAYATS
# ==========================================

panchayats = pd.read_csv(
    PANCHAYAT_FILE
)

print("========================================")
print("IMD RAINFALL EXTRACTION")
print("========================================")

print(
    "Panchayats:",
    len(panchayats)
)


# ==========================================
# 3. LOAD IMD DATA
# ==========================================

ds_2024 = xr.open_dataset(
    IMD_2024_FILE
)

ds_2025 = xr.open_dataset(
    IMD_2025_FILE
)

print("\n2024:")
print(ds_2024)

print("\n2025:")
print(ds_2025)


# ==========================================
# 4. EXTRACT NEAREST GRID CELL
# ==========================================

all_records = []

print("\n========================================")
print("PANCHAYAT → IMD GRID MAPPING")
print("========================================")


for _, p in panchayats.iterrows():

    lat = float(
        p["latitude"]
    )

    lon = float(
        p["longitude"]
    )

    # Select nearest IMD grid point.
    point_2024 = ds_2024["RAINFALL"].sel(
        LATITUDE=lat,
        LONGITUDE=lon,
        method="nearest"
    )

    point_2025 = ds_2025["RAINFALL"].sel(
        LATITUDE=lat,
        LONGITUDE=lon,
        method="nearest"
    )

    imd_lat = float(
        point_2024["LATITUDE"].values
    )

    imd_lon = float(
        point_2024["LONGITUDE"].values
    )

    print(
        f"{p['panchayat_id']} "
        f"{p['panchayat_name']}: "
        f"Panchayat=({lat:.6f}, {lon:.6f}) "
        f"→ IMD=({imd_lat:.2f}, {imd_lon:.2f})"
    )


    # --------------------------------------
    # 2024
    # --------------------------------------

    values_2024 = (
        point_2024
        .to_series()
        .reset_index()
    )

    values_2024.columns = [
        "date",
        "rain_mm"
    ]

    values_2024["panchayat_id"] = (
        p["panchayat_id"]
    )

    values_2024["panchayat_name"] = (
        p["panchayat_name"]
    )

    values_2024["imd_latitude"] = (
        imd_lat
    )

    values_2024["imd_longitude"] = (
        imd_lon
    )


    # --------------------------------------
    # 2025
    # --------------------------------------

    values_2025 = (
        point_2025
        .to_series()
        .reset_index()
    )

    values_2025.columns = [
        "date",
        "rain_mm"
    ]

    values_2025["panchayat_id"] = (
        p["panchayat_id"]
    )

    values_2025["panchayat_name"] = (
        p["panchayat_name"]
    )

    values_2025["imd_latitude"] = (
        imd_lat
    )

    values_2025["imd_longitude"] = (
        imd_lon
    )


    all_records.append(
        values_2024
    )

    all_records.append(
        values_2025
    )


# ==========================================
# 5. COMBINE
# ==========================================

rainfall = pd.concat(
    all_records,
    ignore_index=True
)


rainfall["date"] = pd.to_datetime(
    rainfall["date"]
)


rainfall = rainfall.sort_values(
    [
        "panchayat_id",
        "date"
    ]
).reset_index(drop=True)


# ==========================================
# 6. SAVE
# ==========================================

rainfall.to_csv(
    OUTPUT_FILE,
    index=False
)


# ==========================================
# 7. REPORT
# ==========================================

print("\n========================================")
print("IMD EXTRACTION COMPLETE")
print("========================================")

print(
    "Rows:",
    len(rainfall)
)

print(
    "Panchayats:",
    rainfall["panchayat_id"]
    .nunique()
)

print(
    "Unique IMD cells:",
    rainfall[
        [
            "imd_latitude",
            "imd_longitude"
        ]
    ]
    .drop_duplicates()
    .shape[0]
)

print("\nUnique grid mapping:")

print(
    rainfall[
        [
            "panchayat_id",
            "panchayat_name",
            "imd_latitude",
            "imd_longitude"
        ]
    ]
    .drop_duplicates()
    .sort_values(
        "panchayat_id"
    )
    .to_string(index=False)
)


print("\nRainfall summary:")

print(
    rainfall
    .groupby(
        "panchayat_name"
    )["rain_mm"]
    .agg(
        [
            "count",
            "mean",
            "std",
            "max"
        ]
    )
    .round(2)
    .to_string()
)


print("\nSaved:")
print(OUTPUT_FILE)


# ==========================================
# 8. CLOSE DATASETS
# ==========================================

ds_2024.close()
ds_2025.close()