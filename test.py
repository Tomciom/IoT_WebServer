import json

# Oryginalny JSON
data = {
    'journey_name': '',
    'mac_address': '98:3D:AE:EB:38:C4',
    'cargo_type': '0',
    'position_req': '0',
    'transport_type': '0',
    'duration': '0',
    'osrs_p': '0',
    'osrs_t': '0',
    'filter': '0',
    'interval': ''
}

# Usunięcie kluczy
data.pop('journey_name', None)
data.pop('mac_address', None)

# Wynikowy JSON
print(json.dumps(data, indent=4))
