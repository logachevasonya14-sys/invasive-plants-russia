"""
Сбор наблюдений инвазивных видов в России из GBIF и загрузка в MariaDB.

Что изменилось по сравнению с первой версией:
  - постраничная выгрузка (offset) вместо одной страницы в 300 записей;
  - поиск по taxonKey (GBIF сам учитывает синонимы и подвиды);
  - в таблицу добавлены gbif_id (уникальный ключ), регион, месяц, тип записи;
  - повторный запуск не создаёт дубликатов (INSERT IGNORE по gbif_id);
  - вставка пачками (executemany), а не по одной записи.

Запуск:
    python scripts/fetch_data.py            # догрузить данные
    python scripts/fetch_data.py --reset    # пересоздать таблицу с нуля
"""
import argparse
import os
import time

import mysql.connector
import requests
from dotenv import load_dotenv

load_dotenv()

GBIF_SEARCH = "https://api.gbif.org/v1/occurrence/search"
GBIF_MATCH = "https://api.gbif.org/v1/species/match"
PAGE_SIZE = 300          # максимум GBIF на один запрос
GBIF_MAX_OFFSET = 100_000  # лимит GBIF на глубину пагинации в search API

SPECIES_LIST = [
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

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS observations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    gbif_id BIGINT NOT NULL,
    species VARCHAR(255),
    country VARCHAR(100),
    state_province VARCHAR(255),
    lat FLOAT,
    lon FLOAT,
    year INT,
    month INT,
    basis_of_record VARCHAR(50),
    type VARCHAR(50),
    UNIQUE KEY uq_gbif_id (gbif_id)
)
"""

INSERT_SQL = """
INSERT IGNORE INTO observations
    (gbif_id, species, country, state_province, lat, lon, year, month,
     basis_of_record, type)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def get_json(url, params, attempts=3):
    """GET с повторами и нарастающей паузой. Возвращает None, если не вышло."""
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            print(f"  ошибка запроса (попытка {attempt}/{attempts}): {error}")
            time.sleep(5 * attempt)
    return None


def resolve_taxon_key(species_name):
    """Находит taxonKey вида в бэкбоне GBIF."""
    data = get_json(GBIF_MATCH, {"name": species_name, "kingdom": "Plantae"})
    if not data or "usageKey" not in data:
        return None
    if data.get("matchType") != "EXACT":
        print(f"  внимание: {species_name} -> {data.get('scientificName')} "
              f"(matchType={data.get('matchType')}), проверь вручную")
    return data["usageKey"]


def fetch_species(cursor, db, species_name, species_type):
    print(f"\n{species_name}")
    taxon_key = resolve_taxon_key(species_name)
    if taxon_key is None:
        print("  не удалось определить taxonKey, пропускаю")
        return 0

    params = {
        "taxonKey": taxon_key,
        "country": "RU",
        "hasCoordinate": "true",
        "hasGeospatialIssue": "false",
        "occurrenceStatus": "PRESENT",
        "limit": PAGE_SIZE,
        "offset": 0,
    }

    total_seen = 0
    while params["offset"] < GBIF_MAX_OFFSET:
        data = get_json(GBIF_SEARCH, params)
        if data is None:
            print(f"  остановился на offset={params['offset']} из-за ошибок")
            break

        rows = []
        for rec in data.get("results", []):
            lat, lon = rec.get("decimalLatitude"), rec.get("decimalLongitude")
            if lat is None or lon is None or rec.get("key") is None:
                continue
            rows.append((
                rec["key"],
                species_name,
                rec.get("countryCode", "RU"),
                rec.get("stateProvince"),
                lat,
                lon,
                rec.get("year"),
                rec.get("month"),
                rec.get("basisOfRecord"),
                species_type,
            ))

        if rows:
            cursor.executemany(INSERT_SQL, rows)
            db.commit()
        total_seen += len(rows)

        if data.get("endOfRecords", True):
            break
        params["offset"] += PAGE_SIZE
        time.sleep(0.3)  # не долбим API

    print(f"  получено записей: {total_seen}")
    return total_seen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true",
                        help="удалить таблицу observations и создать заново")
    args = parser.parse_args()

    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_FETCH_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )
    cursor = db.cursor()

    if args.reset:
        cursor.execute("DROP TABLE IF EXISTS observations")
        print("Таблица observations удалена.")
    cursor.execute(CREATE_SQL)
    db.commit()

    grand_total = 0
    for name, sp_type in SPECIES_LIST:
        grand_total += fetch_species(cursor, db, name, sp_type)

    cursor.execute("SELECT COUNT(*) FROM observations")
    in_db = cursor.fetchone()[0]
    print(f"\nГотово. Получено за запуск: {grand_total}, всего в таблице: {in_db}")

    cursor.close()
    db.close()


if __name__ == "__main__":
    main()
