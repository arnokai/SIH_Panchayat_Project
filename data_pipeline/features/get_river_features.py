import geopandas as gpd
import pandas as pd


# -----------------------------
# 1. Load Panchayat coordinates
# -----------------------------

panchayats = pd.read_csv("raw/panchayat_features.csv")

panchayat_gdf = gpd.GeoDataFrame(
    panchayats,
    geometry=gpd.points_from_xy(
        panchayats["longitude"],
        panchayats["latitude"]
    ),
    crs="EPSG:4326"
)


# -----------------------------
# 2. Load river dataset
# -----------------------------

rivers = gpd.read_file(
    "raw/rivers/ne_50m_rivers_lake_centerlines.shp"
)

print("River features loaded:", len(rivers))


# -----------------------------
# 3. Convert to UTM Zone 45N
# -----------------------------

panchayat_gdf = panchayat_gdf.to_crs("EPSG:32645")
rivers = rivers.to_crs("EPSG:32645")


# -----------------------------
# 4. Find nearest river
# -----------------------------

nearest = gpd.sjoin_nearest(
    panchayat_gdf,
    rivers[["name", "geometry"]],
    how="left",
    distance_col="distance_to_river_m"
)


# -----------------------------
# 5. Keep useful columns
# -----------------------------

result = nearest[
    [
        "GPCODE",
        "GPNAME",
        "latitude",
        "longitude",
        "elevation",
        "name",
        "distance_to_river_m"
    ]
].copy()


result = result.rename(
    columns={
        "name": "nearest_river"
    }
)


# -----------------------------
# 6. Display results
# -----------------------------

print("\nPanchayat river features:")
print(result.to_string(index=False))


# -----------------------------
# 7. Save results
# -----------------------------

result.to_csv(
    "raw/panchayat_river_features.csv",
    index=False
)

print("\nSaved: raw/panchayat_river_features.csv")