import pandas as pd

# ==========================================
# 1. LOAD FILES
# ==========================================

panchayats = pd.read_csv("panchayats.csv")
features = pd.read_csv("raw/panchayat_features.csv")

print("Original Panchayat columns:")
print(list(panchayats.columns))

print("\nFeature columns:")
print(list(features.columns))


# ==========================================
# 2. NORMALIZE NAMES
# ==========================================

panchayats["panchayat_name"] = (
    panchayats["panchayat_name"]
    .astype(str)
    .str.strip()
    .str.upper()
)

features["GPNAME"] = (
    features["GPNAME"]
    .astype(str)
    .str.strip()
    .str.upper()
)


# ==========================================
# 3. CREATE LOOKUP TABLE
# ==========================================

lookup = features[
    [
        "GPNAME",
        "latitude",
        "longitude",
        "elevation"
    ]
].copy()

lookup = lookup.rename(
    columns={
        "GPNAME": "panchayat_name"
    }
)


# ==========================================
# 4. MERGE DATA
# ==========================================

panchayats = panchayats.drop(
    columns=["latitude", "longitude", "elevation"],
    errors="ignore"
)

panchayats = panchayats.merge(
    lookup,
    on="panchayat_name",
    how="left"
)


# ==========================================
# 5. CHECK RESULTS
# ==========================================

required_columns = [
    "latitude",
    "longitude",
    "elevation"
]

missing = panchayats[
    required_columns
].isna().any(axis=1)

if missing.any():
    print("\nWARNING: Some Panchayats are missing data:")
    print(
        panchayats.loc[
            missing,
            ["panchayat_name"]
        ].to_string(index=False)
    )
else:
    print("\nAll Panchayats matched successfully.")


# ==========================================
# 6. SHOW FINAL TABLE
# ==========================================

print("\nFINAL PANCHAYAT TABLE")
print("----------------------------------------")

print(
    panchayats.to_string(index=False)
)


# ==========================================
# 7. SAVE
# ==========================================

panchayats.to_csv(
    "panchayats.csv",
    index=False
)

print("\nSaved: panchayats.csv")