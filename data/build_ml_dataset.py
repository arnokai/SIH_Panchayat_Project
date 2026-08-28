import pandas as pd


# ==========================================
# 1. LOAD DATA
# ==========================================

weather = pd.read_csv(
    "raw/historical_weather.csv",
    parse_dates=["date"]
)

panchayats = pd.read_csv(
    "panchayats.csv"
)


# ==========================================
# 2. MERGE WEATHER + PANCHAYAT FEATURES
# ==========================================

geo_features = panchayats[
    [
        "panchayat_id",
        "latitude",
        "longitude",
        "elevation",
        "distance_to_river_m"
    ]
]

df = weather.merge(
    geo_features,
    on="panchayat_id",
    how="left"
)


# ==========================================
# 3. SORT BY PANCHAYAT + DATE
# ==========================================

df = df.sort_values(
    ["panchayat_id", "date"]
).reset_index(drop=True)


# ==========================================
# 4. CREATE LAG FEATURES
# ==========================================

group = df.groupby("panchayat_id")

df["rain_lag_1"] = group["rain_mm"].shift(1)
df["rain_lag_2"] = group["rain_mm"].shift(2)
df["rain_lag_3"] = group["rain_mm"].shift(3)
df["rain_lag_7"] = group["rain_mm"].shift(7)

df["tmax_lag_1"] = group["tmax_c"].shift(1)
df["tmax_lag_2"] = group["tmax_c"].shift(2)
df["tmax_lag_7"] = group["tmax_c"].shift(7)

df["tmin_lag_1"] = group["tmin_c"].shift(1)
df["tmin_lag_2"] = group["tmin_c"].shift(2)


# ==========================================
# 5. CREATE ROLLING RAINFALL FEATURES
# ==========================================

df["rain_3day_sum"] = (
    group["rain_mm"]
    .transform(lambda x: x.shift(1).rolling(3).sum())
)

df["rain_7day_sum"] = (
    group["rain_mm"]
    .transform(lambda x: x.shift(1).rolling(7).sum())
)


# ==========================================
# 6. CREATE CALENDAR FEATURES
# ==========================================

df["month"] = df["date"].dt.month
df["day_of_year"] = df["date"].dt.dayofyear


# ==========================================
# 7. REMOVE ROWS WITHOUT HISTORY
# ==========================================

df = df.dropna().reset_index(drop=True)


# ==========================================
# 8. SAVE DATASET
# ==========================================

output = "raw/ml_training_dataset.csv"

df.to_csv(
    output,
    index=False
)


# ==========================================
# 9. REPORT
# ==========================================

print("========================================")
print("ML DATASET CREATED")
print("========================================")

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nColumns:")
print(list(df.columns))

print("\nFirst rows:")
print(df.head().to_string(index=False))

print("\nSaved:")
print(output)