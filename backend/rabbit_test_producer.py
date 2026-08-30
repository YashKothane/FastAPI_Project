import pika
import json

params=pika.ConnectionParameters("localhost")
connection = pika.BlockingConnection(params)
channel = connection.channel()

# Declare the queue — creates it if it doesn't exist yet.
# Safe to call every time; it won't duplicate or error if it already exists.
channel.queue_declare(queue="test_queue")
data={
    "email":"yashkothane@gmail.com",
    "message":"Hello this message is from Rabbit Mq server, This is a automated message kindly do not respond"
}

channel.basic_publish(
    exchange="",              # "" = the default exchange, routes by queue name directly
    routing_key="test_queue", # which queue to send to
    body=json.dumps(data),
   
)

print("Sent a message!")
connection.close()