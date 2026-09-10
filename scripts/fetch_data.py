import os
import time

import requests
import mysql.connector
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_FETCH_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
)

cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS observations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    species VARCHAR(255),
    country VARCHAR(100),
    lat FLOAT,
    lon FLOAT,
    year INT,
    type VARCHAR(50)
)
""")

db.commit()

species_list = [
    # Травянистые
    ("Reynoutria japonica", "herbaceous"),
    ("Heracleum sosnowskyi", "herbaceous"),
    ("Solidago canadensis", "herbaceous"),
    ("Impatiens parviflora", "herbaceous"),
    ("Ambrosia artemisiifolia", "herbaceous"),
    ("Lupinus polyphyllus", "herbaceous"),
    ("Epilobium adenocaulon", "herbaceous"),
    ("Bidens frondosa", "herbaceous"),
    ("Galinsoga parviflora", "herbaceous"),
    ("Echinocystis lobata", "herbaceous"),

    # Древесные
    ("Acer negundo", "woody"),
    ("Robinia pseudoacacia", "woody"),
    ("Quercus rubra", "woody"),
    ("Elaeagnus angustifolia", "woody"),
    ("Populus canadensis", "woody"),
]


def fetch_species(species_name, species_type=None):
    print(f"Fetching data for {species_name}...")

    url = "https://api.gbif.org/v1/occurrence/search"

    params = {
        "scientificName": species_name,
        "country": "RU",
        "hasCoordinate": True,
        "limit": 300,
    }

    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            break

        except requests.RequestException as error:
            print(
                f"Error fetching data for {species_name} "
                f"(attempt {attempt + 1}): {error}"
            )
            time.sleep(5)

    else:
        print(f"Failed to fetch data for {species_name} after 3 attempts.")
        return

    data = response.json()
    count = 0

    for record in data.get("results", []):
        lat = record.get("decimalLatitude")
        lon = record.get("decimalLongitude")
        year = record.get("year")
        country = record.get("countryCode", "RU")

        if lat is not None and lon is not None:
            cursor.execute(
                """
                INSERT INTO observations (
                    species,
                    country,
                    lat,
                    lon,
                    year,
                    type
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    species_name,
                    country,
                    lat,
                    lon,
                    year,
                    species_type,
                ),
            )

            count += 1

    db.commit()

    print(f"Inserted {count} records for {species_name}.")


for species_name, species_type in species_list:
    fetch_species(species_name, species_type)

print("Готово! Данные загружены в базу :)")

cursor.close()
db.close()