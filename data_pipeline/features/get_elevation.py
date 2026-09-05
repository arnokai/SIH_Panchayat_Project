import requests
import pandas as pd

# ==========================================
# 1. LOAD PANCHAYAT COORDINATES
# ==========================================

input_file = "raw/panchayat_coordinates.csv"

df = pd.read_csv(input_file)

print("Loaded Panchayats:", len(df))


# ==========================================
# 2. PREPARE COORDINATES
# ==========================================

latitudes = ",".join(df["latitude"].astype(str))
longitudes = ",".join(df["longitude"].astype(str))


# ==========================================
# 3. REQUEST ELEVATION FROM DEM
# ==========================================

url = "https://api.open-meteo.com/v1/elevation"

params = {
    "latitude": latitudes,
    "longitude": longitudes
}

response = requests.get(
    url,
    params=params,
    timeout=60
)

response.raise_for_status()

data = response.json()


# ==========================================
# 4. ADD ELEVATION TO DATA
# ==========================================

df["elevation"] = data["elevation"]


# ==========================================
# 5. DISPLAY RESULTS
# ==========================================

print("\nPanchayat elevation:")

print(
    df[
        ["GPCODE", "GPNAME", "latitude", "longitude", "elevation"]
    ].to_string(index=False)
)


# ==========================================
# 6. SAVE RESULT
# ==========================================

output_file = "raw/panchayat_features.csv"

df.to_csv(
    output_file,
    index=False
)

print("\nSaved:", output_file)