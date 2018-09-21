import datetime
import json
from unittest import mock

from model import Features
from sigmet_map import FeatureProvider, MapProvider, SigmetMap, LegendProvider


class InterceptingFeatureProvider(FeatureProvider):

    def __init__(self):
        self.intercepted: Features = None

    def load(self, bbox):
        self.intercepted = super().load(bbox)
        return self.intercepted

    def write(self, prefix):
        def write_to_file(feature, postfix):
            encoded = json.dumps(feature)
            with open(prefix + "_" + postfix, "w") as text_file:
                text_file.write(encoded)

        write_to_file(self.intercepted.sigmets_international, "sigmets_international.json")
        write_to_file(self.intercepted.metars, "metars.json")
        write_to_file(self.intercepted.cwa_us, "cwa_us.json")
        write_to_file(self.intercepted.sigmets_us, "sigmets_us.json")


class LegendProviderStub(LegendProvider):

    def get_title(self):
        return "TESTDATA"


feature_provider = InterceptingFeatureProvider()
map_provider = MapProvider()
legend_provider = LegendProviderStub()
sigmet_map = SigmetMap(map_provider, feature_provider, legend_provider)

ref_dir = "reference/"


def generate_region(region):
    result = sigmet_map.plot("%s" % region, "reference/%s.png" % region)
    feature_provider.write("%s%s" % (ref_dir, region))
    with open(ref_dir + region + "_result_info.json", "w") as text_file:
        text_file.write(json.dumps(result.info))
    with open(ref_dir + region + "_result_failed.json", "w") as text_file:
        text_file.write(json.dumps(result.failed))


generate_region('eu')
generate_region('na')
generate_region('sa')
generate_region('as')
generate_region('oc')
