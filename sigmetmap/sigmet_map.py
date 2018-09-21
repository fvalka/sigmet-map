import datetime
import json  # reading geojson files
import logging
from multiprocessing.pool import ThreadPool
from urllib.request import urlopen

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt  # plotting data
from shapely.geometry import box  # manipulating geometry

# CONSTANTS/CONFIGURATION
from sigmetmap.color_scheme import DefaultColorScheme, NorthAmericaColorScheme
from sigmetmap.model import PlotDefinition, Features
from sigmetmap.plot_features import PlotFeatures


class SigmetMap:
    def __init__(self, map_provider, feature_provider, legend_provider):
        self._map_provider = map_provider
        self._feature_provider = feature_provider
        self._legend_provider = legend_provider

    def plot(self, region, output_path):
        plot_definition = self._map_provider.create(region)
        features = self._feature_provider.load(plot_definition.bbox_string)

        plot_features = PlotFeatures(plot_definition, self._legend_provider.get_title)
        return plot_features.plot(features, output_path)


class MapProvider:
    """
    Provides PlotDefinitions with figures already created and the regions base map already rendered.
    """
    _log = logging.getLogger('map_provider')

    # All Map Settings for Regions
    _region_projections = {"eu": ccrs.LambertConformal(central_longitude=10.0, central_latitude=50.0,
                                                       standard_parallels=(40, 55)),
                           "na": ccrs.LambertConformal(central_longitude=-96.0, central_latitude=39.0,
                                                       standard_parallels=(33, 45)),
                           "sa": ccrs.LambertConformal(central_longitude=-64.0, central_latitude=-36.0,
                                                       standard_parallels=(-24, 5), cutoff=30),
                           "as": ccrs.LambertConformal(central_longitude=110.0,
                                                       central_latitude=24.0, standard_parallels=(21, 42)),
                           "oc": ccrs.LambertConformal(central_longitude=145.0, central_latitude=-25.0,
                                                       standard_parallels=(-28, -11), cutoff=30)}
    _region_extent = {"eu": [-10, 27, 33, 70],
                      "na": [-119, -68, 11, 55],
                      "sa": [-93, -33, -54, 15],
                      "as": [81, 140, -3, 55],
                      "oc": [110, 180, -45, 2]}
    # If no color is provided the default DefaultColorScheme will be used for that region
    _region_custom_color = {"na": NorthAmericaColorScheme}

    def get_regions(self):
        """
        Provides a list of regions supported by this MapProvider
        :return: List of supported regions
        """
        return list(self._region_projections.keys())

    def create(self, region):
        color_scheme = self._region_custom_color.get(region, DefaultColorScheme)
        fig = plt.figure(figsize=(12, 12))  # create a figure to contain the plot elements

        projection = self._region_projections[region]
        ax = plt.axes(projection=projection)
        ax.set_extent(self._region_extent[region])
        ax.background_patch.set_facecolor(color_scheme.MAP_COLOR_WATER)

        self._add_base_features(ax, color_scheme)

        # Since the original extend box is a rectangle only in the PlateCarree projection we need to
        # project this bounding box onto the actual projection obtaining a more complex shape in general
        unprojected_poly = box(ax.viewLim.x0, ax.viewLim.y0, ax.viewLim.x1, ax.viewLim.y1)
        region_box = ccrs.PlateCarree().project_geometry(unprojected_poly, projection)

        # Returns minimum bounding region (minx, miny, maxx, maxy)
        # This region covers all of the actually visible map or more, since it is a box in the
        # PlatteCarree projection which completely fills the actual projection
        x_min, y_min, x_max, y_max = region_box.bounds
        bbox = str(x_min) + "," + str(y_min) + "," + str(x_max) + "," + str(y_max)

        return PlotDefinition(projection, fig, ax, region_box, bbox, color_scheme)

    @staticmethod
    def _add_base_features(ax, color_scheme):
        """
        Adds Countries, Coastlines, Land, Lakes and Water to the base map.

        :param ax: Axis to which the features will be rendered
        :param color_scheme: The color scheme to use for the base map features
        """
        # COUNTRIES AND LAND MASSES
        ax.add_feature(cfeature.NaturalEarthFeature(
            category='cultural',
            name='admin_0_countries',
            scale='50m',
            facecolor=color_scheme.MAP_COLOR_LAND,
            edgecolor=color_scheme.MAP_COLOR_COUNTRIES,
            linewidth=0.3))
        # COASTLINES
        ax.add_feature(cfeature.NaturalEarthFeature(
            category='physical',
            name='coastline',
            scale='50m',
            facecolor='none',
            edgecolor=color_scheme.MAP_COLOR_COASTLINES,
            linewidth=0.5))
        # LAKES
        ax.add_feature(cfeature.NaturalEarthFeature(
            category='physical',
            name='lakes',
            scale='50m',
            facecolor=color_scheme.MAP_COLOR_WATER,
            edgecolor=color_scheme.MAP_COLOR_COASTLINES,
            linewidth=0.25))


class FeatureProvider:
    _log = logging.getLogger('feature_provider')

    def load(self, bbox):
        """
        Load advanced map features like SIGMETs, AIRMETs and METARs for the region provided in bbox.

        The features are loaded via https from the aviationweather.gov GeoJSON webservices.

        :param bbox: Region for which to load the features
        :return: Features object containing all features loaded from the web
        """
        self._log.info("Downloading features for bbox=%s", bbox)

        def load_json_from_web(url):
            response = urlopen(url)
            response_decoded = response.read().decode("utf-8")
            return url, json.loads(response_decoded)

        urls = {"sigmets_international": "https://www.aviationweather.gov/gis/scripts/IsigmetJSON.php",
                "sigmets_us": "https://www.aviationweather.gov/gis/scripts/SigmetJSON.php",
                "cwa_us": "https://aviationweather.gov/cgi-bin/json/CwaJSON.php?zoom=4&bbox=" + bbox,
                "metars": "https://www.aviationweather.gov/gis/scripts/MetarJSON.php?density=all&priority=10&bbox=" + bbox}

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


class LegendProvider:
    def get_title(self):
        return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%MZ")
