from pathlib import Path

import pandas as pd
import rasterio


# ==========================================
# 1. PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

PANCHAYAT_FILE = (
    BASE_DIR
    / "data"
    / "panchayats.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "chirps_panchayat_rainfall.csv"
)


# ==========================================
# 2. SETTINGS
# ==========================================

CHIRPS_BASE = (
    "https://data.chc.ucsb.edu/products/"
    "CHIRPS/v3.0/daily/final/rnl"
)


START_DATE = "2024-01-01"
END_DATE = "2025-09-30"


# ==========================================
# 3. LOAD PANCHAYATS
# ==========================================

panchayats = pd.read_csv(
    PANCHAYAT_FILE
)


dates = pd.date_range(
    START_DATE,
    END_DATE,
    freq="D"
)


print("========================================")
print("BUILDING CHIRPS PANCHAYAT DATASET")
print("========================================")

print(
    "Panchayats:",
    len(panchayats)
)

print(
    "Dates:",
    len(dates)
)

print(
    "Expected rows:",
    len(panchayats) * len(dates)
)


# ==========================================
# 4. EXTRACT DAILY VALUES
# ==========================================

records = []

total = len(dates)


for index, date in enumerate(
    dates,
    start=1
):

    year = date.year

    date_string = date.strftime(
        "%Y.%m.%d"
    )

    url = (
        f"{CHIRPS_BASE}/"
        f"{year}/"
        f"chirps-v3.0.rnl."
        f"{date_string}.tif"
    )

    print(
        f"\rReading CHIRPS "
        f"{index}/{total}",
        end=""
    )

    try:

        with rasterio.open(
            "/vsicurl/" + url
        ) as src:

            coordinates = [
                (
                    float(p["longitude"]),
                    float(p["latitude"])
                )
                for _, p in panchayats.iterrows()
            ]

            sampled = list(
                src.sample(coordinates)
            )


            for (
                (_, p),
                value
            ) in zip(
                panchayats.iterrows(),
                sampled
            ):

                rainfall = float(
                    value[0]
                )

                records.append({

                    "date":
                        date,

                    "panchayat_id":
                        p["panchayat_id"],

                    "panchayat_name":
                        p["panchayat_name"],

                    "latitude":
                        float(
                            p["latitude"]
                        ),

                    "longitude":
                        float(
                            p["longitude"]
                        ),

                    "chirps_rain_mm":
                        rainfall
                })


    except Exception as e:

        print()

        print(
            f"\nERROR on {date.date()}:"
        )

        print(e)

        raise


print()


# ==========================================
# 5. CREATE DATAFRAME
# ==========================================

result = pd.DataFrame(
    records
)


result["date"] = pd.to_datetime(
    result["date"]
)


result = result.sort_values(
    [
        "panchayat_id",
        "date"
    ]
).reset_index(drop=True)


# ==========================================
# 6. CHECK ROW COUNT
# ==========================================

expected_rows = (
    len(panchayats)
    *
    len(dates)
)


if len(result) != expected_rows:

    raise ValueError(
        f"Expected {expected_rows} rows "
        f"but got {len(result)}."
    )


# ==========================================
# 7. CHECK MISSING VALUES
# ==========================================

missing = (
    result
    .isna()
    .sum()
)


print("\n========================================")
print("DATA QUALITY")
print("========================================")

print(
    missing.to_string()
)


if missing.sum() > 0:

    raise ValueError(
        "Missing values detected."
    )


# ==========================================
# 8. SAVE
# ==========================================

result.to_csv(
    OUTPUT_FILE,
    index=False
)


# ==========================================
# 9. SUMMARY
# ==========================================

print("\n========================================")
print("CHIRPS DATASET CREATED")
print("========================================")

print(
    "Rows:",
    len(result)
)

print(
    "Panchayats:",
    result["panchayat_id"].nunique()
)

print(
    "Dates:",
    result["date"].min().date(),
    "to",
    result["date"].max().date()
)


print("\nRainfall summary:")

print(
    result
    .groupby("panchayat_name")
    ["chirps_rain_mm"]
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


# ==========================================
# 10. UNIQUE SERIES
# ==========================================

pivot = result.pivot(
    index="date",
    columns="panchayat_id",
    values="chirps_rain_mm"
)


unique_series = (
    pivot.T
    .drop_duplicates()
    .shape[0]
)


print(
    "\nUnique daily rainfall series:",
    unique_series,
    "out of",
    len(panchayats)
)


print(
    "\nSaved:"
)

print(
    OUTPUT_FILE
)