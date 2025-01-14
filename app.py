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
                    username TEXT NOT NULL,
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

def save_mac_to_db(mac_address):
    conn = sqlite3.connect('Users.db')
    c = conn.cursor()
    c.execute("INSERT INTO user_boards (user_id, mac_address) VALUES (?, ?)", (1, mac_address))
    conn.commit()
    conn.close()

def send_mac():
    try:
        received_data = request.json
        print("Received data:", received_data)
        save_mac_to_db(received_data['mac_address'])
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
    app.run(host='192.168.1.15', port=5000,debug=config.Config.DEBUG)