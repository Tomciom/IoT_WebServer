from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
import sqlite3

bp = Blueprint('new_journey', __name__)

def return_json(data, status_code):
    return jsonify(data), status_code

@bp.route('/new_journey', methods=['GET', 'POST'])
def new_journey():
    if request.method == 'GET':
        username = session.get('username')  # Pobierz aktualnie zalogowanego użytkownika
        if not username:
            return redirect(url_for('login.login'))  # Przekierowanie do logowania, jeśli użytkownik niezalogowany
        
        conn = sqlite3.connect('Users.db')
        c = conn.cursor()
        
        # Pobierz ID użytkownika na podstawie nazwy użytkownika
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_id = c.fetchone()
        
        if user_id:
            user_id = user_id[0]
            # Pobierz wszystkie adresy MAC powiązane z użytkownikiem
            c.execute("SELECT mac_address FROM user_boards WHERE user_id = ?", (user_id,))
            user_macs = [row[0] for row in c.fetchall()]
        else:
            user_macs = []
        
        conn.close()
        return render_template('new_journey.html', mac_addresses=user_macs)


    if request.method == 'POST':
        data = request.json  # Receive the JSON data
        try:
            print("Received configuration:", data)
            # You can process or pass the data to another module here
            return redirect(url_for('home.home'))  # Redirect after processing
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({'message': 'Wystąpił błąd podczas zapisywania konfiguracji.'}), 500
    return render_template('new_journey.html')
