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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracking_entries 
          (id TEXT, 
          session TEXT, 
          timestamp TEXT, 
          x_value REAL, 
          y_value REAL, 
          z_value REAL,
          signal_strength REAL,
          x_value_acceleration REAL, 
          y_value_acceleration REAL, 
          z_value_acceleration REAL,
          x_value_acceleration_linear REAL, 
          y_value_acceleration_linear REAL, 
          z_value_acceleration_linear REAL,
          x_value_angular_velocity REAL,
          y_value_angular_velocity REAL,
          z_value_angular_velocity REAL,
          heading_value_euler REAL,
          roll_value_euler REAL,
          pitch_value_euler REAL,
          x_value_gravity_vector REAL,
          y_value_gravity_vector REAL,
          z_value_gravity_vector REAL,
          x_value_magnetic REAL,
          y_value_magnetic REAL,
          z_value_magnetic REAL,
          W_value_quaternion REAL,
          x_value_quaternion REAL,
          y_value_quaternion REAL,
          z_value_quaternion REAL,
          temperature REAL
          )''')

    db_connection.commit()
    db_connection.close()
    setattr(g, '_has_database', True)
    app.logger.info("finished init")


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


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
        insert_values.append((id, session,
                              entry["timestamp"],
                              entry["x-value"], entry["y-value"], entry["z-value"],
                              entry.get("signal-strength"),
                              entry.get("x-value-acceleration"),
                              entry.get("y-value-acceleration"),
                              entry.get("z-value-acceleration"),
                              entry.get("x-value-acceleration-linear"),
                              entry.get("y-value-acceleration-linear"),
                              entry.get("z-value-acceleration-linear"),
                              entry.get("x-value-angular-velocity"),
                              entry.get("y-value-angular-velocity"),
                              entry.get("z-value-angular-velocity"),
                              entry.get("heading-value-euler"),
                              entry.get("roll-value-euler"),
                              entry.get("pitch-value-euler"),
                              entry.get("x-value-gravity-vector"),
                              entry.get("y-value-gravity-vector"),
                              entry.get("z-value-gravity-vector"),
                              entry.get("x-value-magnetic"),
                              entry.get("y-value-magnetic"),
                              entry.get("z-value-magnetic"),
                              entry.get("w-value-quaternion"),
                              entry.get("x-value-quaternion"),
                              entry.get("y-value-quaternion"),
                              entry.get("z-value-quaternion"),
                              entry.get("temperature")
                              ))
        cursor.executemany('INSERT INTO tracking_entries '
                           'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', insert_values)

    database.commit()


def get_tracking_entries(session):
    database = get_db()
    cursor = get_db().cursor()
    results = cursor.execute('SELECT * FROM tracking_entries WHERE session=? ORDER BY timestamp ASC', (session,))
    return format_results(results)


def delete_tracking_entries(session):
    database = get_db()
    cursor = get_db().cursor()
    results = cursor.execute('DELETE FROM tracking_entries WHERE session=?', (session,))
    database.commit()
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
                                  "signal-strength": result[6],
                                  "x-value-acceleration": result[7],
                                  "y-value-acceleration": result[8],
                                  "z-value-acceleration": result[9],
                                  "x-value-acceleration-linear": result[10],
                                  "y-value-acceleration-linear": result[11],
                                  "z-value-acceleration-linear": result[12],
                                  "x-value-angular-velocity": result[13],
                                  "y-value-angular-velocity": result[14],
                                  "z-value-angular-velocity": result[15],
                                  "heading-value-euler": result[16],
                                  "roll-value-euler": result[17],
                                  "pitch-value-euler": result[18],
                                  "x-value-gravity-vector": result[19],
                                  "y-value-gravity-vector": result[20],
                                  "z-value-gravity-vector": result[21],
                                  "x-value-magnetic": result[22],
                                  "y-value-magnetic": result[23],
                                  "z-value-magnetic": result[24],
                                  "w-value-quaternion": result[25],
                                  "x-value-quaternion": result[26],
                                  "y-value-quaternion": result[27],
                                  "z-value-quaternion": result[28],
                                  "temperature": result[29]
                                })

    return formatted_results


#################
# API
#################
@app.route('/raw-tracking-sessions/<session_uuid>/data-points', methods=["POST"])
def store_entry(session_uuid):
    # validates
    data = request.get_json(force=True)
    if type(data) is not list:
        data = [data]

    store_tracking_entries(session_uuid, data)

    return jsonify({}), 204


@app.route('/raw-tracking-sessions/<session_uuid>/data-points', methods=["GET"])
def get_entries_session(session_uuid):
    start = request.args.get('start')
    end = request.args.get('end')
    if not (start and end):
        return jsonify(get_tracking_entries(session_uuid)), 200

    return jsonify(get_tracking_entries_between(start, end, session_uuid)), 200


@app.route('/raw-tracking-sessions/<session_uuid>', methods=["DELETE"])
def delete_entries_session(session_uuid):
    return jsonify(delete_tracking_entries(session_uuid)), 200


@app.route('/raw-tracking-sessions/<session_uuid>/data-points/<datapoint_id>', methods=["GET"])
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
