class DefaultColorScheme:
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


class NorthAmericaColorScheme(DefaultColorScheme):
    METAR_ALPHA = 0.4
