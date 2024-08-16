# NYC Violation Tickets Analysis

![](https://github.com/DrejcPesjak/nyc-violation-tickets-analysis/blob/main/gif/violations_2.gif)


## Overview
This repository contains the code and documentation for a big data project focused on analyzing and predicting NYC violation tickets. The project utilizes a variety of data sources, including weather data, school locations, businesses, landmarks, events, and holidays, to provide a comprehensive analysis.

## Project Structure
```
nyc-violation-tickets-analysis/
├── data
├── data-convert
├── data-enhance
├── eda-analysis
├── kafka
├── machine-learning
└── README.md
```

### Folders
- **data**: Contains a bash script to download NYCTickets data for each year from 2013 to april of 2024.
- **data-convert**: Scripts and utilities for converting raw data to Parquet and HDF5 formats.
- **data-enhance**: Processes and enhances the data by integrating additional datasets like weather, school locations, etc.
- **eda-analysis**: Notebooks and scripts for exploratory data analysis (EDA).
- **kafka**: Kafka streaming scripts for real-time data processing.
- **machine-learning**: Machine learning models and scripts for predictions.

## Data Sources
- NYC violation tickets (mostly parking violations)
- Weather data (hourly for full NYC from the Square Park weather station) - VisualCrossing
- NYC OpenData
	- School locations
	- Businesses data
	- Landmarks data
	- Event data (special events and construction)
- Holidays (national, NYC-specific, general, religious, school)

## Exploratory Data Analysis
The EDA includes:
- Vehicle year distribution analysis
- Monthly violations trends (including COVID-19 impact)
- Geographical map of violations per county

## Kafka Streaming
Real-time statistics on violation data:
- Full dataset statistics
- County/borough specific statistics
- Top 10 streets statistics

Statistics include mean, standard deviation, minimum, maximum, and anomaly/invalid counts.

### Vehicle Year Imputation
- Nearest Neighbor Theory
  - Locality Sensitive Hashing
  - Learning-to-Hash (ML methods like PCA)
  - Synopses (subsampling)
- Models:
  - Centroid + KNN(1)
  - PCA(20) + KNN(5)
  - SGDRegressor

## Machine Learning Models
### Violation Count Prediction
- Daily/hourly (county-based) violation count prediction using:
  - Dask-ML
  - XGBoost
  - Sklearn partial-fit

