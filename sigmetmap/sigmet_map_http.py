import logging
import os
import secrets
import time

from flask import Flask, jsonify, url_for, abort
from flask_caching import Cache
from apscheduler.schedulers.background import BackgroundScheduler

# CONSTANTS/CONFIGURATION
from sigmetmap.sigmet_map import MapProvider, FeatureProvider, SigmetMap

logging.basicConfig(level=logging.DEBUG)

# Flask Setup
app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Application Setup
map_provider = MapProvider()
feature_provider = FeatureProvider()
sigmet_map_plotter = SigmetMap(map_provider, feature_provider)
plots_dir = "static/"

# Background Task Setup
sched = BackgroundScheduler()
sched.start()


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
    plot_result = sigmet_map_plotter.plot(region, plots_dir + file_name)
    url = url_for('static', filename=file_name)
    return jsonify(url=url, infos=plot_result.info, failed=plot_result.failed)


@sched.scheduled_job(trigger='interval', minutes=10)
def cleanup():
    now = time.time()
    for file in os.listdir(plots_dir):
        created = os.path.getctime(plots_dir + file)
        if (now - created) >= 2*60*60:
            os.unlink(plots_dir + file)


if __name__ == '__main__':
    app.run(threaded=True)
