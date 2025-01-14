from flask import Blueprint, render_template, session, request, jsonify
import sqlite3

bp = Blueprint('home', __name__)

def send_code(username):
    conn = sqlite3.connect('Users.db')
    c = conn.cursor()
    
    # Wykonaj zapytanie, aby pobrać pin dla danego username
    c.execute("SELECT pin FROM users WHERE username = ?", (username,))
    
    # Pobierz wynik zapytania
    result = c.fetchone()
    
    # Sprawdź, czy wynik istnieje (czy znaleziono użytkownika)
    if result:
        pin = result[0]  # przypisanie pierwszego (i jedynego) elementu do zmiennej pin
        print("Received configuration code:", pin)
    else:
        print("User not found.")
        pin = None  # przypisanie None, jeśli użytkownik nie istnieje
    
    conn.close()
    return pin



@bp.route('/', methods=['GET', 'POST'])
def home():
    username = session.get('username')
    if request.method == 'POST':
        newCode = request.json  # Receive the JSON data
        try:
            conn = sqlite3.connect('Users.db')
            c = conn.cursor()
            c.execute("UPDATE users SET pin = ? WHERE username = ?", (newCode['code'], username))
            print("Received configuration code:", newCode['code'])
            conn.commit()
            conn.close()
            return jsonify({'message': 'Kod został zapisany!'}), 200
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({'message': 'Wystąpił błąd podczas zapisywania kodu.'}), 500
    return render_template('home.html', username=username)