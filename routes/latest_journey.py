from flask import Blueprint, redirect, url_for, session
import sqlite3

bp = Blueprint('current_journey', __name__)

def get_latest_journey_id_for_user():
    username = session.get('username')
    if not username:
        return None

    # Krok 1: Pobranie user_id na podstawie username oraz adresów MAC powiązanych z tym użytkownikiem
    conn_users = sqlite3.connect('Users.db')
    conn_users.row_factory = sqlite3.Row
    cur_users = conn_users.cursor()

    # Pobierz user_id
    cur_users.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_row = cur_users.fetchone()
    if not user_row:
        conn_users.close()
        return None
    user_id = user_row['id']

    # Pobierz wszystkie adresy MAC powiązane z tym użytkownikiem
    cur_users.execute("SELECT mac_address FROM user_boards WHERE user_id = ?", (user_id,))
    boards = cur_users.fetchall()
    conn_users.close()

    # Lista adresów MAC
    mac_addresses = [row['mac_address'] for row in boards]
    if not mac_addresses:
        return None

    # Krok 2: Wyszukaj najnowszą podróż dla tych adresów MAC
    conn_journeys = sqlite3.connect('journeys.db')
    cur_journeys = conn_journeys.cursor()

    # Przygotowanie placeholderów dla klauzuli IN SQL
    placeholders = ','.join('?' for _ in mac_addresses)
    query = f"""
        SELECT id 
        FROM journeys 
        WHERE mac_address IN ({placeholders})
        ORDER BY start_time DESC 
        LIMIT 1
    """
    cur_journeys.execute(query, mac_addresses)
    latest_journey = cur_journeys.fetchone()
    conn_journeys.close()

    return latest_journey[0] if latest_journey else None



@bp.route('/current_journey', methods=['GET'])
def current_journey():
    latest_journey_id = get_latest_journey_id_for_user()
    if latest_journey_id:
        return redirect(url_for('journey_details.journey_details', journey_id=latest_journey_id))
    else:
        return "Nie znaleziono aktualnej podróży.", 404
