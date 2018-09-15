import json  # reading geojson files
import logging
import pickle
from multiprocessing.pool import ThreadPool
from urllib.request import urlopen

import matplotlib.pyplot as plt  # plotting data
from mpl_toolkits.basemap import Basemap
from shapely.geometry import box  # manipulating geometry

# CONSTANTS/CONFIGURATION
from color_scheme import DefaultColorScheme, NorthAmericaColorScheme
from model import PlotDefinition, Features


class MapProvider:
    log = logging.getLogger('map_provider')

    def __init__(self):
        self._init_base_maps()

    def get_map(self, region):
        return pickle.loads(self._maps[region])

    def _init_base_maps(self):
        logging.debug("Pre-rendering maps for later usage")
        region_settings = [("eu", dict(llcrnrlon=-15, llcrnrlat=30, urcrnrlon=46, urcrnrlat=67,
                                       projection='lcc', lat_1=40, lat_2=55, lon_0=10, resolution="i"),
                            DefaultColorScheme),
                           ("na", dict(llcrnrlon=-130, llcrnrlat=5, urcrnrlon=-55, urcrnrlat=70,
                                       projection='cyl', resolution="i"),
                            NorthAmericaColorScheme),
                           ("sa", dict(llcrnrlon=-100, llcrnrlat=-54, urcrnrlon=-37, urcrnrlat=15,
                                       projection='lcc', lat_1=-8, lat_2=-33, lon_0=-60, resolution="c"),
                            DefaultColorScheme)]

        self._maps = {}
        results = ThreadPool(len(region_settings)).imap_unordered(self._create_base_map, region_settings)

        for region, plot_definition in results:
            self._maps[region] = pickle.dumps(plot_definition)

        logging.debug('Finished rendering maps')

    def _create_base_map(self, settings):
        logging.debug('Rendering single base map settings=%s', settings)
        region, map_settings, color_scheme = settings
        fig = plt.figure(figsize=(12, 12))  # create a figure to contain the plot elements
        ax = fig.gca()

        map = Basemap(**map_settings)
        map.drawcoastlines(color=color_scheme.MAP_COLOR_COASTLINES)
        map.drawcountries(color=color_scheme.MAP_COLOR_COUNTRIES)
        map.drawmapboundary(fill_color=color_scheme.MAP_COLOR_WATER)
        map.fillcontinents(color=color_scheme.MAP_COLOR_LAND, lake_color=color_scheme.MAP_COLOR_WATER)
        region_box = box(minx=map.xmin, miny=map.ymin, maxx=map.xmax, maxy=map.ymax)

        return region, PlotDefinition(map, fig, ax, region_box)


# Draw Basemap

# map = Basemap(projection='cyl', urcrnrlon=44, urcrnrlat=72, llcrnrlon=-19, llcrnrlat=33, resolution="i")
# map = Basemap(width=5e6,height=5e6, projection='gnom',lat_0=53.,lon_0=10., resolution="i")
# Europe
# map = Basemap(llcrnrlon=-15, llcrnrlat=30, urcrnrlon=46, urcrnrlat=67,
#              projection='lcc', lat_1=40, lat_2=55, lon_0=10, resolution="i")
# North America


# bbox = str(map.lonmin) + "," + str(map.latmin) + "," + str(map.lonmax) + "," + str(map.latmax)


class FeatureProvider:
    def load(self, bbox):
        def load_json_from_web(url):
            response = urlopen(url)
            response_decoded = response.read().decode("utf-8")
            return url, json.loads(response_decoded)

        urls = {"sigmets_international": "https://www.aviationweather.gov/gis/scripts/IsigmetJSON.php",
                "sigmets_us": "https://www.aviationweather.gov/gis/scripts/SigmetJSON.php",
                "cwa_us": "https://aviationweather.gov/cgi-bin/json/CwaJSON.php?zoom=4&bbox=" + bbox,
                "metars": "https://www.aviationweather.gov/gis/scripts/MetarJSON.php?density=all&bbox=" + bbox}

        features_json = {}
        results = ThreadPool(5).imap_unordered(load_json_from_web, urls.values())

        for url, result in results:
            match = False
            for name, original_url in urls.items():
                if url == original_url:
                    features_json[name] = result
                    match = True
                    break
            if not match:
                raise ValueError('Got a result for an url which was not requested')

        return Features(features_json['sigmets_international'], features_json['sigmets_us'], features_json['cwa_us'],
                        features_json['metars'])
