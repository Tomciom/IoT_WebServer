import requests

mac_address = "12:34:56:78:9A:BC"

response = requests.get('http://localhost:5000/get_code')
print("Response status code:", response.status_code)
try:
    code_data = response.json()
    print("GET response:", code_data)
except ValueError as e:
    print(f"JSON decoding failed: {e}")

print("Current code:", code_data['code'])
print("Current username:", code_data['username'])
if code_data['code'] != "00000":
    # Wysyłanie żądania POST z danymi JSON
    data_to_send = {"mac_address": mac_address, "username": code_data['username'], "value": 100}
    response = requests.post('http://localhost:5000/send_mac', json=data_to_send)

