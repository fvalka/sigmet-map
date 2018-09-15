class Features:
    def __init__(self, sigmets_international, sigmets_us, cwa_us, metars):
        self.metars = metars
        self.cwa_us = cwa_us
        self.sigmets_us = sigmets_us
        self.sigmets_international = sigmets_international


class PlotDefinition:
    def __init__(self, map, fig, ax, region_box):
        self.map = map
        self.fig = fig
        self.ax = ax
        self.region_box = region_box
