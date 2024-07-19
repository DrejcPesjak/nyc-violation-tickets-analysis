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

window_size = 12
values = {} # key: borough, value: list of vehicle years
try:
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            raise Exception(msg.error())
        else:
            # key = msg.key().decode('utf-8') # Summons Number
            val = msg.value().decode('utf-8')
            time = msg.timestamp()[1]

            ticket = json.loads(val)
            key = ticket["Violation County"]
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
                print(f"Found invalid years {invalid} for borough {key}")


except KeyboardInterrupt:
    print("Consumer interrupted.")
finally:
    consumer.close()

print("Finished receiving all data")
