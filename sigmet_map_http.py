import logging
import secrets

from flask import Flask, jsonify, url_for, abort
from flask_caching import Cache

# CONSTANTS/CONFIGURATION
from sigmet_map import MapProvider, FeatureProvider, SigmetMap

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

map_provider = MapProvider()
feature_provider = FeatureProvider()
sigmet_map_plotter = SigmetMap(map_provider, feature_provider)


@app.route('/')
def index():
    return 'index'


@app.route('/sigmet_map/<region>')
@cache.memoize(timeout=60)
def sigmet_map(region):
    if region not in map_provider.get_regions():
        abort(404)

    # Use a random file path, which should never ever collide
    file_name = secrets.token_urlsafe(32) + ".png"
    plot_result = sigmet_map_plotter.plot(region, "static/" + file_name)
    url = url_for('static', filename=file_name)
    return jsonify(url=url, infos=plot_result.info, failed=plot_result.failed)


if __name__ == '__main__':
    app.run(threaded=True)
