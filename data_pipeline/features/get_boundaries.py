import requests

url = "https://mapservice.gov.in/mapserviceserv176/rest/services/Panchayat/AdminGPHierarchy/MapServer/3/query"

params = {
    "where": "blklgdcode='2723'",
    "outFields": "GPCODE,GPNAME,STNAME,DTNAME,blkname,blklgdcode",
    "returnGeometry": "true",
    "outSR": "4326",
    "f": "geojson"
}

response = requests.get(
    url,
    params=params,
    timeout=60,
    verify=False
)

response.raise_for_status()

data = response.json()

print("Number of GP records:", len(data.get("features", [])))

with open("raw/amdanga_gps.geojson", "w", encoding="utf-8") as file:
    file.write(response.text)

for feature in data.get("features", []):
    print(
        feature["properties"]["GPCODE"],
        "-",
        feature["properties"]["GPNAME"]
    )

print("\nSaved to raw/amdanga_gps.geojson")