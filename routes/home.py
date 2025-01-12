from flask import Blueprint, render_template, session, request, jsonify

bp = Blueprint('home', __name__)

current_json = {"code": "00000", "username": "noUser","value": 42} 


@bp.route('/get_code', methods=['GET'])
def get_code():
    return jsonify(current_json), 200


@bp.route('/', methods=['GET', 'POST'])
def home():
    username = session.get('username')
    if request.method == 'POST':
        newCode = request.json  # Receive the JSON data
        try:
            current_json['code'] = newCode['code']
            current_json['username'] = username
            print("Received configuration code:", newCode['code'])
            return jsonify({'message': 'Kod został zapisany!'}), 200
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({'message': 'Wystąpił błąd podczas zapisywania kodu.'}), 500
    return render_template('home.html', username=username)