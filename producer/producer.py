from kafka import KafkaProducer
import uuid
import json
import collections
from datetime import datetime
import os
from fastapi import FastAPI

app = FastAPI()


# user login endpoint (simulates a user login action)
@app.get("/login")
def login():
    """
    data is of the form
    {"userId": <guid>, "action": "login", "timestamp": <iso formatted time>}
    """
    userId = str(uuid.uuid4())
    data["userId"] = userId
    data["action"] = "login"
    tstamp = datetime.now().isoformat()
    data["timestamp"] = tstamp

    # push the message to the metrics topic
    producer.send("metrics", json.dumps(data).encode("utf-8"))

    # flush the producer to ensure all message data has been pushed before exiting the program
    producer.flush()

    # return message stating the message has been sent
    return {"message": f"Login event for user {userId} sent to Kafka topic 'metrics'"}


### main (initialization)
# set kafka broker host (localhost:9092 if not available as an env. variable)
host = (
    "localhost:9092" if "KAFKA_BROKER" not in os.environ else os.environ["KAFKA_BROKER"]
)
# return a reference to producer object to push events/messages to the kafka broker
producer = KafkaProducer(bootstrap_servers=host)
# dictionary to specify the data that needs to be pushed to the broker
data = collections.defaultdict(str)
### end main
