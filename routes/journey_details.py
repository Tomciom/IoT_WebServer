from flask import Blueprint, render_template
import sqlite3

bp = Blueprint('journey_details', __name__)

def get_journey_data(journey_id):
    conn = sqlite3.connect('journeys.db')
    conn.row_factory = sqlite3.Row  # Umożliwia dostęp do kolumn po nazwie
    cursor = conn.cursor()

    # Pobierz dane pomiarowe temperatury i ciśnienia
    cursor.execute('SELECT timestamp, temperature, pressure FROM temperature_pressure WHERE journey_id = ?', (journey_id,))
    measurements = cursor.fetchall()

    # Pobierz dane statusów związanych z wykryciem ognia
    cursor.execute('SELECT timestamp, fire_detected, sensor_value FROM fire_detection WHERE journey_id = ?', (journey_id,))
    fire_data = cursor.fetchall()

    # Pobierz dane obrotu i przyspieszenia
    cursor.execute('SELECT timestamp, rotation_degrees_x, rotation_degrees_y, rotation_degrees_z, gx, gy, gz FROM rotation_acceleration WHERE journey_id = ?', (journey_id,))
    rotation_data = cursor.fetchall()

    conn.close()
    return measurements, fire_data, rotation_data

@bp.route('/journey_details/<int:journey_id>', methods=['GET'])
def journey_details(journey_id):
    measurements, fire_data, rotation_data = get_journey_data(journey_id)
    return render_template('journey_details.html', 
                           journey_id=journey_id, 
                           measurements=measurements, 
                           fire_data=fire_data, 
                           rotation_data=rotation_data)
