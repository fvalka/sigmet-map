# ----------------------------------------------------------------------
# ------------------------- IMPORT LIBRARIES ---------------------------
import json  # reading geojson files
import matplotlib.pyplot as plt  # plotting data
import math
import random
import numpy as np
from shapely.ops import transform
from matplotlib.collections import PatchCollection
from shapely.geometry import asShape, box, Point, LineString  # manipulating geometry
from descartes import PolygonPatch  # integrating geom object to matplot
from mpl_toolkits.basemap import Basemap
from urllib.request import urlopen
from adjustText import adjust_text


def load_json_from_web(url):
    response = urlopen(url)
    response_decoded = response.read().decode("utf-8")
    return json.loads(response_decoded)



# initiate the plot axes
fig = plt.figure(figsize=(12, 12))  # create a figure to contain the plot elements
ax = fig.gca()

# map = Basemap(projection='cyl', urcrnrlon=44, urcrnrlat=72, llcrnrlon=-19, llcrnrlat=33, resolution="i")
# map = Basemap(width=5e6,height=5e6, projection='gnom',lat_0=53.,lon_0=10., resolution="i")
# Europe
map = Basemap(llcrnrlon=-15, llcrnrlat=30, urcrnrlon=46, urcrnrlat=67,
              projection='lcc', lat_1=40, lat_2=55, lon_0=10, resolution="i")
# North America
map = Basemap(llcrnrlon=-130, llcrnrlat=5, urcrnrlon=-55, urcrnrlat=70,
              projection='cyl', lat_1=40, lat_2=55, lon_0=-100, resolution="i")
map.drawcoastlines(color='#00BCD1')
map.drawcountries(color='#4E4D4A')
map.drawmapboundary(fill_color='#B0F8FF')
map.fillcontinents(color='#FEF9F0', lake_color='#B0F8FF')

regionBox = box(minx=map.xmin, miny=map.ymin, maxx=map.xmax, maxy=map.ymax)

sigmets_international = load_json_from_web("https://www.aviationweather.gov/gis/scripts/IsigmetJSON.php")
sigmets_us = load_json_from_web("https://www.aviationweather.gov/gis/scripts/SigmetJSON.php")

bbox = str(map.lonmin) + "," + str(map.latmin) + "," + str(map.lonmax) + "," + str(map.latmax)
metars = load_json_from_web("https://www.aviationweather.gov/gis/scripts/MetarJSON.php?density=all&bbox=" + bbox)

# loop through the features plotting polygon centroid
info = []
texts = []


def plot_features(features, label_property, text_property):
    patches = []
    for feat in features:
        if feat["geometry"]["type"] == "Polygon":
            # convert the geometry to shapely
            geom = transform(map, asShape(feat["geometry"]))
            # obtain the coordinates of the feature's centroid
            centroid = geom.centroid

            patches.append(PolygonPatch(geom))

            if geom.intersects(regionBox):
                idx = len(info)
                text = feat["properties"][label_property] + "\n" + str(idx) + "."
                new_text = ax.text(centroid.x, centroid.y, text, horizontalalignment='center',
                                   verticalalignment='center', zorder=50, fontweight="heavy", fontsize=9)
                texts.append(new_text)
                info.append(feat["properties"][text_property])

    ax.add_collection(
        PatchCollection(patches, facecolor='#D40F67', edgecolor='#D40F67', linewidths=1.5, alpha=0.3, zorder=40))


def plot_metars(metar_features):
    for feat in metar_features:
        if feat["geometry"]["type"] == "Point":
            geom = transform(map, Point(feat["geometry"]["coordinates"][0], feat["geometry"]["coordinates"][1]))

            flight_cat_colors = { "VFR": "#87F70F", "MVFR": "#046D8B", "IFR": "#FF3D7F", "LIFR": "#8808BB"}
            color = flight_cat_colors.get(feat["properties"].get("fltcat", "?"), "#DAD6CE")

            ax.plot(geom.x, geom.y, 'o', color=color, markersize=6, zorder=30, alpha=0.5)


plot_features(sigmets_international["features"], "hazard", "rawSigmet")
plot_features(sigmets_us["features"], "hazard", "rawAirSigmet")

plot_metars(metars["features"])

adjust_text(texts, ha='center', va='center', expand_text=(1.05, 1), autoalign=False,
            on_basemap=True, text_from_points=False, arrowprops=dict(arrowstyle='->', color='red'))

# plt.savefig("data\siaya_wards.png")
plt.show()
