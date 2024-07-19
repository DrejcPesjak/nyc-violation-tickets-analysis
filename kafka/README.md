# Kafka Streaming for NYC Violation Tickets

This directory contains the Kafka streaming setup and implementation for real-time processing and analysis of NYC parking violation tickets. The Kafka architecture is designed to handle high volumes of data efficiently, providing real-time statistics and predictive analytics.

## Kafka Setup

We configured a Kafka cluster with the following components:
- **Three Confluent Kafka Brokers**: Each broker has a replication factor of 3 and a retention rate of 5 minutes or 5GB, ensuring high availability and fault tolerance.
- **Confluent Zookeeper**: Manages coordination and synchronization across the Kafka cluster.
- **Kafka UI from ProvectusLabs**: Provides a user-friendly interface for monitoring the Kafka cluster.

### Architecture Overview

![Kafka Brokers](Screenshot%20from%202024-07-01%2000-42-23.png)
*Figure 1: Kafka Brokers Configuration*

![Kafka Topics](Screenshot%20from%202024-07-01%2000-42-16.png)
*Figure 2: Kafka Topics Overview*

## Producer and Consumer Configuration

### Producer
The producer [producer.py](producer.py) streams all NYC parking violation tickets (excluding augmented datasets) to a single topic, `NYTickets`.

### Consumers
We implemented multiple consumers to compute real-time running statistics and perform vehicle year prediction:
1. **Running Statistics Consumer**: Computes statistics for the entire dataset [consumer_all.py](consumer_all.py), specific counties/boroughs [consumer_borough.py](consumer_borough.py), and the top 10 streets with the most violations [consumer_street.py](consumer_street.py).
2. **Vehicle Year Prediction Consumers**: Implements three methods for predicting vehicle years using nearest neighbor techniques.

## Running Statistics

The running statistics consumers compute real-time metrics, focusing on:
- **Mean**: Average value of vehicle years or other relevant metrics.
- **Standard Deviation (Std)**: Variation or dispersion of the dataset.
- **Minimum (Min)**: Minimum value observed.
- **Maximum (Max)**: Maximum value observed.
- **Anomalies/Invalid Data**: Detection of data anomalies, such as vehicle years outside the valid range.

## Vehicle Year Prediction/Imputation

We employed an online learning approach utilizing nearest neighbor techniques for vehicle year prediction and imputation. This method leverages streaming nearest neighbor theory, including locality sensitive hashing, learning-to-hash techniques, and synopses for subsampling.

### Streaming Nearest Neighbor Theory
The streaming nearest neighbor approach is based on several key techniques [Jiang et al., 2018](https://www.sciencedirect.com/science/article/pii/S0743731518300182):
- **Locality Sensitive Hashing (LSH)**: Uses random hash functions to group similar items, enabling efficient nearest neighbor searches. 
- **Learning-to-Hash**: Applies machine learning methods, such as Principal Component Analysis (PCA), to learn hash functions that preserve the proximity of data points. [Wang et al., 2017](https://arxiv.org/abs/1606.00185)
- **Synopses**: Utilizes subsampling methods to maintain a compact representation of the data, allowing efficient updates and queries.

### Implemented Methods

#### Feature Extraction
For each method, the following preprocessing steps are applied:
- **OneHotEncoding** for categorical features.
- **Conversion of numeric features** to float.
- **Parsing date features** into year, month, and day.
- **Standard Scaling** for numerical feature normalization where applicable.

#### Method 1: Centroid-based k-Nearest Neighbors (Centroid-kNN) - [consumer_knn.py](consumer_knn.py)
This method maintains a running average vector (centroid) for each vehicle year category. For each new sample, its features are compared to the centroids of all categories, and the nearest centroid (k=1) determines the predicted vehicle year. This method reduces the complexity of searching by using precomputed centroids as representatives of the categories. The centroids are periodically updated to reflect new incoming data.

#### Method 2: Incremental PCA with k-Nearest Neighbors (IPCA-kNN) - [consumer_ipca_knn.py](consumer_ipca_knn.py)
This approach applies incremental PCA to perform dimensionality reduction on the data, reducing it to 20 principal components. For each new sample, its features are first transformed using the PCA model and then k-Nearest Neighbors (k=5) is applied to predict the vehicle year. Incremental PCA processes data in small batches and updates the PCA transformation incrementally, allowing the model to handle streaming data. The scaler and PCA are updated every 1000 samples to ensure they adapt to new data distributions.

#### Method 3: Stochastic Gradient Descent Regressor (SGDRegressor) - [consumer_sgd.py](consumer_sgd.py)
The SGDRegressor model performs online learning by training on one sample at a time after an initial warmup phase with 1000 samples. This method uses a linear model with stochastic gradient descent optimization. It predicts the vehicle year by using a mean shift (predicting the offset from the year 2000) and a standard scaler, which is incrementally updated with each new sample to normalize the feature set. This method continuously learns and adapts to new data, providing robust performance over time.

### Evaluation
Evaluation of the models is performed every 3000 samples using a set of 100 samples. The performance metrics used are Root Mean Squared Error (RMSE) and Mean Absolute Error (MAE).

### Performance Metrics

| Method        | RMSE | MAE |
|---------------|------|-----|
| Centroid-kNN  | 8.7  | 6.7 |
| IPCA-kNN      | 5.8  | 4.7 |
| SGDRegressor  | 5.1  | 4.0 |
| **Baseline (mean=2013)** | **6.2**  | **4.6** |

*Table 1: Performance Metrics for Vehicle Year Prediction Methods*

By implementing these online learning methods, we aim to accurately predict or impute vehicle years in real-time, leveraging the continuous stream of parking violation data.

## References

- Xiaohui Jiang, Peng Hu, Yanchao Li, Chi Yuan, Isma Masood, Hamed Jelodar, Mahdi Rabbani, Yongli Wang. "A survey of real-time approximate nearest neighbor query over streaming data for fog computing." Journal of Parallel and Distributed Computing, 2018. [Link](https://www.sciencedirect.com/science/article/pii/S0743731518300182)
- Jingdong Wang, Ting Zhang, Jingkuan Song, Nicu Sebe, Heng Tao Shen. "A Survey on Learning to Hash." arXiv preprint, 2017. [Link](https://arxiv.org/abs/1606.00185)

