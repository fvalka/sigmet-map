import json  # reading geojson files
import time
from multiprocessing.pool import ThreadPool
from urllib.request import urlopen

import matplotlib.pyplot as plt  # plotting data
from mpl_toolkits.basemap import Basemap
from shapely.geometry import box  # manipulating geometry

# CONSTANTS/CONFIGURATION
from Configuration import MAP_COLOR_LAND, MAP_COLOR_WATER, MAP_COLOR_COUNTRIES, MAP_COLOR_COASTLINES
from model import PlotDefinition, Features
from plot_features import PlotFeatures

t0 = time.time()


def load_json_from_web(url):
    response = urlopen(url)
    response_decoded = response.read().decode("utf-8")
    return url, json.loads(response_decoded)


# initiate the plot axes
fig = plt.figure(figsize=(12, 12))  # create a figure to contain the plot elements
ax = fig.gca()

# Draw Basemap

# map = Basemap(projection='cyl', urcrnrlon=44, urcrnrlat=72, llcrnrlon=-19, llcrnrlat=33, resolution="i")
# map = Basemap(width=5e6,height=5e6, projection='gnom',lat_0=53.,lon_0=10., resolution="i")
# Europe
map = Basemap(llcrnrlon=-15, llcrnrlat=30, urcrnrlon=46, urcrnrlat=67,
              projection='lcc', lat_1=40, lat_2=55, lon_0=10, resolution="i")
# North America
# map = Basemap(llcrnrlon=-130, llcrnrlat=5, urcrnrlon=-55, urcrnrlat=70,
#              projection='cyl', lat_1=40, lat_2=55, lon_0=-100, resolution="i")
map.drawcoastlines(color=MAP_COLOR_COASTLINES)
map.drawcountries(color=MAP_COLOR_COUNTRIES)
map.drawmapboundary(fill_color=MAP_COLOR_WATER)
map.fillcontinents(color=MAP_COLOR_LAND, lake_color=MAP_COLOR_WATER)

region_box = box(minx=map.xmin, miny=map.ymin, maxx=map.xmax, maxy=map.ymax)
bbox = str(map.lonmin) + "," + str(map.latmin) + "," + str(map.lonmax) + "," + str(map.latmax)

print("Basemap drawing: " + str(time.time() - t0))
t0 = time.time()

urls = {"sigmets_international": "https://www.aviationweather.gov/gis/scripts/IsigmetJSON.php",
        "sigmets_us": "https://www.aviationweather.gov/gis/scripts/SigmetJSON.php",
        "cwa_us": "https://aviationweather.gov/cgi-bin/json/CwaJSON.php?zoom=4&bbox=" + bbox,
        "metars": "https://www.aviationweather.gov/gis/scripts/MetarJSON.php?density=all&bbox=" + bbox}

results = ThreadPool(5).imap_unordered(load_json_from_web, urls.values())

features_json = {}

for url, result in results:
    match = False
    for name, original_url in urls.items():
        if url == original_url:
            features_json[name] = result
            match = True
            break
    if not match:
        raise ValueError('Got a result for an url which was not requested')

print("Http access: " + str(time.time() - t0))
t0 = time.time()

plot_defintion = PlotDefinition(map, fig, ax, region_box)
features = Features(features_json['sigmets_international'], features_json['sigmets_us'], features_json['cwa_us'],
                    features_json['metars'])

plot_features = PlotFeatures(plot_defintion)
plot_features.plot(features)


print("Plotting: " + str(time.time() - t0))
t0 = time.time()
