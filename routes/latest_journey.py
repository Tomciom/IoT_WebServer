from flask import Blueprint, redirect, url_for, session
import sqlite3

bp = Blueprint('current_journey', __name__)

def get_latest_journey_id():
    username = session.get('username')
    conn = sqlite3.connect('journeys.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM journeys ORDER BY start_time DESC LIMIT 1')
    latest_journey = cursor.fetchone()
    conn.close()
    return latest_journey[0] if latest_journey else None

@bp.route('/current_journey', methods=['GET'])
def current_journey():
    latest_journey_id = get_latest_journey_id()
    if latest_journey_id:
        return redirect(url_for('journey_details.journey_details', journey_id=latest_journey_id,))
    else:
        return "Nie znaleziono aktualnej podróży.", 404
