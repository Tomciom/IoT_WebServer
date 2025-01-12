from flask import Flask
from routes import home, journey_history,latest_journey, login, register, new_journey, journey_details
import config
import sqlite3



def init_db():
    #hardcoded
    admin_username = "admin"
    admin_password = "admin"
    mac_address = "12:34:56:78:9A:BC"



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

    c.execute("INSERT INTO user_boards (user_id, mac_address) VALUES (?, ?)", (1, mac_address))
    
    conn.commit()


    conn.close()

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

    return app

if __name__ == '__main__':
    init_db()
    app = create_app()
    app.run(debug=config.Config.DEBUG)