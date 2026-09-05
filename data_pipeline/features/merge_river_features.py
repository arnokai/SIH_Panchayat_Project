import pandas as pd

# Load master Panchayat table
panchayats = pd.read_csv("panchayats.csv")

# Load river features
river = pd.read_csv("raw/panchayat_river_features.csv")


# Normalize names before matching
panchayats["panchayat_name"] = (
    panchayats["panchayat_name"]
    .astype(str)
    .str.strip()
    .str.upper()
)

river["GPNAME"] = (
    river["GPNAME"]
    .astype(str)
    .str.strip()
    .str.upper()
)


# Keep only the river information we need
river = river[
    [
        "GPNAME",
        "nearest_river",
        "distance_to_river_m"
    ]
].rename(
    columns={
        "GPNAME": "panchayat_name"
    }
)


# Remove old columns if the script is run again
panchayats = panchayats.drop(
    columns=["nearest_river", "distance_to_river_m"],
    errors="ignore"
)


# Merge
panchayats = panchayats.merge(
    river,
    on="panchayat_name",
    how="left"
)


# Check for missing values
missing = panchayats[
    ["nearest_river", "distance_to_river_m"]
].isna().any(axis=1)

if missing.any():
    print("WARNING: Missing river data:")
    print(
        panchayats.loc[
            missing,
            ["panchayat_name"]
        ].to_string(index=False)
    )
else:
    print("All Panchayats matched with river data.")


# Show final table
print("\nMASTER PANCHAYAT TABLE")
print("----------------------------------------")
print(panchayats.to_string(index=False))


# Save
panchayats.to_csv(
    "panchayats.csv",
    index=False
)

print("\nSaved: panchayats.csv")