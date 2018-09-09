import json  # reading geojson files
from urllib.request import urlopen

import matplotlib.pyplot as plt  # plotting data
from adjustText import adjust_text
from descartes import PolygonPatch  # integrating geom object to matplot
from matplotlib.collections import PatchCollection
from mpl_toolkits.basemap import Basemap
from shapely.geometry import asShape, box, Point  # manipulating geometry
from shapely.ops import transform

# ------------------------- LOAD THE DATA -----------------------------
# data = json.load(open("sigmet.json")) # from data folder.

response = urlopen("https://www.aviationweather.gov/gis/scripts/IsigmetJSON.php")
response_decoded = response.read().decode("utf-8")
data = json.loads(response_decoded)

# initiate the plot axes
fig = plt.figure(figsize=(16, 16))  # create a figure to contain the plot elements
ax = fig.gca()

# map = Basemap(projection='cyl', urcrnrlon=44, urcrnrlat=72, llcrnrlon=-19, llcrnrlat=33, resolution="i")
# map = Basemap(width=5e6,height=5e6, projection='gnom',lat_0=53.,lon_0=10., resolution="i")
# Europe
map = Basemap(llcrnrlon=-15, llcrnrlat=30, urcrnrlon=46, urcrnrlat=67,
              projection='lcc', lat_1=40, lat_2=55, lon_0=10, resolution="i")
# North America
# map = Basemap(llcrnrlon=-130,llcrnrlat=5,urcrnrlon=-55,urcrnrlat=70,
#              projection='cyl',lat_1=40,lat_2=55,lon_0=-100, resolution="c")
map.drawcoastlines(color='#00BCD1')
map.drawcountries(color='#4E4D4A')
map.drawmapboundary(fill_color='#B0F8FF')
map.fillcontinents(color='#FEF9F0', lake_color='#B0F8FF')

regionBox = box(minx=map.xmin, miny=map.ymin, maxx=map.xmax, maxy=map.ymax)

# loop through the features plotting polygon centroid
patches = []
info = []
texts = []

for feat in data["features"]:
    if feat["geometry"]["type"] == "Polygon":
        # convert the geometry to shapely
        geom = asShape(feat["geometry"])
        # obtain the coordinates of the feature's centroid
        x, y = geom.centroid.x, geom.centroid.y
        x_conv, y_conv = map(x, y)
        centroid_conv = Point(x_conv, y_conv)

        geom_conv = transform(map, geom)

        patches.append(PolygonPatch(geom_conv))

        if regionBox.contains(centroid_conv):
            idx = len(info)
            text = feat["properties"]["hazard"] + "\n" + str(idx) + "."
            new_text = ax.text(x_conv, y_conv, text, horizontalalignment='center',
                               verticalalignment='center', zorder=5, fontweight="heavy", fontsize=10)
            texts.append(new_text)
            info.append(feat["properties"]["rawSigmet"])

ax.add_collection(
    PatchCollection(patches, facecolor='#D40F67', edgecolor='#D40F67', linewidths=1.5, alpha=0.3, zorder=4))
adjust_text(texts, ha='center', va='center', expand_text=(1.05, 1), autoalign=False,
            on_basemap=True, text_from_points=False)

ax.clear()  # clear the axes memory
# plt.savefig("data\siaya_wards.png")
plt.show()
