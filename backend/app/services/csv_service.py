from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[3]      # project root
CSV_PATH = ROOT / "data" / "raw" / "panchayat_coordinates.csv"

def get_all_panchayats():
    panchayats = []

    with CSV_PATH.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            panchayats.append({
                "id": row["GPCODE"],
                "name": row["GPNAME"],
                "district": "North 24 Parganas"
            })

    return panchayats