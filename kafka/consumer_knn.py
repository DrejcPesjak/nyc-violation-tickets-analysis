import confluent_kafka as kafka
import json
import numpy as np
from collections import defaultdict
from sklearn.metrics import mean_squared_error
from datetime import datetime
from sklearn.preprocessing import OneHotEncoder

class VehicleYearInferenceConsumer:
    def __init__(self, topic, bootstrap_servers, group_id):
        self.consumer = kafka.Consumer({
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'earliest'
        })
        # self.producer = kafka.Producer({
        #     'bootstrap.servers': bootstrap_servers
        # })
        self.topic = topic
        self.consumer.subscribe([topic])
        self.samples = defaultdict(list)
        self.centroids = {}
        self.sample_count = defaultdict(int)
        self.total_samples = 0
        self.warmup_complete = False

        self.categorical_columns = ['Registration State', 'Plate Type', 'Vehicle Body Type', 'Vehicle Make', 
                                    'Issuing Agency', 'Vehicle Color']
        self.numeric_columns = ['Violation Code', 'Street Code1', 'Street Code2', 'Street Code3', 
                                'Violation Precinct', 'Issuer Precinct', 'Issuer Code', 
                                'Feet From Curb', 'Violation Location', 'Unregistered Vehicle?']
        self.date_columns = ['Issue Date', 'Vehicle Expiration Date', 'Date First Observed']
        self.time_columns = ['Violation Time']

        self.onehot_encoders = {col: OneHotEncoder(handle_unknown='ignore') for col in self.categorical_columns}
        self.prepare_encoders()

    def prepare_encoders(self):
        # Load unique values from JSON file
        with open('unique_values.json', 'r') as f:
            unique_values = json.load(f)
        
        # Replace NaN (which is a float) with "Unknown"
        for key, values in unique_values.items():
            unique_values[key] = ["Unknown" if isinstance(v, float) and np.isnan(v) else v for v in values]
        
        # Fit one-hot encoders with the unique values
        for column, encoder in self.onehot_encoders.items():
            unique_value_array = np.array(unique_values[column]).reshape(-1, 1)
            encoder.fit(unique_value_array)

    def extract_features(self, record):
        features = []
        
        # Handle numeric columns
        for column in self.numeric_columns:
            value = record.get(column, 0)
            try:
                features.append(float(value) if value else 0.0)
            except ValueError:
                features.append(0.0)
        
        # Handle categorical columns with one-hot encoding
        for column in self.categorical_columns:
            value = record.get(column, 'Unknown')
            encoded = self.onehot_encoders[column].transform([[value]]).toarray().flatten()
            features.extend(encoded.tolist())
        
        # Handle date columns
        for column in self.date_columns:
            date_str = record.get(column, '01/01/1970')
            try:
                if '/' not in date_str:
                    date_obj = datetime.strptime(date_str, '%Y%m%d')
                else:
                    date_obj = datetime.strptime(date_str, '%m/%d/%Y')
            except ValueError:
                # print(f"Invalid date format {date_str}")
                date_obj = datetime.strptime('01/01/1970', '%m/%d/%Y')
            features.extend([date_obj.year, date_obj.month, date_obj.day])
        
        # Handle time columns
        for column in self.time_columns:
            time_str = record.get(column, '0000A')
            minutes = self.convert_to_minutes(time_str)
            features.append(minutes)
        
        return np.array(features)

    def convert_to_minutes(self, time_str):
        if time_str[-1] == 'P' and int(time_str[:2]) != 12:
            minutes = (int(time_str[:2]) + 12) * 60 + int(time_str[2:4])
        elif time_str[-1] == 'A' and int(time_str[:2]) == 12:
            minutes = int(time_str[2:4])
        else:
            minutes = int(time_str[:2]) * 60 + int(time_str[2:4])
        return minutes
    
    def collect_samples(self, record):
        vehicle_year = int(record['Vehicle Year'])
        if vehicle_year != 0:
            features = self.extract_features(record)
            self.samples[vehicle_year].append(features)
            self.sample_count[vehicle_year] += 1
            if self.sample_count[vehicle_year] == 1000 and vehicle_year not in self.centroids:
                self.calculate_centroid(vehicle_year)

    def calculate_centroid(self, vehicle_year):
        self.centroids[vehicle_year] = np.mean(self.samples[vehicle_year], axis=0)
        self.samples[vehicle_year] = []
        if len(self.centroids) >= 10:
            self.warmup_complete = True
        print(f"Calculated centroid for vehicle year {vehicle_year}")

    def update_centroid(self, vehicle_year):
        if vehicle_year in self.centroids:
            current_centroid = self.centroids[vehicle_year]
            total_count = self.sample_count[vehicle_year]
            new_samples = np.array(self.samples[vehicle_year])
            new_count = len(new_samples)
            current_count = total_count - new_count
            
            updated_centroid = (current_centroid * current_count + new_samples.mean(axis=0) * new_count) / (current_count + new_count)
            
            self.centroids[vehicle_year] = updated_centroid
            # self.sample_count[vehicle_year] += new_count
            self.samples[vehicle_year] = []
            print(f"Updated centroid for vehicle year {vehicle_year}")

    def infer_vehicle_year(self, features):
        distances = {year: np.linalg.norm(features - centroid) for year, centroid in self.centroids.items()}
        return min(distances, key=distances.get)

    def evaluate_model(self):
        known_years = []
        inferred_years = []
        for year, samples in self.samples.items():
            for sample in samples[:100]:
                inferred_year = self.infer_vehicle_year(sample)
                known_years.append(year)
                inferred_years.append(inferred_year)
        rmse = mean_squared_error(known_years, inferred_years, squared=False)
        print(f"RMSE: {rmse}")
        abs_avg_error = np.mean(np.abs(np.array(known_years) - np.array(inferred_years)))
        print(f"Mean Absolute Error: {abs_avg_error}")

    def run(self):
        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    raise Exception(msg.error())
                else:
                    record = json.loads(msg.value().decode('utf-8'))
                    try:
                        vehicle_year = int(record['Vehicle Year'])
                    except ValueError:
                        vehicle_year = 0
                        print(f"Invalid vehicle year {record['Vehicle Year']} for ticket {record['Summons Number']}")
                    self.total_samples += 1

                    if vehicle_year == 0:
                        if self.warmup_complete:
                            features = self.extract_features(record)
                            inferred_year = self.infer_vehicle_year(features)
                            record['Vehicle Year'] = inferred_year
                            # self.producer.produce('inferred_vehicle_years', key=str(record['Summons Number']), value=json.dumps(record))
                            print(f"Inferred vehicle year {inferred_year} for ticket {record['Summons Number']}")
                    else:
                        self.collect_samples(record)
                        # print(self.sample_count)
                        if (self.sample_count[vehicle_year]+1) % 1000 == 0 and vehicle_year in self.centroids:
                            self.update_centroid(vehicle_year)

                    if self.total_samples % 3000 == 0 and self.warmup_complete:
                        self.evaluate_model()
        except KeyboardInterrupt:
            print("Consumer interrupted.")
        finally:
            self.consumer.close()
            print("Finished receiving all data")

if __name__ == "__main__":
    consumer = VehicleYearInferenceConsumer(
        topic='NYTickets',
        bootstrap_servers='localhost:9091,localhost:9092,localhost:9093',
        group_id='vehicle_year_inference'
    )
    consumer.run()
