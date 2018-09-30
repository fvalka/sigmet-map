import datetime
import json
from unittest import mock
from urllib.request import urlopen

from model import Features
from sigmet_map import FeatureProvider, MapProvider, SigmetMap, LegendProvider


class InterceptingFeatureProvider(FeatureProvider):

    def __init__(self, ref_dir, prefix):
        self.ref_dir = ref_dir
        self.prefix = prefix
        self.intercepted = []

    def load_from_web(self, definition):
        name, url, decoder = definition
        response = urlopen(url)
        response_decoded = decoder(response)

        self._write(name, response)

        return name, response_decoded

    def _write(self, name, response):
        f = open(self.ref_dir + self.prefix + "_" + name, "wb")
        content = response.read()
        f.write(content)
        f.close()


class LegendProviderStub(LegendProvider):

    def get_title(self):
        return "TESTDATA"


ref_dir = "reference/"

feature_provider = InterceptingFeatureProvider(ref_dir, 'none')
map_provider = MapProvider()
legend_provider = LegendProviderStub()
sigmet_map = SigmetMap(map_provider, feature_provider, legend_provider)


def generate_region(region):
    feature_provider.prefix = region
    result = sigmet_map.plot("%s" % region, "reference/%s.png" % region)
    with open(ref_dir + region + "_result_info.json", "w") as text_file:
        text_file.write(json.dumps(result.info))
    with open(ref_dir + region + "_result_failed.json", "w") as text_file:
        text_file.write(json.dumps(result.failed))


generate_region('eu')
generate_region('na')
generate_region('sa')
generate_region('as')
generate_region('oc')
