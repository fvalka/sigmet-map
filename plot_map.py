import json  # reading geojson files
import time
from multiprocessing.pool import ThreadPool
from urllib.request import urlopen

import matplotlib.pyplot as plt  # plotting data
from mpl_toolkits.basemap import Basemap
from shapely.geometry import box  # manipulating geometry

# CONSTANTS/CONFIGURATION
from color_scheme import DefaultColorScheme, NorthAmericaColorScheme
from model import PlotDefinition, Features
from plot_features import PlotFeatures


class PlotMap:
    def __init__(self):
        pass

    def _load_features(self, bbox):
        def load_json_from_web(url):
            response = urlopen(url)
            response_decoded = response.read().decode("utf-8")
            return url, json.loads(response_decoded)

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

        return Features(features_json['sigmets_international'], features_json['sigmets_us'],
                        features_json['cwa_us'], features_json['metars'])

    def plot(self, region):
        color_scheme = NorthAmericaColorScheme()
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
        map.drawcoastlines(color=color_scheme.MAP_COLOR_COASTLINES)
        map.drawcountries(color=color_scheme.MAP_COLOR_COUNTRIES)
        map.drawmapboundary(fill_color=color_scheme.MAP_COLOR_WATER)
        map.fillcontinents(color=color_scheme.MAP_COLOR_LAND, lake_color=color_scheme.MAP_COLOR_WATER)

        region_box = box(minx=map.xmin, miny=map.ymin, maxx=map.xmax, maxy=map.ymax)
        plot_definition = PlotDefinition(map, fig, ax, region_box)

        bbox = str(map.lonmin) + "," + str(map.latmin) + "," + str(map.lonmax) + "," + str(map.latmax)

        plot_features = PlotFeatures(plot_definition, color_scheme)
        plot_features.plot(self._load_features(bbox))
