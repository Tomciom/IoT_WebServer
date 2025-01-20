from flask import Flask, jsonify, request
from routes import home, journey_history,latest_journey, login, register, new_journey, journey_details, boards
import config, sqlite3
import sqlite3


def create_journeys():
    conn = sqlite3.connect('journeys.db')
    c = conn.cursor()

    # Tabela podróży
    c.execute('''
        CREATE TABLE IF NOT EXISTS journeys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            is_current BOOLEAN DEFAULT 0,
            mac_address TEXT
        )
    ''')

    # Tabela temperatury i ciśnienia
    c.execute('''
        CREATE TABLE IF NOT EXISTS temperature_pressure (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            journey_id INTEGER,
            timestamp TIMESTAMP NOT NULL,
            temperature REAL NOT NULL,
            pressure REAL NOT NULL,
            mac_address TEXT,
            FOREIGN KEY (journey_id) REFERENCES journeys (id)
        )
    ''')

    # Tabela wykrycia ognia
    c.execute('''
        CREATE TABLE IF NOT EXISTS fire_detection (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            journey_id INTEGER,
            timestamp TIMESTAMP NOT NULL,
            fire_detected INTEGER NOT NULL,
            sensor_value REAL NOT NULL,
            mac_address TEXT,
            FOREIGN KEY (journey_id) REFERENCES journeys (id)
        )
    ''')

    # Tabela obrotu i przyspieszenia
    c.execute('''
        CREATE TABLE IF NOT EXISTS rotation_acceleration (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            journey_id INTEGER,
            timestamp TIMESTAMP NOT NULL,
            rotation_degrees_x REAL NOT NULL,
            rotation_degrees_y REAL NOT NULL,
            rotation_degrees_z REAL NOT NULL,
            gx REAL NOT NULL,
            gy REAL NOT NULL,
            gz REAL NOT NULL,
            mac_address TEXT,
            FOREIGN KEY (journey_id) REFERENCES journeys (id)
        )
    ''')

    conn.commit()
    conn.close()


def init_db():



    conn = sqlite3.connect('Users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    pin VARCHAR(6))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_boards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    mac_address TEXT NOT NULL,
                    board_name TEXT,
                    is_in_use INTEGER DEFAULT 0 NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    
    conn.commit()


    conn.close()

def save_mac_to_db(username, mac_address):
    # Połącz się z bazą Users.db w celu aktualizacji tabeli user_boards
    conn_users = sqlite3.connect('Users.db')
    cur_users = conn_users.cursor()

    # Uzyskaj user_id na podstawie username
    cur_users.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cur_users.fetchone()
    if result is None:
        conn_users.close()
        raise ValueError(f"User with username '{username}' not found.")
    user_id = result[0]


    # Sprawdzenie, czy dany adres MAC jest powiązany z innym użytkownikiem
    cur_users.execute("SELECT user_id FROM user_boards WHERE mac_address = ?", (mac_address,))
    existing_rows = cur_users.fetchall()
    remove_journeys = False
    for (existing_user_id,) in existing_rows:
        if existing_user_id != user_id:
            # Znaleziono innego użytkownika przypisanego do tej płytki
            remove_journeys = True
            break

    # Usuń istniejące wpisy dla danego user_id i mac_address
    cur_users.execute(
        "DELETE FROM user_boards WHERE mac_address = ?",
        (mac_address,)
    )
    conn_users.commit()
    
    # Wstaw nowy wpis dla danej płytki i użytkownika
    cur_users.execute(
        "INSERT INTO user_boards (user_id, mac_address) VALUES (?, ?)",
        (user_id, mac_address)
    )
    conn_users.commit()
    conn_users.close()

    # Jeżeli płytka była wcześniej przypisana do innego użytkownika,
    # usuwamy powiązane podróże i dane.
    if remove_journeys:
        conn_journeys = sqlite3.connect('journeys.db')
        cur_journeys = conn_journeys.cursor()
        
        # Pobranie identyfikatorów podróży powiązanych z tą płytką
        cur_journeys.execute(
            "SELECT id FROM journeys WHERE mac_address = ?",
            (mac_address,)
        )
        journey_ids = cur_journeys.fetchall()
        
        # Usunięcie powiązanych rekordów z tabel pomocniczych dla każdej podróży
        for (journey_id,) in journey_ids:
            cur_journeys.execute(
                "DELETE FROM temperature_pressure WHERE journey_id = ?",
                (journey_id,)
            )
            cur_journeys.execute(
                "DELETE FROM fire_detection WHERE journey_id = ?",
                (journey_id,)
            )
            cur_journeys.execute(
                "DELETE FROM rotation_acceleration WHERE journey_id = ?",
                (journey_id,)
            )
        
        # Usunięcie samych podróży powiązanych z tą płytką
        cur_journeys.execute(
            "DELETE FROM journeys WHERE mac_address = ?",
            (mac_address,)
        )
        conn_journeys.commit()
        conn_journeys.close()



def send_mac():
    try:
        received_data = request.json
        print("Received data:", received_data)
        save_mac_to_db(received_data['username'], received_data['mac_address'])
        response = {"response": f"Data received: {received_data['mac_address']}"}
        return jsonify(response), 200
    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({"error": "Invalid request"}), 400

    
def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    app.register_blueprint(boards.bp)
    app.register_blueprint(home.bp)
    app.register_blueprint(journey_history.bp)
    app.register_blueprint(journey_details.bp)
    app.register_blueprint(latest_journey.bp)
    app.register_blueprint(login.bp)
    app.register_blueprint(register.bp)
    app.register_blueprint(new_journey.bp)

    app.add_url_rule('/send_mac', view_func=send_mac, methods=['POST'])
    


    return app

if __name__ == '__main__':
    init_db()
    create_journeys()
    app = create_app()
    app.run(host=config.mqtt_broker, port=5000,debug=config.Config.DEBUG)