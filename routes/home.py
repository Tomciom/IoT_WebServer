from flask import Blueprint, render_template, session, request, jsonify

bp = Blueprint('home', __name__)

@bp.route('/', methods=['GET', 'POST'])
def home():
    username = session.get('username')
    if request.method == 'POST':
        newCode = request.json  # Receive the JSON data
        try:
            print("Received configuration:", newCode)
            # You can process or pass the data to another module here
            return jsonify({'message': 'Kod został zapisany!'}), 200
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({'message': 'Wystąpił błąd podczas zapisywania kodu.'}), 500
    return render_template('home.html', username=username)