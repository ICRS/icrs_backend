import paho.mqtt.client as mqtt
import json
from dateutil import parser


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("monitor/ble/#")


# Dummy database call
def save_to_db(time, name, occupancy):
    print(f"At time {time}, {name} {'arrived' if occupancy else 'departed'}")


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
