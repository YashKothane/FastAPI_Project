import pika
import json
connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()

channel.queue_declare(queue="test_queue")

def email_sender(body):
    data = json.loads(body.decode())
    email = data["email"]
    msg = data["message"]

def callback(ch, method, properties, body):
    print(f"Received: {body.decode()}")
    email_sender(body)


channel.basic_consume(queue="test_queue", on_message_callback=callback, auto_ack=True)

print("Waiting for messages. Press CTRL+C to stop.")
channel.start_consuming()