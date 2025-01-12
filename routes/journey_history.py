from flask import Blueprint, render_template, jsonify, request
import sqlite3

bp = Blueprint('journey_history', __name__)

def get_all_journeys():
    conn = sqlite3.connect('journeys.db')
    conn.row_factory = sqlite3.Row  # Umożliwia dostęp do kolumn po nazwie
    c = conn.cursor()
    c.execute('SELECT id, name, start_time, end_time FROM journeys ORDER BY start_time DESC')
    journeys = c.fetchall()
    conn.close()
    return journeys

@bp.route('/journey_history', methods=['GET'])
def journey_history():
    journeys = get_all_journeys()
    return render_template('journey_history.html', journeys=journeys)
