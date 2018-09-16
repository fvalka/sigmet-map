class Features:
    def __init__(self, sigmets_international, sigmets_us, cwa_us, metars):
        self.metars = metars
        self.cwa_us = cwa_us
        self.sigmets_us = sigmets_us
        self.sigmets_international = sigmets_international


class PlotDefinition:
    def __init__(self, projection, fig, ax, region_box, bbox_string):
        self.projection = projection
        self.fig = fig
        self.ax = ax
        self.region_box = region_box
        self.bbox_string = bbox_string


class PlotResult:
    def __init__(self, plot_path, info, failed):
        self.plot_path = plot_path
        self.info = info
        self.failed = failed
