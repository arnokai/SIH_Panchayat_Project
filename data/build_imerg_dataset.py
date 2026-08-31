from pathlib import Path

import pandas as pd
import xarray as xr


# ==========================================
# 1. PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

IMerg_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "imerg"
)

PANCHAYAT_FILE = (
    BASE_DIR
    / "data"
    / "panchayats.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "imerg_panchayat_rainfall.csv"
)


# ==========================================
# 2. LOAD PANCHAYATS
# ==========================================

panchayats = pd.read_csv(
    PANCHAYAT_FILE
)

print("========================================")
print("BUILDING IMERG PANCHAYAT DATASET")
print("========================================")

print(
    "Panchayats:",
    len(panchayats)
)


# ==========================================
# 3. FIND IMERG FILES
# ==========================================

files = sorted(
    IMerg_DIR.glob("*.nc4")
)

print(
    "IMERG files:",
    len(files)
)


if len(files) == 0:

    raise FileNotFoundError(
        f"No .nc4 files found in {IMerg_DIR}"
    )


# ==========================================
# 4. READ FIRST FILE
# ==========================================

with xr.open_dataset(
    files[0],
    engine="netcdf4"
) as ds:

    lats = ds["lat"].values
    lons = ds["lon"].values


print("\nIMERG grid:")
print(
    "Latitudes:",
    lats
)

print(
    "Longitudes:",
    lons
)


# ==========================================
# 5. CREATE PANCHAYAT → GRID MAPPING
# ==========================================

mapping = []

for _, p in panchayats.iterrows():

    p_lat = float(
        p["latitude"]
    )

    p_lon = float(
        p["longitude"]
    )

    nearest_lat = float(
        lats[
            abs(lats - p_lat).argmin()
        ]
    )

    nearest_lon = float(
        lons[
            abs(lons - p_lon).argmin()
        ]
    )

    mapping.append({

        "panchayat_id":
            p["panchayat_id"],

        "panchayat_name":
            p["panchayat_name"],

        "panchayat_latitude":
            p_lat,

        "panchayat_longitude":
            p_lon,

        "imerg_latitude":
            nearest_lat,

        "imerg_longitude":
            nearest_lon
    })


mapping_df = pd.DataFrame(
    mapping
)


print("\n========================================")
print("PANCHAYAT → IMERG MAPPING")
print("========================================")

print(
    mapping_df.to_string(
        index=False
    )
)


# ==========================================
# 6. READ ALL DAILY FILES
# ==========================================

all_records = []


for index, file_path in enumerate(
    files,
    start=1
):

    print(
        f"\rReading file "
        f"{index}/{len(files)}",
        end=""
    )

    with xr.open_dataset(
        file_path,
        engine="netcdf4"
    ) as ds:

        precipitation = (
            ds["precipitation"]
            .squeeze("time")
        )

        date = pd.Timestamp(
    ds["time"].values[0]
)

        # Convert the 2 x 2 grid into
        # a normal DataFrame.

        grid = (
            precipitation
            .to_dataframe(
                name="precipitation"
            )
            .reset_index()
        )

        grid["date"] = date

        all_records.append(
            grid[
                [
                    "date",
                    "lon",
                    "lat",
                    "precipitation"
                ]
            ]
        )


print()


# ==========================================
# 7. COMBINE GRID DATA
# ==========================================

grid_df = pd.concat(
    all_records,
    ignore_index=True
)


# ==========================================
# 8. CREATE PANCHAYAT SERIES
# ==========================================

panchayat_records = []


for _, p in mapping_df.iterrows():

    selected = grid_df[
        (
            grid_df["lat"]
            ==
            p["imerg_latitude"]
        )
        &
        (
            grid_df["lon"]
            ==
            p["imerg_longitude"]
        )
    ].copy()


    selected["panchayat_id"] = (
        p["panchayat_id"]
    )

    selected["panchayat_name"] = (
        p["panchayat_name"]
    )

    selected["panchayat_latitude"] = (
        p["panchayat_latitude"]
    )

    selected["panchayat_longitude"] = (
        p["panchayat_longitude"]
    )


    panchayat_records.append(
        selected
    )


result = pd.concat(
    panchayat_records,
    ignore_index=True
)


# ==========================================
# 9. CLEAN COLUMN ORDER
# ==========================================

result = result[
    [
        "date",
        "panchayat_id",
        "panchayat_name",
        "panchayat_latitude",
        "panchayat_longitude",
        "lat",
        "lon",
        "precipitation"
    ]
]


result = result.rename(
    columns={
        "lat":
            "imerg_latitude",

        "lon":
            "imerg_longitude",

        "precipitation":
            "imerg_rain_mm"
    }
)


result = result.sort_values(
    [
        "panchayat_id",
        "date"
    ]
).reset_index(drop=True)


# ==========================================
# 10. SAVE
# ==========================================

result.to_csv(
    OUTPUT_FILE,
    index=False
)


# ==========================================
# 11. REPORT
# ==========================================

print("\n========================================")
print("IMERG PANCHAYAT DATASET CREATED")
print("========================================")

print(
    "Rows:",
    len(result)
)

print(
    "Panchayats:",
    result["panchayat_id"]
    .nunique()
)

print(
    "Dates:",
    result["date"].min().date(),
    "to",
    result["date"].max().date()
)

print(
    "Unique IMERG grid cells:",
    result[
        [
            "imerg_latitude",
            "imerg_longitude"
        ]
    ]
    .drop_duplicates()
    .shape[0]
)


print("\nGrid mapping:")
print(
    mapping_df[
        [
            "panchayat_id",
            "panchayat_name",
            "imerg_latitude",
            "imerg_longitude"
        ]
    ]
    .to_string(index=False)
)


# ==========================================
# 12. RAINFALL SUMMARY
# ==========================================

print(
    "\nRainfall summary:"
)

print(
    result
    .groupby("panchayat_name")
    ["imerg_rain_mm"]
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
# 13. UNIQUE DAILY SERIES
# ==========================================

pivot = result.pivot(
    index="date",
    columns="panchayat_id",
    values="imerg_rain_mm"
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


print("\nSaved:")
print(OUTPUT_FILE)