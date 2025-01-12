import sqlite3
import time
import random
from datetime import datetime, timedelta

# Tworzenie bazy danych i tabel
def create_database():
    conn = sqlite3.connect('journeys.db')
    c = conn.cursor()

    # Tabela podróży
    c.execute('''
        CREATE TABLE IF NOT EXISTS journeys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            is_current BOOLEAN DEFAULT 0
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
            FOREIGN KEY (journey_id) REFERENCES journeys (id)
        )
    ''')

    conn.commit()
    conn.close()

# Dodawanie nowej podróży
def add_new_journey(journey_name):
    conn = sqlite3.connect('journeys.db')
    c = conn.cursor()
    start_time = datetime.now()
    c.execute('''
        INSERT INTO journeys (name, start_time, is_current)
        VALUES (?, ?, 1)
    ''', (journey_name, start_time))
    conn.commit()
    journey_id = c.lastrowid
    conn.close()
    return journey_id

# Aktualizacja podróży (ustawienie zakończenia)
def end_journey(journey_id):
    conn = sqlite3.connect('journeys.db')
    c = conn.cursor()
    end_time = datetime.now()
    c.execute('''
        UPDATE journeys
        SET end_time = ?, is_current = 0
        WHERE id = ?
    ''', (end_time, journey_id))
    conn.commit()
    conn.close()

# Generowanie danych pomiarowych
def generate_data(journey_id):
    conn = sqlite3.connect('journeys.db')
    c = conn.cursor()

    # Symulowane wartości
    timestamp = datetime.now()
    temperature = round(random.uniform(-10, 30), 2)  # Temperatura w °C
    pressure = round(random.uniform(950, 1050), 2)  # Ciśnienie w hPa
    fire_detected = random.choice([0, 1])  # Wykrycie ognia (0 = brak, 1 = wykryto)
    sensor_value = round(random.uniform(0, 100), 2)  # Wartość czujnika ognia
    rotation_degrees_x = round(random.uniform(0, 360), 2)  # Obrót w stopniach
    rotation_degrees_y = round(random.uniform(0, 360), 2)  # Obrót w stopniach
    rotation_degrees_z = round(random.uniform(0, 360), 2)  # Obrót w stopniach
    gx = round(random.uniform(-10, 10), 2)  # Przyspieszenie w osi X
    gy = round(random.uniform(-10, 10), 2)  # Przyspieszenie w osi Y
    gz = round(random.uniform(-10, 10), 2)  # Przyspieszenie w osi Z

    # Wstawianie do tabel
    c.execute('''
        INSERT INTO temperature_pressure (journey_id, timestamp, temperature, pressure)
        VALUES (?, ?, ?, ?)
    ''', (journey_id, timestamp, temperature, pressure))

    c.execute('''
        INSERT INTO fire_detection (journey_id, timestamp, fire_detected, sensor_value)
        VALUES (?, ?, ?, ?)
    ''', (journey_id, timestamp, fire_detected, sensor_value))

    c.execute('''
        INSERT INTO rotation_acceleration (journey_id, timestamp, rotation_degrees_x, rotation_degrees_y, rotation_degrees_z, gx, gy, gz)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (journey_id, timestamp, rotation_degrees_x, rotation_degrees_y, rotation_degrees_z, gx, gy, gz))

    conn.commit()
    conn.close()

# Główna funkcja
if __name__ == '__main__':
    create_database()
    journey_id = add_new_journey("Podróż Testowa")

    try:
        while True:
            generate_data(journey_id)
            print(f"Dodano nowe dane dla podróży ID {journey_id}.")
            time.sleep(1)  # Czas między odczytami (w sekundach)
    except KeyboardInterrupt:
        print("Kończenie podróży...")
        end_journey(journey_id)
        print(f"Podróż ID {journey_id} zakończona.")
