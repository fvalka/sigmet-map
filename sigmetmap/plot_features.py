import logging
from datetime import datetime, timezone
import dateutil.parser

import cartopy.crs as ccrs
from adjustText import adjust_text, get_renderer, get_bboxes
from descartes import PolygonPatch  # integrating geom object to matplot
from matplotlib.backends.backend_template import FigureCanvas
from matplotlib.collections import PatchCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from shapely.geometry import asShape, Point  # manipulating geometry

from sigmetmap.model import PlotResult


class PlotFeatures:
    """
    Plots the SIGMET, AIRMET, CWA and METAR features onto a matplotlib axis with details of the map provided
    in the PlotDefinition.
    """
    _log = logging.getLogger('plot_features')

    def __init__(self, plot_definition, get_title):
        self._color_scheme = plot_definition.color_scheme
        self._plot_definition = plot_definition
        self._get_title = get_title

    def plot(self, features, output_path):
        """
        Plots the features: International SIGMETs, US SIGMETs, US AIRMETs and METARS on the map with which this
        class was instantiated.

        :param features: Feature object containing the parsed GEOJSON data
        :param output_path: Path to where the plot will be saved. Only PNG supported for now!
        :return:
        """
        self._log.debug("Plotting features onto axis")

        # Storage of return values
        texts = []
        plotting_failed = []
        info = {}

        ax = self._plot_definition.ax
        data_crs = ccrs.PlateCarree()

        def plot_features(features, label_property, text_property):
            """
            Plots a collection of features onto the map.

            :param features: The list of GEOJSON features
            :param label_property: Field in features[i]["properties"] which contains the label to be plotted onto the map
            :param text_property: Field in features[i]["properties"] which will be added to the infos.
            :return: Information dictionary { idx: info_text, ... }
            """
            patches = []
            patches_unkown = []
            for feat in features:
                try:
                    plot_one_feature(feat, label_property, patches, patches_unkown, text_property)
                except ValueError:
                    plotting_failed.append(feat['properties'][text_property])
                    self._log.warning("Plotting of feature=%s failed", feat)

            ax.add_collection(
                PatchCollection(patches, facecolor=self._color_scheme.SIGMET_COLOR,
                                edgecolor=self._color_scheme.SIGMET_COLOR,
                                linewidths=1.5, alpha=self._color_scheme.SIGMET_ALPHA, zorder=40,
                                transform=data_crs))
            ax.add_collection(
                PatchCollection(patches_unkown, facecolor=self._color_scheme.SIGMET_UNKNOWN_COLOR,
                                linestyle='dashed', edgecolor=self._color_scheme.SIGMET_UNKNOWN_COLOR,
                                hatch="/", linewidths=1.5, alpha=self._color_scheme.SIGMET_UNKNOWN_ALPHA, zorder=39,
                                transform=data_crs))

        def plot_one_feature(feat, label_property, patches, patches_unkown, text_property):
            """
            Plots one feature. If the feature is a point it will be plotted straight onto the map.

            If it is a polygon it will be added to patches

            :param feat: Feature to be plotted
            :param label_property: Field in feat["properties"] which contains the label to be plotted on the map
            :param patches: Patches collection to which the patch will be appended
            :param patches_unknown: Patches collection with unkown geometry
            :param text_property: Field in feat["properties"] which contains the text will be added to the info
            :return: Information dictionary with one element { idx: info_text }
            """
            if feat["geometry"]["type"] == "Polygon":
                # convert the geometry to shapely
                geom_raw = asShape(feat["geometry"])
                if len(geom_raw.shell) > 2:
                    geom = geom_raw.buffer(0)
                    label_geometry(geom, feat, label_property, text_property)

                    if feat["properties"].get("geom", "") == "UNK":
                        patches_unkown.append(PolygonPatch(geom))
                    else:
                        patches.append(PolygonPatch(geom))
                else:
                    self._log.warning("Encountered feature which had less than 2 elements in its shell feature=%s",
                                      feat)
            elif feat["geometry"]["type"] == "Point":
                geom = Point(feat["geometry"]["coordinates"][0], feat["geometry"]["coordinates"][1])
                ax.plot(geom.x, geom.y, 'o', color=self._color_scheme.SIGMET_COLOR, markersize=8,
                        zorder=35, transform=data_crs)
                label_geometry(geom, feat, label_property, text_property)
            else:
                self._log.error("Encountered geometry which was neither a polygon nor a point. feature=%s", feat)
                raise ValueError('Geometry type was neither Polygon nor Point.')

        def find_text(x, y):
            for text in texts:
                text_x, text_y = text.get_position()
                if text_x == x and text_y == y:
                    return text
            return None

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
                label = self._color_scheme.TEXT_REPLACEMENT.get(label, label)
                text = label + "\n" + str(idx) + "."

                text_x, text_y = self._plot_definition.projection.transform_point(centroid.x, centroid.y, data_crs)
                conflicting_text = find_text(text_x, text_y)
                if conflicting_text:
                    self._log.debug("Resolving conflicting text")
                    r = get_renderer(self._plot_definition.ax.get_figure())
                    bbox = get_bboxes([conflicting_text], r, (1.0, 1.0), ax)
                    text_x = text_x - bbox[0].width / 10
                    text_y = text_y - bbox[0].height / 10

                new_text = ax.text(text_x, text_y, text, horizontalalignment='center',
                                   verticalalignment='center', zorder=50, fontweight="heavy",
                                   fontsize=8)
                texts.append(new_text)
                info[idx] = feat["properties"][text_property]

        def plot_metars(metar_features):
            """
            Plots metars on the map.

            :param metar_features: GEOJSON METAR feature list
            :return:
            """
            self._log.debug("Plotting METARs")

            for index, feat in metar_features.iterrows():
                geom = Point(feat['longitude'], feat['latitude'])

                if self._plot_definition.region_box.contains(geom):
                    label = feat['flight_category']
                    color = self._color_scheme.METAR_FLIGHT_CATEGORY_COLORS.get(label,
                                                                                self._color_scheme.METAR_COLOR_UNKOWN)

                    age = datetime.now(timezone.utc) - dateutil.parser.parse(feat['observation_time'])
                    age_m = age.total_seconds()/60
                    alpha_age_factor = min(1, -1/90 * age_m + 4/3)
                    alpha = self._color_scheme.METAR_ALPHA * alpha_age_factor

                    ax.plot(geom.x, geom.y, 'o', color=color, markersize=4,
                            zorder=30, alpha=alpha, transform=data_crs)

        plot_features(features.sigmets_international["features"], "hazard", "rawSigmet")
        plot_features(features.sigmets_us["features"], "hazard", "rawAirSigmet")
        plot_features(features.cwa_us["features"], "hazard", "cwaText")

        plot_metars(features.metars)

        adjust_text(texts, ha='center', va='center', expand_text=(0.9, 0.9), autoalign=False,
                    on_basemap=True, text_from_points=False,
                    arrowprops=dict(arrowstyle='->', color='0.15', shrinkA=3, shrinkB=3, connectionstyle="arc3,rad=0."),
                    force_text=(0.8, 0.8))

        self._plot_legend(ax, plotting_failed)

        canvas = FigureCanvas(self._plot_definition.fig)
        canvas.print_figure(output_path, format="png", pad_inches=0.2, bbox_inches="tight",
                            bbox_extra_artists=[], dpi=90)

        return PlotResult(output_path, info, plotting_failed)

    def _plot_legend(self, ax, plotting_failed):
        """
        Plot the legend on the map.

        Including a warning if plotting_failed is not empty

        :param ax:
        :param plotting_failed:
        :return:
        """
        self._log.debug("Plotting legend")
        ax.set_title(self._get_title(), loc='right')
        if len(plotting_failed) > 0:
            ax.set_title('WARNING! Some SIGMETs or AIRMETs were not plotted due to errors!', loc='left',
                         fontweight="heavy")

        def metar_legend(flight_category):
            return Line2D([0], [0], marker='o', color=self._color_scheme.METAR_FLIGHT_CATEGORY_COLORS[flight_category],
                          label=flight_category, markersize=8, linestyle='None', alpha=self._color_scheme.METAR_ALPHA)

        legend_elements = [metar_legend('VFR'), metar_legend('MVFR'), metar_legend('IFR'),
                           metar_legend('LIFR'), metar_legend('?'),
                           Patch(facecolor=self._color_scheme.SIGMET_COLOR, edgecolor=self._color_scheme.SIGMET_COLOR,
                                 label='SIGMETs and AIRMETs', alpha=self._color_scheme.SIGMET_ALPHA, linewidth=1.5),
                           Patch(facecolor=self._color_scheme.SIGMET_UNKNOWN_COLOR,
                                 linestyle='dashed', edgecolor=self._color_scheme.SIGMET_UNKNOWN_COLOR,
                                 hatch="/", linewidth=1.5, alpha=self._color_scheme.SIGMET_UNKNOWN_ALPHA,
                                 label="SIGMETs unknown location in FIR")]
        ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.005), ncol=5)
