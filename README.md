# invasive-plants-russia

ETL-пайплайн для сбора, очистки, хранения и визуализации данных о наблюдениях инвазивных видов растений в России.

## Цель проекта

Проект помогает собрать данные о распространении выбранных инвазивных видов растений из GBIF API, сохранить их в базу данных и визуализировать наблюдения на интерактивной карте.

## Что делает проект

- получает данные о наблюдениях 15 инвазивных видов растений через GBIF API;
- очищает и структурирует данные;
- загружает данные в базу MariaDB;
- формирует датасет для анализа;
- строит интерактивную карту распространения видов.

## Как запустить

```bash
pip install -r requirements.txt
cp .env.example .env            # заполнить доступы к БД
python scripts/fetch_data.py --reset   # первый запуск: пересоздать таблицу и загрузить данные
python scripts/fetch_data.py           # повторные запуски: дубликаты не создаются (уникальный gbif_id)
python scripts/visual.py               # карта -> data/invasive_plants_map.html
```

Таблица `observations`: `gbif_id`, `species`, `country`, `state_province`, `lat`, `lon`, `year`, `month`, `basis_of_record`, `type`.
Данные выгружаются постранично (пагинация GBIF), вид ищется по `taxonKey`, поэтому учитываются синонимы.

## Стек

- Python
- SQL
- MariaDB
- pandas
- requests
- SQLAlchemy
- folium

## Структура проекта

```text
scripts/
  fetch_data.py      # загрузка данных из GBIF API и запись в БД
  visual.py          # генерация интерактивной карты

data/
  output files       # выходные файлы проекта
