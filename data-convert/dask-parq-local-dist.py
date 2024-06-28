from dask.distributed import Client, LocalCluster
import dask.dataframe as dd
import pyarrow as pa
import pyarrow.parquet as pq
import gc

def main():
    cluster = LocalCluster(n_workers=4, threads_per_worker=1, memory_limit="2GB")
    client = Client(cluster)

    base_path = "../data"
    glob_pattern = f"{base_path}/*.csv"  # Find all CSV files
    # cols = ['Summons Number', 'Plate ID', 'Registration State', 'Plate Type',
    #     'Issue Date', 'Violation Code', 'Vehicle Body Type', 'Vehicle Make',
    #     'Issuing Agency', 'Street Code1', 'Street Code2', 'Street Code3',
    #     'Vehicle Expiration Date', 'Violation Location', 'Violation Precinct',
    #     'Issuer Precinct', 'Issuer Code', 'Issuer Command', 'Issuer Squad',
    #     'Violation Time', 'Time First Observed', 'Violation County',
    #     'Violation In Front Of Or Opposite', 'Number', 'Street',
    #     'Intersecting Street', 'Date First Observed', 'Law Section',
    #     'Sub Division', 'Violation Legal Code', 'Days Parking In Effect    ',
    #     'From Hours In Effect', 'To Hours In Effect', 'Vehicle Color',
    #     'Unregistered Vehicle?', 'Vehicle Year', 'Meter Number',
    #     'Feet From Curb', 'Violation Post Code', 'Violation Description',
    #     'No Standing or Stopping Violation', 'Hydrant Violation',
    #     'Double Parking Violation']
    # dtype = {col: "object" for col in cols}

    # dtype={'Issuer Squad': 'object',
    #    'Unregistered Vehicle?': 'float64',
    #    'Violation Description': 'object',
    #    'Violation Legal Code': 'object',
    #    'Violation Post Code': 'object'}

    ddf = dd.read_csv(glob_pattern, assume_missing=True, dtype="object", blocksize="64MB")

    ddf.to_parquet(
        "parquet_data/", engine="pyarrow", overwrite=True, compression="snappy"
    )

    client.close()
    gc.collect()

if __name__ == '__main__':
    main()

