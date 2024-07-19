import confluent_kafka as kafka
import json
import numpy as np
from sklearn.decomposition import IncrementalPCA
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import mean_squared_error
from datetime import datetime

class VehicleYearInferenceWithIPCAKNN:
    def __init__(self, topic, bootstrap_servers, group_id):
        self.consumer = kafka.Consumer({
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'earliest'
        })
        self.topic = topic
        self.consumer.subscribe([topic])
        
        self.categorical_columns = ['Registration State', 'Plate Type', 'Vehicle Body Type', 'Vehicle Make', 
                                    'Issuing Agency', 'Vehicle Color']
        self.numeric_columns = ['Violation Code', 'Street Code1', 'Street Code2', 'Street Code3', 
                                'Violation Precinct', 'Issuer Precinct', 'Issuer Code', 
                                'Feet From Curb', 'Violation Location', 'Unregistered Vehicle?']
        self.date_columns = ['Issue Date', 'Vehicle Expiration Date', 'Date First Observed']
        self.time_columns = ['Violation Time']

        self.onehot_encoders = {col: OneHotEncoder(handle_unknown='ignore') for col in self.categorical_columns}
        self.scaler = StandardScaler()
        self.ipca = IncrementalPCA(n_components=10)
        self.knn = KNeighborsRegressor(n_neighbors=5)
        self.buffer = []
        self.total_samples = 0
        self.mean_shift = 2000
        self.prepare_encoders()
        self.already_fit = False

    def prepare_encoders(self):
        with open('unique_values.json', 'r') as f:
            unique_values = json.load(f)
        
        for key, values in unique_values.items():
            unique_values[key] = ["Unknown" if isinstance(v, float) and np.isnan(v) else v for v in values]
        
        for column, encoder in self.onehot_encoders.items():
            unique_value_array = np.array(unique_values[column]).reshape(-1, 1)
            encoder.fit(unique_value_array)

    def extract_features(self, record):
        features = []

        for column in self.numeric_columns:
            value = record.get(column, 0)
            try:
                features.append(float(value) if value else 0.0)
            except ValueError:
                features.append(0.0)
        
        for column in self.categorical_columns:
            value = record.get(column, 'Unknown')
            encoded = self.onehot_encoders[column].transform([[value]]).toarray().flatten()
            features.extend(encoded.tolist())
        
        for column in self.date_columns:
            date_str = record.get(column, '01/01/1970')
            try:
                if '/' not in date_str:
                    date_obj = datetime.strptime(date_str, '%Y%m%d')
                else:
                    date_obj = datetime.strptime(date_str, '%m/%d/%Y')
            except ValueError:
                date_obj = datetime.strptime('01/01/1970', '%m/%d/%Y')
            features.extend([date_obj.year, date_obj.month, date_obj.day])
        
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

    def update_models(self):
        buffer_features, buffer_labels = zip(*self.buffer)
        buffer_features = np.array(buffer_features)
        buffer_labels = np.array(buffer_labels)

        # Fit scaler and IPCA incrementally
        self.scaler.partial_fit(buffer_features)
        scaled_features = self.scaler.transform(buffer_features)
        self.ipca.partial_fit(scaled_features)

        # Transform features using updated IPCA
        transformed_features = self.ipca.transform(scaled_features)

        # Update kNN model
        self.knn.fit(transformed_features, buffer_labels)

        self.buffer = []

    def infer_vehicle_year(self, features):
        scaled_features = self.scaler.transform([features])
        transformed_features = self.ipca.transform(scaled_features)
        return self.knn.predict(transformed_features)[0] + self.mean_shift

    def evaluate_model(self):
        known_years = []
        inferred_years = []
        for features, actual_year in self.buffer:
            inferred_year = self.infer_vehicle_year(features)
            known_years.append(actual_year + self.mean_shift)
            inferred_years.append(inferred_year)
        rmse = mean_squared_error(known_years, inferred_years, squared=False)
        print(f"RMSE: {rmse}")
        abs_avg_error = np.mean(np.abs(np.array(known_years) - np.array(inferred_years)))
        print(f"Mean Absolute Error: {abs_avg_error}")
        self.buffer = []

    def run(self):
        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    raise Exception(msg.error())
                record = json.loads(msg.value().decode('utf-8'))
                try:
                    vehicle_year = int(record['Vehicle Year'])
                except ValueError:
                    vehicle_year = 0
                    print(f"Invalid vehicle year {record['Vehicle Year']} for ticket {record['Summons Number']}")
                self.total_samples += 1

                if vehicle_year == 0:
                    if self.already_fit:
                        features = self.extract_features(record)
                        inferred_year = self.infer_vehicle_year(features)
                        record['Vehicle Year'] = int(inferred_year)
                        print(f"Inferred vehicle year {record['Vehicle Year']} for ticket {record['Summons Number']}")
                else:
                    features = self.extract_features(record)
                    self.buffer.append((features, vehicle_year - self.mean_shift))
                    
                    if len(self.buffer) >= 1000:
                        self.update_models()
                        self.already_fit = True
                    
                    if len(self.buffer) >= 100 and self.total_samples % 3000 < 100:
                        self.evaluate_model()

        except KeyboardInterrupt:
            print("Consumer interrupted.")
        finally:
            self.consumer.close()
            print("Finished receiving all data")

if __name__ == "__main__":
    consumer = VehicleYearInferenceWithIPCAKNN(
        topic='NYTickets',
        bootstrap_servers='localhost:9091,localhost:9092,localhost:9093',
        group_id='vehicle_year_inference'
    )
    consumer.run()
