from pathlib import Path

import pandas as pd
import rasterio


BASE_DIR = Path(__file__).resolve().parent.parent

IMERG_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "imerg_panchayat_rainfall.csv"
)

PANCHAYAT_FILE = (
    BASE_DIR
    / "data"
    / "panchayats.csv"
)


CHIRPS_BASE = (
    "https://data.chc.ucsb.edu/products/"
    "CHIRPS/v3.0/daily/final/rnl"
)


# ==========================================
# LOAD DATA
# ==========================================

panchayats = pd.read_csv(
    PANCHAYAT_FILE
)

imerg = pd.read_csv(
    IMERG_FILE,
    parse_dates=["date"]
)


# ==========================================
# FIND WETTEST DATES
# ==========================================

daily = (
    imerg
    .groupby("date")["imerg_rain_mm"]
    .max()
    .sort_values(
        ascending=False
    )
)

dates = (
    daily
    .head(5)
    .index
    .tolist()
)


print("========================================")
print("CHIRPS SPATIAL TEST")
print("========================================")

print("\nTesting dates:")

for d in dates:
    print(
        d.date(),
        "IMERG max:",
        round(
            float(daily.loc[d]),
            2
        ),
        "mm"
    )


# ==========================================
# SAMPLE CHIRPS
# ==========================================

all_results = []


for date in dates:

    year = date.year

    date_str = date.strftime(
        "%Y.%m.%d"
    )

    url = (
        f"{CHIRPS_BASE}/{year}/"
        f"chirps-v3.0.rnl.{date_str}.tif"
    )

    print(
        f"\nOpening CHIRPS: {date.date()}"
    )

    with rasterio.open(
        "/vsicurl/" + url
    ) as src:

        print(
            "Resolution:",
            src.res
        )

        for _, p in panchayats.iterrows():

            lon = float(
                p["longitude"]
            )

            lat = float(
                p["latitude"]
            )

            value = next(
                src.sample(
                    [(lon, lat)]
                )
            )[0]

            all_results.append({

                "date":
                    date,

                "panchayat_id":
                    p["panchayat_id"],

                "panchayat_name":
                    p["panchayat_name"],

                "rain_mm":
                    float(value)

            })


# ==========================================
# RESULTS
# ==========================================

result = pd.DataFrame(
    all_results
)


print(
    "\n========================================"
)

print(
    "CHIRPS RESULTS"
)

print(
    "========================================"
)

print(
    result.to_string(
        index=False
    )
)


# ==========================================
# COUNT SPATIAL VARIATION
# ==========================================

print(
    "\nUnique rainfall values per date:"
)

for date, group in result.groupby("date"):

    unique_values = (
        group["rain_mm"]
        .round(4)
        .nunique()
    )

    print(
        date.date(),
        "→",
        unique_values,
        "unique values across 8 Panchayats"
    )


# ==========================================
# SAVE
# ==========================================

output = (
    BASE_DIR
    / "data"
    / "raw"
    / "chirps_spatial_test.csv"
)

result.to_csv(
    output,
    index=False
)

print(
    "\nSaved:",
    output
)