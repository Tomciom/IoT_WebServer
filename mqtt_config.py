import paho.mqtt.client as mqtt
import sqlite3
import json
import time
import threading, config
import datetime  # Dodano import dla konwersji daty

# Ustawienia MQTT
BROKER_ADDRESS = config.mqtt_broker
BROKER_PORT = 1883

# Tematy
CONTROL_TOPIC = "BlackBox/+/+/Control"
sensor_topics = [
    ("BlackBox/+/+/mpu6050", 0),
    ("BlackBox/+/+/bmp280", 0),
    ("BlackBox/+/+/ky026", 0)
]

# Tablice do przechowywania danych pomiarowych
mpu6050_data = []
bmp280_data = []
ky026_data = []

receiving_data = False
last_data_time = None

# Połączenie z bazą danych SQLite i tworzenie tabel, jeśli nie istnieją
def create_database():
    global conn, cursor
    conn = sqlite3.connect('journeys.db')
    cursor = conn.cursor()

    # Tabela podróży
    cursor.execute('''
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
    cursor.execute('''
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
    cursor.execute('''
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
    cursor.execute('''
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

def insert_measurement(sensor_table, data):
    # Przygotowuje wstawienie danych do odpowiedniej tabeli
    columns = []
    placeholders = []
    values = []
    for key, value in data.items():
        columns.append(key)
        placeholders.append('?')
        values.append(value)
    cols = ", ".join(columns)
    phs = ", ".join(placeholders)
    sql = f"INSERT INTO {sensor_table} ({cols}) VALUES ({phs})"
    cursor.execute(sql, tuple(values))
    conn.commit()

def handle_stop():
    global receiving_data, mpu6050_data, bmp280_data, ky026_data

    # Wyciąganie wszystkich dat z otrzymanych danych sensorów
    all_datetimes = []
    for d in mpu6050_data + bmp280_data + ky026_data:
        if 'timestamp' in d:
            try:
                # Parsowanie ISO daty z pól timestamp
                dt = datetime.datetime.fromisoformat(d['timestamp'])
                all_datetimes.append(dt)
            except Exception as e:
                print("Błąd parsowania daty:", e)

    if all_datetimes:
        start_time = min(all_datetimes)
        end_time = max(all_datetimes)
    else:
        start_time = None
        end_time = None

    # Wyciągnięcie adresu MAC z pierwszego dostępnego wpisu
    mac = None
    if mpu6050_data:
        mac = mpu6050_data[0].get('mac_address')
    elif bmp280_data:
        mac = bmp280_data[0].get('mac_address')
    elif ky026_data:
        mac = ky026_data[0].get('mac_address')

    if mac:
        try:
            conn_users = sqlite3.connect('Users.db')
            c = conn_users.cursor()
            c.execute("UPDATE user_boards SET is_in_use = 0 WHERE mac_address = ?", (mac,))
            conn_users.commit()
            conn_users.close()
            print(f"Zaktualizowano is_in_use dla {mac} w bazie Users.db.")
        except Exception as e:
            print("Błąd podczas aktualizacji Users.db:", e)

    # Inicjalizacja journey_id
    journey_id = None

    # Wstawienie nowej podróży do tabeli journeys, jeśli są dostępne daty
    if start_time and end_time:
        cursor.execute(
            "INSERT INTO journeys (name, start_time, end_time, is_current, mac_address) VALUES (?,?,?,?,?)",
            ("test", start_time, end_time, False, mac)
        )
        conn.commit()
        journey_id = cursor.lastrowid  # Pobranie ID ostatnio wstawionej podróży

    # Unsubskrybuj tematy sensorowe
    for topic, qos in sensor_topics:
        client.unsubscribe(topic)

    # Dodanie journey_id do danych i wstawienie ich do odpowiednich tabel w bazie
    if journey_id is not None:
        for data in mpu6050_data:
            data['journey_id'] = journey_id
            insert_measurement("rotation_acceleration", data)
        for data in bmp280_data:
            data['journey_id'] = journey_id
            insert_measurement("temperature_pressure", data)
        for data in ky026_data:
            data['journey_id'] = journey_id
            insert_measurement("fire_detection", data)
    else:
        # Jeśli journey_id nie został ustawiony, wstawiamy bez niego
        for data in mpu6050_data:
            insert_measurement("rotation_acceleration", data)
        for data in bmp280_data:
            insert_measurement("temperature_pressure", data)
        for data in ky026_data:
            insert_measurement("fire_detection", data)

    # Wyczyść tablice danych
    mpu6050_data.clear()
    bmp280_data.clear()
    ky026_data.clear()

    receiving_data = False
    print("Dane zapisane do bazy oraz zakończono odbiór danych.")
    
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # Subskrybuj tylko temat kontrolny na początek
    client.subscribe(CONTROL_TOPIC)

def on_message(client, userdata, msg):
    global receiving_data, last_data_time
    topic_parts = msg.topic.split("/")
    payload = msg.payload.decode("utf-8")

    # Obsługa komunikatów kontrolnych
    if topic_parts[-1] == "Control":
        if payload == "1":
            print("Otrzymano sygnał START. Rozpoczynam odbiór danych.")
            receiving_data = True
            last_data_time = time.time()
            # Subskrybuj tematy sensorowe
            for topic, qos in sensor_topics:
                client.subscribe(topic, qos)
        elif payload == "0":
            print("Otrzymano sygnał STOP. Kończę odbiór danych.")
            # Aktualizacja is_in_use w Users.db

            handle_stop()
        return

    # Obsługa danych pomiarowych
    if receiving_data:
        last_data_time = time.time()
        try:
            data = json.loads(payload)  # Parsowanie JSON-a
        except json.JSONDecodeError:
            print("Błąd dekodowania JSON:", payload)
            return

        # Wyciąganie typu sensora i adresu MAC z tematu
        sensor_type = topic_parts[-1]
        mac_address = topic_parts[2]
        data['mac_address'] = mac_address

        # Konwersja timestampu z Unix na ISO format, jeśli obecny
        if 'timestamp' in data:
            try:
                data['timestamp'] = datetime.datetime.fromtimestamp(
                    float(data['timestamp'])
                ).isoformat(' ')
            except Exception as e:
                print("Błąd konwersji timestampu:", e)

        # Zamiana wartości obrotu i przyspieszenia dla MPU6050
        if sensor_type == "mpu6050":
            # Przykładowa zamiana - dostosuj nazwy pól do formatu twoich danych!
            # Zakładamy, że pola rotacji to: rotation_degrees_x, rotation_degrees_y, rotation_degrees_z
            # oraz pola przyspieszenia to: gx, gy, gz
            try:
                # Zamiana wartości między polami obrotu a przyspieszeniem
                data['rotation_degrees_x'], data['gx'] = data.get('gx', 0), data.get('rotation_degrees_x', 0)
                data['rotation_degrees_y'], data['gy'] = data.get('gy', 0), data.get('rotation_degrees_y', 0)
                data['rotation_degrees_z'], data['gz'] = data.get('gz', 0), data.get('rotation_degrees_z', 0)
            except KeyError as e:
                print(f"Nie znaleziono oczekiwanego pola: {e}")

            mpu6050_data.append(data)

        elif sensor_type == "bmp280":
            bmp280_data.append(data)
        elif sensor_type == "ky026":
            ky026_data.append(data)
        else:
            print("Nieznany temat pomiarowy:", msg.topic)
    else:
        print("Otrzymano dane pomiarowe, ale tryb odbioru nie jest aktywny.")

def timeout_monitor():
    global receiving_data, last_data_time
    while True:
        time.sleep(1)
        if receiving_data and last_data_time is not None:
            if time.time() - last_data_time > 20:
                print("Timeout - brak danych przez 20 sekund. Zatrzymuję odbiór.")
                handle_stop()

# Inicjalizacja bazy danych
create_database()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER_ADDRESS, BROKER_PORT, 60)

# Uruchomienie wątku monitorującego timeout
monitor_thread = threading.Thread(target=timeout_monitor, daemon=True)
monitor_thread.start()

client.loop_forever()
