import json
import pika
import sys


rabbitmq_settings = json.load(open("rabbitmq.json", "r", encoding="utf-8"))
RABBITMQ_HOST = rabbitmq_settings["ENDPOINT"]
RABBITMQ_PORT = rabbitmq_settings["PORT"]
RABBITMQ_QUEUE = rabbitmq_settings["QUEUE"]


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=str(RABBITMQ_HOST), port=int(RABBITMQ_PORT)))
channel = connection.channel()

channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

data = {
    "gcode": "G28",
    "filename": "test.gcode",
    "printer_type": "p1p"
}

channel.basic_publish(
    exchange='',
    routing_key=RABBITMQ_QUEUE,
    body=json.dumps(data),
    properties=pika.BasicProperties(
        delivery_mode=pika.DeliveryMode.Persistent
    ))
print(f" [x] Sent {data}")
connection.close()