from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
import sqlite3
import paho.mqtt.client as mqtt
import json
import config
from time import sleep as Sleep

bp = Blueprint('new_journey', __name__)

# Konfiguracja MQTT
mqtt_broker = config.mqtt_broker  # Adres brokera MQTT
mqtt_port = 1883

@bp.route('/new_journey', methods=['GET', 'POST'])
def new_journey():
    username = session.get('username')
    if request.method == 'GET':
        username = session.get('username')  # Pobierz aktualnie zalogowanego użytkownika
        if not username:
            return redirect(url_for('login.login'))  # Przekierowanie do logowania, jeśli użytkownik niezalogowany

        conn = sqlite3.connect('Users.db')
        c = conn.cursor()

        # Pobierz ID użytkownika na podstawie nazwy użytkownika
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_id_row = c.fetchone()

        boards = []
        if user_id_row:
            user_id = user_id_row[0]
            # Pobierz adresy MAC oraz nazwy płyt powiązane z użytkownikiem
            c.execute("SELECT mac_address, board_name FROM user_boards WHERE user_id = ?", (user_id,))
            boards = [{'mac_address': row[0], 'board_name': row[1]} for row in c.fetchall()]

        conn.close()
        # Przekazujemy listę płyt do szablonu jako 'boards'
        return render_template('new_journey.html', username=username, boards=boards)

    if request.method == 'POST':
        username = session.get('username')
        data = request.json  # Odbierz dane JSON z żądania
        try:
            print("Received configuration:", data)
            mac = data['mac_address']
            # Usuń niepotrzebne klucze przed wysłaniem
            data.pop('journey_name', None)
            data.pop('mac_address', None)
            print(f"json: {data}")

            # Konfiguracja klienta MQTT
            mqtt_client = mqtt.Client()
            mqtt_client.connect(mqtt_broker, mqtt_port, 60)

            # Wyślij dane JSON do MQTT
            mqtt_topic = f"BlackBox/{username}/{mac}/Config"
            print(f"Publishing to topic {mqtt_topic}: {json.dumps(data)}")
            mqtt_client.publish(mqtt_topic, json.dumps(data))

            # Lista do przechowywania odebranych wiadomości
            messages_received = []

            # Definicja funkcji on_message, która zapisuje wiadomości do listy
            def on_message(client, userdata, msg):
                messages_received.append(msg)

            mqtt_client.on_message = on_message
            topic = "BlackBox/+/+/ConfigResponse"
            mqtt_client.subscribe(topic)

            # Uruchomienie pętli sieciowej MQTT, aby odebrać odpowiedzi
            mqtt_client.loop_start()
            Sleep(1)  # Czekaj na odpowiedzi przez określony czas
            mqtt_client.loop_stop()

            # Przetwarzanie odebranych wiadomości i aktualizacja bazy danych
            for msg in messages_received:
                try:
                    # Parsowanie tematu i ładunku wiadomości
                    topic_parts = msg.topic.split("/")
                    topic_username = topic_parts[1]  # Nazwa użytkownika z tematu
                    topic_mac = topic_parts[2]       # MAC z tematu
                    pin_received = msg.payload.decode("utf-8")  # PIN z ładunku
                    print(f"Otrzymano wiadomość dla użytkownika: {topic_username}, MAC: {topic_mac}, PIN: {pin_received}")

                    # Sprawdzenie, czy wiadomość dotyczy aktualnie zalogowanego użytkownika
                    if topic_username == username:
                        conn = sqlite3.connect('Users.db')
                        c = conn.cursor()
                        # Pobranie ID użytkownika z bazy danych
                        c.execute("SELECT id FROM users WHERE username = ?", (username,))
                        user_id = c.fetchone()
                        if user_id:
                            user_id = user_id[0]
                            # Aktualizacja pola is_in_use w tabeli user_boards dla danego użytkownika
                            c.execute("UPDATE user_boards SET is_in_use = ? WHERE user_id = ?", (int(pin_received), int(user_id)))
                            conn.commit()
                            print(f"Aktualizacja PIN {pin_received} dla użytkownika {username} zakończona pomyślnie.")
                        conn.close()
                except Exception as e:
                    print(f"Błąd podczas przetwarzania wiadomości: {e}")

            return redirect(url_for('home.home'))  # Przekierowanie po przetwarzzeniu danych

        except Exception as e:
            print(f"Error: {e}")
            return jsonify({'message': 'Wystąpił błąd podczas wysyłania danych przez MQTT.'}), 500

    # Domyślny zwrot, chociaż nie powinien tu dojść
    return render_template('new_journey.html',username=username, boards=boards)

