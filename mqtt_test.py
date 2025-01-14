import paho.mqtt.client as mqtt

# Dictionary to store PINs (hardcoded for now)
pins = {
    "user1": "111222",
    "user2": "567855"
}

# MQTT settings
BROKER_ADDRESS = "192.168.1.15"
BROKER_PORT = 1883
TOPIC_RECEIVE = "BlackBox/+/+/Pin"
TOPIC_RESPONSE_TEMPLATE = "BlackBox/{username}/{mac}/Response"

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(TOPIC_RECEIVE)

def on_message(client, userdata, msg):
    try:
        # Parse topic - format is BlackBox/user1/MAC/Pin
        topic_parts = msg.topic.split("/")
        username = topic_parts[1]  # Wyciągamy username z topicu (np. "user1")
        mac = topic_parts[2]       # Wyciągamy MAC z topicu
        pin_received = msg.payload.decode("utf-8")  # PIN jest w wiadomości jako prosty string
        
        print(f"Received message:")
        print(f"Username (from topic): {username}")
        print(f"MAC: {mac}")
        print(f"PIN (from payload): {pin_received}")
        
        # Sprawdzamy czy user istnieje i czy PIN się zgadza
        if username in pins and pins[username] == pin_received:
            response = "1"
        else:
            response = "0"
            
        response_topic = TOPIC_RESPONSE_TEMPLATE.format(username=username, mac=mac)
        client.publish(response_topic, response)
        print(f"Sent response to {response_topic}: {response}")
        
    except Exception as e:
        print(f"Error processing message: {e}")

# Create MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
client.connect(BROKER_ADDRESS, BROKER_PORT, 60)

# Start the MQTT loop
client.loop_forever()