import confluent_kafka as kafka, socket
import os, socket, json
from datetime import date

consumer = kafka.Consumer({
    'bootstrap.servers': "localhost:9091,localhost:9092,localhost:9093",
    'client.id': socket.gethostname(),
    'group.id': 'test_group',
    'auto.offset.reset': 'earliest'
})

topic = "NYTickets"
consumer.subscribe([topic])

window_size = 12
sum_year, count = 0, 0
min_y, max_y = 3000, 0
try:
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            raise Exception(msg.error())
        else:
            # Avg Vehicle Year
            key = msg.key().decode('utf-8')
            val = msg.value().decode('utf-8')
            time = msg.timestamp()[1]
            # print(f"Received data {key}:{val} at time {time}")

            ticket = json.loads(val)
            year = int(ticket["Vehicle Year"])

            curr_year = date.today().year
            if year < 1885 or year > curr_year: # First car was made in 1885
                print(f"Found invalid year {year} for ticket {key}")
                continue
            
            sum_year += year
            count += 1

            if year < min_y:
                min_y = year
                print(f"Found new oldest vehicle {ticket['Vehicle Make']} {year}")
            if year > max_y:
                max_y = year
                print(f"Found new newest vehicle {ticket['Vehicle Make']} {year}")
            
            if count % window_size == 0:
                avg_year = sum_year / window_size
                print(f"Received {window_size} tickets. Average Vehicle Year: {avg_year:.2f}")
                sum_year = 0
                count = 0

except KeyboardInterrupt:
    print("Consumer interrupted.")
finally:
    consumer.close()

print("Finished receiving all data")
