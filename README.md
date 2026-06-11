# invasive-plants-russia
ETL pipeline for invasive plant species distribution analysis in Russia

## Что делает
- Качает данные о наблюдениях с GBIF API (15 видов, 4000+ записей)
- Загружает в базу данных MariaDB
- Строит интерактивную карту распространения видов

## Стек
Python, SQL, MariaDB, pandas, requests, folium, SQLAlchemy

## Структура
scripts/fetch_data.py   - загрузка данных с API в БД
scripts/visual.py       - генерация карты
data/                   - выходные файлы
