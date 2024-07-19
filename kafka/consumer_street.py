import confluent_kafka as kafka, socket
import os, socket, json

consumer = kafka.Consumer({
    'bootstrap.servers': "localhost:9091,localhost:9092,localhost:9093",
    'client.id': socket.gethostname(),
    'group.id': 'test_group',
    'auto.offset.reset': 'earliest'
})

topic = "NYTickets"
consumer.subscribe([topic])

streets = [street.strip().upper() for street in """
Broadway
3rd Ave
5th Ave
Madison Ave
Lexington Ave
2nd Ave
1st Ave
Queens Blvd
8th Ave
7th Ave
""".split("\n") if street]

window_size = 12
values = {} # key: street, value: list of vehicle years
try:
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            raise Exception(msg.error())
        else:
            # key = msg.key().decode('utf-8')
            val = msg.value().decode('utf-8')
            time = msg.timestamp()[1]

            ticket = json.loads(val)
            key = ticket["Street"].upper()
            if key not in streets:
                continue
            year = int(ticket["Vehicle Year"])

            if key not in values:
                values[key] = []
            values[key].append(year)

            if len(values[key]) > window_size:
                values[key].pop(0)
            
            if len(values[key]) < window_size:
                continue

            avg_year = sum(values[key]) / window_size
            std_dev = (sum([(v - avg_year) ** 2 for v in values[key]]) / window_size) ** 0.5
            min_year = min(values[key])
            max_year = max(values[key])

            print(f"Received {window_size} tickets for {key}. Average Vehicle Year: {avg_year:.2f} +/- {std_dev:.2f}. Min: {min_year}, Max: {max_year}")
            
            invalid = [v for v in values[key] if v < 1885 or v > 2024]
            if invalid:
                print(f"Found invalid years {invalid} for street {key}")

except KeyboardInterrupt:
    print("Consumer interrupted.")
finally:
    consumer.close()

print("Finished receiving all data")
