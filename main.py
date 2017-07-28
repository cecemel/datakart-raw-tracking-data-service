from flask import Flask, request, jsonify
import os, sys
import logging
import config
from flask import jsonify, g
import sqlite3
import uuid

##############
# INIT CONFIG
##############
CONFIG = config.load_config(os.environ.get('ENVIRONMENT', "DEBUG"))
app = Flask(__name__)

handler = logging.StreamHandler(stream=sys.stderr)
handler.setLevel(CONFIG["LOG_LEVEL"])
app.logger.addHandler(handler)


##############
# HELPERS
##############
@app.before_first_request
def init_db():
    app.logger.info("checking DB existance")
    response = getattr(g, '_has_database', False)

    if response:
        return

    app.logger.info("init database")
    # create folder if non existant
    os.makedirs(os.path.dirname(CONFIG["DB"]), exist_ok=True)
    db_connection = sqlite3.connect(CONFIG["DB"])
    cursor = db_connection.cursor()
    # Create table
    cursor.execute('''CREATE TABLE IF NOT EXISTS tracking_entries 
                      (id text, session text, timestamp text, x_value real, y_value real, z_value real, signal_strength real)''')

    db_connection.commit()
    db_connection.close()
    setattr(g, '_has_database', True)
    app.logger.info("finished init")


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        g._database = sqlite3.connect(CONFIG["DB"])
    return g._database


def store_tracking_entries(session, entries):
    database = get_db()
    cursor = get_db().cursor()

    insert_values = []

    for entry in entries:
        id = str(uuid.uuid4())
        insert_values.append((id, session, entry["timestamp"], entry["x-value"], entry["y-value"],
                             entry["z-value"], entry.get("signal-strength")))



    cursor.executemany('INSERT INTO tracking_entries VALUES (?,?,?,?,?,?,?)', insert_values)
    database.commit()


def get_tracking_entries(session):
    database = get_db()
    cursor = get_db().cursor()
    results = cursor.execute('SELECT * FROM tracking_entries WHERE session=? ORDER BY timestamp ASC', (session,))
    return format_results(results)


def get_tracking_entries_between(start, end, session):
    database = get_db()
    cursor = get_db().cursor()
    results = cursor.execute('SELECT * FROM tracking_entries WHERE session=? '
                             'AND timestamp >= ? and TIMESTAMP <= ? '
                             'ORDER BY timestamp ASC', (session, start, end,))
    return format_results(results)


def get_tracking_entries_point(datapoint_id):
    database = get_db()
    cursor = get_db().cursor()
    results = cursor.execute('SELECT * FROM tracking_entries WHERE id=? ', (datapoint_id,))
    return format_results(results)


def format_results(results):
    formatted_results = []
    for result in results:
        formatted_results.append({
                                  "id": result[0],
                                  "session": result[1],
                                  "timestamp": result[2],
                                  "x-value": result[3],
                                  "y-value": result[4],
                                  "z-value": result[5],
                                  "signal-strength": result[6]})

    return formatted_results


#################
# API
#################
@app.route('/raw-trackings-data/<session_uuid>/data-points', methods=["PATCH"])
def store_entry(session_uuid):
    # validates
    data = request.get_json(force=True)
    if type(data) is not list:
        data = [data]

    store_tracking_entries(session_uuid, data)

    return jsonify({}), 204


@app.route('/raw-trackings-data/<session_uuid>/data-points', methods=["GET"])
def get_entries_session(session_uuid):
    start = request.args.get('start')
    end = request.args.get('end')
    if not (start and end):
        return jsonify(get_tracking_entries(session_uuid)), 200

    return jsonify(get_tracking_entries_between(start, end, session_uuid)), 200


@app.route('/raw-trackings-data/<session_uuid>/data-points/<datapoint_id>', methods=["GET"])
def get_trackings_data_point(session_uuid, datapoint_id):
    points = get_tracking_entries_point(datapoint_id)

    if points:
        return jsonify(points[0]), 200

    return jsonify({}), 404

#######################
# APPLICATION START #
#######################
if __name__ == '__main__':
    app.logger.info("starting")
    app.run(host='0.0.0.0', debug=True)
