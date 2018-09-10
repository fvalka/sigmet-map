from datetime import datetime

import matplotlib.pyplot as plt  # plotting data
from adjustText import adjust_text
from descartes import PolygonPatch  # integrating geom object to matplot
from matplotlib.collections import PatchCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from shapely.geometry import asShape, Point  # manipulating geometry
from shapely.ops import transform

from Configuration import SIGMET_COLOR, \
    SIGMET_ALPHA, METAR_COLOR_UNKOWN, METAR_FLIGHT_CATEGORY_COLORS, METAR_ALPHA, TEXT_REPLACEMENT


class PlotFeatures:
    def __init__(self, plot_definition):
        self._plot_definition = plot_definition

    def plot(self, features):
        """
        Plots the features: International SIGMETs, US SIGMETs, US AIRMETs and METARS on the map with which this
        class was instantiated.

        :param features: Feature object containing the parsed GEOJSON data
        :return:
        """

        # Storage of return values
        texts = []
        plotting_failed = []
        info = {}

        ax = self._plot_definition.ax
        m = self._plot_definition.map

        def plot_features(features, label_property, text_property):
            """
            Plots a collection of features onto the map.

            :param features: The list of GEOJSON features
            :param label_property: Field in features[i]["properties"] which contains the label to be plotted onto the map
            :param text_property: Field in features[i]["properties"] which will be added to the infos.
            :return: Information dictionary { idx: info_text, ... }
            """
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
            """
            Plots one feature. If the feature is a point it will be plotted straight onto the map.

            If it is a polygon it will be added to patches

            :param feat: Feature to be plotted
            :param label_property: Field in feat["properties"] which contains the label to be plotted on the map
            :param patches: Patches collection to which the patch will be appended
            :param text_property: Field in feat["properties"] which contains the text will be added to the info
            :return: Information dictionary with one element { idx: info_text }
            """
            if feat["geometry"]["type"] == "Polygon":
                # convert the geometry to shapely
                geom_raw = asShape(feat["geometry"])
                if len(geom_raw.shell) > 2:
                    geom = transform(m, geom_raw.buffer(0))
                    patches.append(PolygonPatch(geom))
                    label_geometry(geom, feat, label_property, text_property)
            elif feat["geometry"]["type"] == "Point":
                geom = transform(m, Point(feat["geometry"]["coordinates"][0], feat["geometry"]["coordinates"][1]))
                ax.plot(geom.x, geom.y, 'o', color=SIGMET_COLOR, markersize=12, zorder=35)
                label_geometry(geom, feat, label_property, text_property)
            else:
                raise ValueError('Geometry type was neither Polygon nor Point.')

        def label_geometry(geom, feat, label_property, text_property):
            """
            Labels one geometry elements. Usually a  SIMGET or AIRMET patch.

            The label will be placed in the centroid of the visible part of geom.

            :param geom: Geometry to be labeled.
            :param feat: GEOJSON Feature
            :param label_property: Field in feat["properties"] which contains the label to be plotted on the map
            :param text_property: Field in feat["properties"] which contains the text will be added to the info
            :return: Information dictionary with one element { idx: info_text }
            """
            centroid = geom.intersection(self._plot_definition.region_box).centroid

            if geom.intersects(self._plot_definition.region_box):
                idx = len(info) + 1
                label = feat["properties"][label_property]
                label = TEXT_REPLACEMENT.get(label, label)
                text = label + "\n" + str(idx) + "."
                new_text = self._plot_definition.ax.text(centroid.x, centroid.y, text, horizontalalignment='center',
                                                         verticalalignment='center', zorder=50, fontweight="heavy",
                                                         fontsize=9)
                texts.append(new_text)
                info[idx] = feat["properties"][text_property]

        def plot_metars(metar_features):
            """
            Plots metars on the map.

            :param metar_features: GEOJSON METAR feature list
            :return:
            """
            for feat in metar_features:
                if feat["geometry"]["type"] == "Point":
                    geom = transform(m, Point(feat["geometry"]["coordinates"][0], feat["geometry"]["coordinates"][1]))

                    label = feat["properties"].get("fltcat", "?")
                    color = METAR_FLIGHT_CATEGORY_COLORS.get(label, METAR_COLOR_UNKOWN)

                    ax.plot(geom.x, geom.y, 'o', color=color, markersize=5, zorder=30, alpha=METAR_ALPHA)

        plot_features(features.sigmets_international["features"], "hazard", "rawSigmet")
        plot_features(features.sigmets_us["features"], "hazard", "rawAirSigmet")
        plot_features(features.cwa_us["features"], "hazard", "cwaText")

        plot_metars(features.metars["features"])

        adjust_text(texts, ha='center', va='center', expand_text=(0.9, 0.9), autoalign=False,
                    on_basemap=True, text_from_points=False,
                    arrowprops=dict(arrowstyle='->', color='0.15', shrinkA=3, shrinkB=3, connectionstyle="arc3,rad=0."),
                    force_text=(0.8, 0.8))

        self._plot_legend(ax, plotting_failed)

        plt.show()

    @staticmethod
    def _plot_legend(ax, plotting_failed):
        """
        Plot the legend on the map.

        Including a warning if plotting_failed is not empty

        :param ax:
        :param plotting_failed:
        :return:
        """
        ax.set_title(datetime.utcnow().strftime("%Y-%m-%d %H:%MZ"), loc='right')
        if len(plotting_failed) > 0:
            ax.set_title('WARNING! Some SIGMETs or AIRMETs were not plotted due to errors!', loc='left',
                         fontweight="heavy")

        def metar_legend(flight_category):
            return Line2D([0], [0], marker='o', color=METAR_FLIGHT_CATEGORY_COLORS[flight_category],
                          label=flight_category, markersize=8, linestyle='None', alpha=METAR_ALPHA)

        legend_elements = [metar_legend('VFR'), metar_legend('MVFR'), metar_legend('IFR'),
                           metar_legend('LIFR'), metar_legend('?'),
                           Patch(facecolor=SIGMET_COLOR, edgecolor=SIGMET_COLOR,
                                 label='SIGMETs and AIRMETs', alpha=SIGMET_ALPHA)]
        ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.005), ncol=6)
