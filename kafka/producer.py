import confluent_kafka as kafka
import socket
import json, os, time

producer = kafka.Producer({
    'bootstrap.servers': "localhost:9091,localhost:9092,localhost:9093",
    'client.id': socket.gethostname()
})

topic = "NYTickets"

def acked(err, msg):
    if err is not None:
        print("Failed to deliver message: %s: %s" % (str(msg), str(err)))
    else:
        print("Message produced: %s" % (str(msg)))

def send_tickets(file):
    columns = None
    with open(file) as f:
        for line in f:
            vals = line.strip().split(",")
            vals = [v.strip() for v in vals]
            if columns is None:
                columns = vals
                continue
            key = vals[0]  # Use Summons Number as key
            msg = dict(zip(columns, vals))
            val = json.dumps(msg)
            producer.produce(topic, key=key, value=val, callback=acked)
            producer.poll(0)
            print(f"Sent data {key}")#:{val}")
            #time.sleep(0.01)

data_dir = "../data"
files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".csv")]

for file in files:
    send_tickets(file)
    print(f"Finished sending data for {file}")

producer.flush()
print("Finished sending all data")
