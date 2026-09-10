import os
import pandas as pd
import folium
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

load_dotenv()

database_url = URL.create(
    "mysql+pymysql",
    username=os.getenv("DB_VISUAL_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(database_url)
df = pd.read_sql("SELECT * FROM observations", engine)
print(f"Загружено {len(df)} записей из базы данных.")
print(df.groupby("species")["id"].count())
m = folium.Map(location=[60, 90], zoom_start=3)
colors = {
    "Reynoutria japonica": "red",
    "Heracleum sosnowskyi": "blue",
    "Solidago canadensis": "green",
    "Impatiens parviflora": "orange",
    "Acer negundo": "purple",
    "Robinia pseudoacacia": "cyan",
    "Quercus rubra": "magenta",
    "Elaeagnus angustifolia": "yellow",
    "Populus canadensis": "brown",
    "Lupinus polyphyllus": "pink",
    "Epilobium adenocaulon": "gray",
    "Bidens frondosa": "lime",
    "Galinsoga parviflora": "lightblue",
    "Echinocystis lobata": "lightgreen",
    "Ambrosia artemisiifolia": "coral"

}
for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=3,
        color=colors.get(row["species"], "gray"),
        fill=True,
        fill_color=colors.get(row["species"], "gray"),
        fill_opacity=0.7,
        popup=f"{row['species']} ({row['year']})"
    ).add_to(m)
legend_html = """
<div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000; 
background-color: white; padding: 10px; border-radius: 5px; border: 1px solid grey;">
<b>Инвазивные растения России</b><br>
<i style="background:red; width:12px; height:12px; display:inline-block; border-radius:50%"></i> Reynoutria japonica<br>
<i style="background:blue; width:12px; height:12px; display:inline-block; border-radius:50%"></i> Heracleum sosnowskyi<br>
<i style="background:green; width:12px; height:12px; display:inline-block; border-radius:50%"></i> Solidago canadensis<br>
<i style="background:orange; width:12px; height:12px; display:inline-block; border-radius:50%"></i> Impatiens parviflora<br>
<i style="background:purple; width:12px; height:12px; display:inline-block; border-radius:50%"></i> Acer negundo<br>
<i style="background:cyan; width:12px; height:12px; display:inline-block; border-radius:50%"></i> Robinia pseudoacacia<br>
<i style="background:magenta; width:12px; height:12px; display:inline-block; border-radius:50%"></i> Quercus rubra<br>
<i style="background:yellow; width:12px; height:12px; display:inline-block; border-radius:50%"></i> Elaeagnus angustifolia<br>
<i style="background:brown; width:12px; height:12px; display:inline-block; border-radius:50%"></i> Populus canadensis<br>
<i style="background:pink; width:12px; height:12px; display:inline-block; border-radius:50%"></i> Lupinus polyphyllus<br>
<i style="background:gray; width:12px; height:12px; display:inline-block; border-radius:50%"></i> Epilobium adenocaulon<br>
<i style="background:lime; width:12px; height:12px; display:inline-block; border-radius:50%"></i> Bidens frondosa<br>
<i style="background:lightblue; width:12px; height:12px; display:inline-block; border-radius:50%"></i> Galinsoga parviflora<br>
<i style="background:lightgreen; width:12px; height:12px; display:inline-block; border-radius:50%"></i> Echinocystis lobata<br>
<i style="background:coral; width:12px; height:12px; display:inline-block; border-radius:50%"></i> Ambrosia artemisiifolia<br>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))
m.save("data/invasive_plants_map.html")
print("Карта сохранена в data/invasive_plants_map.html")