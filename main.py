from flask import Flask, request, jsonify
import os, sys
import helpers, escape_helpers
import logging
import config
from flask import jsonify

##############
# INIT CONFIG
##############
CONFIG = config.load_config(os.environ.get('ENVIRONMENT', "DEBUG"))
app = Flask(__name__)

handler = logging.StreamHandler(stream=sys.stderr)
handler.setLevel(CONFIG["LOG_LEVEL"])
app.logger.addHandler(handler)


#################
# API
#################
@app.route('/raw-trackings-data/<session_uuid>', methods=["PATCH"])
def store_entry():
    # validates
    data = request.get_json(force=True)

    return jsonify(formatted_order), 200


#######################
## Start Application ##
#######################
if __name__ == '__main__':
    app.logger.info("starting")
    app.run(host='0.0.0.0', debug=True)
