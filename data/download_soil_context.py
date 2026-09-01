import os
import time

import pandas as pd
import requests


# ============================================================
# TERRAMIND — PANCHAYAT SOIL CONTEXT
# ============================================================
#
# Source:
#   ISRIC SoilGrids
#
# We collect raw soil texture measurements first.
# We do NOT immediately convert them into a "sandy/not-sandy"
# label. Classification will be a separate step.
#
# Depth:
#   0–5 cm
#
# Properties:
#   sand
#   clay
#   silt
#
# ============================================================


SOILGRIDS_URL = (
    "https://rest.isric.org/"
    "soilgrids/v2.0/properties/query"
)

COORDINATE_FILE = (
    "data/raw/panchayat_coordinates.csv"
)

OUTPUT_FILE = (
    "data/raw/panchayat_soil_features.csv"
)

DEPTH = "0-5cm"

PROPERTIES = [
    "sand",
    "clay",
    "silt",
]


# ============================================================
# START
# ============================================================

print(
    "========================================"
)

print(
    "TERRAMIND PANCHAYAT SOIL CONTEXT"
)

print(
    "========================================"
)


# ============================================================
# LOAD COORDINATES
# ============================================================

coords = pd.read_csv(
    COORDINATE_FILE
)


required_columns = [
    "GPCODE",
    "GPNAME",
    "latitude",
    "longitude",
]


missing = [
    column
    for column in required_columns
    if column not in coords.columns
]


if missing:

    raise ValueError(
        "Missing coordinate columns: "
        +
        ", ".join(missing)
    )


# ============================================================
# DOWNLOAD
# ============================================================

records = []


for _, row in coords.iterrows():

    panchayat_id = str(
        row["GPCODE"]
    )

    panchayat_name = str(
        row["GPNAME"]
    )

    latitude = float(
        row["latitude"]
    )

    longitude = float(
        row["longitude"]
    )


    print(
        f"\nQuerying SoilGrids for "
        f"{panchayat_name}..."
    )


    record = {

        "panchayat_id":
            panchayat_id,

        "panchayat_name":
            panchayat_name,

        "latitude":
            latitude,

        "longitude":
            longitude,

        "depth":
            DEPTH,

        "source":
            "ISRIC SoilGrids",

    }


    for property_name in PROPERTIES:

        params = {

            "lon":
                longitude,

            "lat":
                latitude,

            "property":
                property_name,

            "depth":
                DEPTH,

            "value":
                "mean",

        }


        try:

            response = requests.get(
                SOILGRIDS_URL,
                params=params,
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

        except requests.RequestException as exc:

            raise RuntimeError(
                f"SoilGrids request failed for "
                f"{panchayat_name} "
                f"({property_name}): {exc}"
            ) from exc


        # ----------------------------------------------------
        # Extract SoilGrids value
        # ----------------------------------------------------

        try:

            layer = (
                data[
                    "properties"
                ][
                    "layers"
                ][0]
            )

            value = (
                layer[
                    "depths"
                ][0][
                    "values"
                ][
                    "mean"
                ]
            )

        except (
            KeyError,
            IndexError,
            TypeError
        ) as exc:

            raise ValueError(
                f"Unexpected SoilGrids response "
                f"for {panchayat_name}, "
                f"property={property_name}"
            ) from exc


        # ----------------------------------------------------
        # SoilGrids reports g/kg with a d_factor of 10
        # for conversion to %
        # ----------------------------------------------------

        value_percent = (
            float(value) / 10.0
        )


        record[
            f"{property_name}_pct"
        ] = value_percent


        time.sleep(0.2)


    records.append(record)


    print(
        "Sand:",
        round(
            record["sand_pct"],
            1
        ),
        "% | Clay:",
        round(
            record["clay_pct"],
            1
        ),
        "% | Silt:",
        round(
            record["silt_pct"],
            1
        ),
        "%"
    )


# ============================================================
# DATAFRAME
# ============================================================

soil = pd.DataFrame(
    records
)


# ============================================================
# VALIDATION
# ============================================================

print(
    "\n========================================"
)

print(
    "VALIDATING SOIL DATA"
)

print(
    "========================================"
)


if len(soil) != len(coords):

    raise ValueError(
        f"Expected {len(coords)} Panchayats, "
        f"got {len(soil)}."
    )


if soil.duplicated(
    subset=["panchayat_id"]
).any():

    raise ValueError(
        "Duplicate Panchayat IDs found."
    )


for column in [
    "sand_pct",
    "clay_pct",
    "silt_pct",
]:

    if soil[column].isna().any():

        raise ValueError(
            f"Missing values in {column}."
        )


    if (
        (
            soil[column] < 0
        )
        |
        (
            soil[column] > 100
        )
    ).any():

        raise ValueError(
            f"Invalid percentage in {column}."
        )


# ============================================================
# SAVE
# ============================================================

os.makedirs(
    "data/raw",
    exist_ok=True
)


soil.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print(
    "\n========================================"
)

print(
    "SOIL CONTEXT CREATED"
)

print(
    "========================================"
)

print(
    "Panchayats:",
    len(soil)
)

print(
    "Depth:",
    DEPTH
)

print(
    "\nSoil measurements:"
)

print(
    soil[
        [
            "panchayat_id",
            "panchayat_name",
            "sand_pct",
            "clay_pct",
            "silt_pct",
        ]
    ]
    .round(1)
    .to_string(index=False)
)

print(
    "\nSaved:"
)

print(
    OUTPUT_FILE
)