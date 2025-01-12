from flask import Flask, jsonify, request
from routes import home, journey_history,latest_journey, login, register, new_journey, journey_details
import config, sqlite3
import sqlite3



def init_db():
    #hardcoded
    admin_username = "admin"
    admin_password = "admin"



    conn = sqlite3.connect('Users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_boards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    mac_address TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (admin_username, admin_password))
    
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
    app = create_app()
    app.run(debug=config.Config.DEBUG)