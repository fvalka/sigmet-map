import json  # reading geojson files
import time
from urllib.request import urlopen

import matplotlib.pyplot as plt  # plotting data
from adjustText import adjust_text
from descartes import PolygonPatch  # integrating geom object to matplot
from matplotlib.collections import PatchCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from mpl_toolkits.basemap import Basemap
from shapely.geometry import asShape, box, Point  # manipulating geometry
from shapely.ops import transform
from datetime import datetime

# CONSTANTS/CONFIGURATION
MAP_COLOR_LAND = '#FEF9F0'
MAP_COLOR_WATER = '#B0F8FF'
MAP_COLOR_COUNTRIES = '#4E4D4A'
MAP_COLOR_COASTLINES = '#00BCD1'

SIGMET_COLOR = '#D40F67'
SIGMET_ALPHA = 0.3

METAR_COLOR_UNKOWN = '#DAD6CE'
METAR_FLIGHT_CATEGORY_COLORS = {"VFR": '#87F70F',
                                "MVFR": '#046D8B',
                                "IFR": '#FF3D7F',
                                "LIFR": '#E604F9',
                                "?": METAR_COLOR_UNKOWN}
METAR_ALPHA = 0.55

TEXT_REPLACEMENT = {"CONVECTIVE": "Conv"}

t0 = time.time()


def load_json_from_web(url):
    response = urlopen(url)
    response_decoded = response.read().decode("utf-8")
    return json.loads(response_decoded)


# initiate the plot axes
fig = plt.figure(figsize=(12, 12))  # create a figure to contain the plot elements
ax = fig.gca()

# Draw Basemap

# map = Basemap(projection='cyl', urcrnrlon=44, urcrnrlat=72, llcrnrlon=-19, llcrnrlat=33, resolution="i")
# map = Basemap(width=5e6,height=5e6, projection='gnom',lat_0=53.,lon_0=10., resolution="i")
# Europe
# map = Basemap(llcrnrlon=-15, llcrnrlat=30, urcrnrlon=46, urcrnrlat=67,
#              projection='lcc', lat_1=40, lat_2=55, lon_0=10, resolution="i")
# North America
map = Basemap(llcrnrlon=-130, llcrnrlat=5, urcrnrlon=-55, urcrnrlat=70,
              projection='cyl', lat_1=40, lat_2=55, lon_0=-100, resolution="i")
map.drawcoastlines(color=MAP_COLOR_COASTLINES)
map.drawcountries(color=MAP_COLOR_COUNTRIES)
map.drawmapboundary(fill_color=MAP_COLOR_WATER)
map.fillcontinents(color=MAP_COLOR_LAND, lake_color=MAP_COLOR_WATER)

regionBox = box(minx=map.xmin, miny=map.ymin, maxx=map.xmax, maxy=map.ymax)
bbox = str(map.lonmin) + "," + str(map.latmin) + "," + str(map.lonmax) + "," + str(map.latmax)

print("Basemap drawing: " + str(time.time() - t0))
t0 = time.time()

sigmets_international = load_json_from_web("https://www.aviationweather.gov/gis/scripts/IsigmetJSON.php")
sigmets_us = load_json_from_web("https://www.aviationweather.gov/gis/scripts/SigmetJSON.php")
cwa_us = load_json_from_web("https://aviationweather.gov/cgi-bin/json/CwaJSON.php?zoom=4&bbox=" + bbox)

metars = load_json_from_web("https://www.aviationweather.gov/gis/scripts/MetarJSON.php?density=all&bbox=" + bbox)

print("Http access: " + str(time.time() - t0))
t0 = time.time()

# loop through the features plotting polygon centroid
info = []
texts = []
plotting_failed = []


def label_geometry(geom, feat, label_property, text_property):
    # obtain the coordinates of the feature's centroid
    centroid = geom.intersection(regionBox).centroid

    if geom.intersects(regionBox):
        idx = len(info) + 1
        label = feat["properties"][label_property]
        label = TEXT_REPLACEMENT.get(label, label)
        text = label + "\n" + str(idx) + "."
        new_text = ax.text(centroid.x, centroid.y, text, horizontalalignment='center',
                           verticalalignment='center', zorder=50, fontweight="heavy", fontsize=9)
        texts.append(new_text)
        info.append(feat["properties"][text_property])


def plot_features(features, label_property, text_property):
    patches = []
    for feat in features:
        try:
            plot_one_feature(feat, label_property, patches, text_property)
        except ValueError:
            plotting_failed.append(feat['properties'][text_property])

    ax.add_collection(
        PatchCollection(patches, facecolor=SIGMET_COLOR, edgecolor=SIGMET_COLOR,
                        linewidths=1.5, alpha=SIGMET_ALPHA, zorder=40))


def plot_one_feature(feat, label_property, patches, text_property):
    if feat["geometry"]["type"] == "Polygon":
        # convert the geometry to shapely
        geom_raw = asShape(feat["geometry"])
        if len(geom_raw.shell) > 2:
            geom = transform(map, geom_raw.buffer(0))
            patches.append(PolygonPatch(geom))
            label_geometry(geom, feat, label_property, text_property)
    elif feat["geometry"]["type"] == "Point":
        geom = transform(map, Point(feat["geometry"]["coordinates"][0], feat["geometry"]["coordinates"][1]))
        ax.plot(geom.x, geom.y, 'o', color=SIGMET_COLOR, markersize=12, zorder=35)
        label_geometry(geom, feat, label_property, text_property)
    else:
        raise ValueError('Geometry type was neither Polygon nor Point.')


def plot_metars(metar_features):
    for feat in metar_features:
        if feat["geometry"]["type"] == "Point":
            geom = transform(map, Point(feat["geometry"]["coordinates"][0], feat["geometry"]["coordinates"][1]))

            label = feat["properties"].get("fltcat", "?")
            color = METAR_FLIGHT_CATEGORY_COLORS.get(label, METAR_COLOR_UNKOWN)

            ax.plot(geom.x, geom.y, 'o', color=color, markersize=5, zorder=30, alpha=METAR_ALPHA)


plot_features(sigmets_international["features"], "hazard", "rawSigmet")
plot_features(sigmets_us["features"], "hazard", "rawAirSigmet")
plot_features(cwa_us["features"], "hazard", "cwaText")

plot_metars(metars["features"])

adjust_text(texts, ha='center', va='center', expand_text=(0.9, 0.9), autoalign=False,
            on_basemap=True, text_from_points=False,
            arrowprops=dict(arrowstyle='->', color='0.15', shrinkA=3, shrinkB=3, connectionstyle="arc3,rad=0."),
            force_text=(0.8, 0.8))

ax.set_title(datetime.utcnow().strftime("%Y-%m-%d %H:%MZ"), loc='right')

if len(plotting_failed) > 0:
    ax.set_title('WARNING! Some SIGMETs or AIRMETs were not plotted due to errors!', loc='left', fontweight="heavy")


def metar_legend(flight_category):
    return Line2D([0], [0], marker='o', color=METAR_FLIGHT_CATEGORY_COLORS[flight_category],
                  label=flight_category, markersize=8, linestyle='None', alpha=METAR_ALPHA)


legend_elements = [metar_legend('VFR'), metar_legend('MVFR'), metar_legend('IFR'),
                   metar_legend('LIFR'), metar_legend('?'),
                   Patch(facecolor=SIGMET_COLOR, edgecolor=SIGMET_COLOR,
                         label='SIGMETs and AIRMETs', alpha=SIGMET_ALPHA)]

ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.005), ncol=6)

plt.show()

print("Plotting: " + str(time.time() - t0))
t0 = time.time()
