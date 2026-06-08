import requests
import mysql.connector
import pandas as pd
import time
db = mysql.connector.connect(
    host="localhost",
    user="plantuser",
    password="plantspass123",
    database="invasive_plants"
    )
cursor = db.cursor()
cursor.execute("""create table if not exists observations (
    id int auto_increment primary key,
    species varchar(255),
    country varchar(100),
    lat float,
    lon float,
    year int,
    type varchar(50)
)""")
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
        "limit": 300
    }
    for attempt in range(3):
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Поднять ошибку при HTML ошибке
            break
        except requests.RequestException as e:
            print(f"Error fetching data for {species_name} (attempt {attempt + 1}): {e}")
            time.sleep(5)  # Ждем 5 секунд перед повторной попыткой
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
        if lat and lon:
            cursor.execute("INSERT INTO observations (species, country, lat, lon, year, type) VALUES (%s, %s, %s, %s, %s, %s)",
                           (species_name, country, lat, lon, year, species_type))
            count += 1
    db.commit()
    print(f"Inserted {count} records for {species_name}.")
for species_name, species_type in species_list:
    fetch_species(species_name, species_type)
print("Готово! Данные загружены в базу :)")
db.close()