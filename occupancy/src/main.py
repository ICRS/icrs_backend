import paho.mqtt.client as mqtt
import json
import datetime
from dateutil import parser
import os
import requests

def get_env_string(env_name: str) -> str:
    return str(os.getenv(env_name)).strip()
DATABASE_URL = get_env_string("DATABASE_ADAPTER_ENDPOINT")

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("monitor/ble/#")


# Dummy database call
def save_to_db(time:datetime.datetime, name:str, occupancy:bool):
    try:
        response = requests.post(
            f"{DATABASE_URL}/occupancy",
            json={
                "time": time.isoformat(),
                "name": name,
                "occupancy": occupancy,
            }
        )
        print(f"Saved to DB: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Failed to save to DB: {e}")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    try:
        if msg.topic.split("/")[-1] not in ["status", "rssi"]:
            msg = json.loads(msg.payload.decode("utf-8"))
            occupancy = True if int(msg['confidence']) >= 45 else False
            name = msg['name']
            time = parser.parse(msg['timestamp'])
            save_to_db(time, name, occupancy)
    except Exception as e:
        print(f"Error reading message from topic {msg.topic}: {e}")


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "occupancyLogger")
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.connect("localhost", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
mqttc.loop_forever()
