from dask.distributed import Client, LocalCluster
import dask.dataframe as dd
import pyarrow as pa
import pyarrow.parquet as pq

def main():
    cluster = LocalCluster(n_workers=64, threads_per_worker=2)
    client = Client(cluster)

    base_path = "/d/hpc/projects/FRI/bigdata/data/NYTickets"
    glob_pattern = f"{base_path}/*.csv"  # Find all CSV files
    cols = ['Summons Number', 'Plate ID', 'Registration State', 'Plate Type',
        'Issue Date', 'Violation Code', 'Vehicle Body Type', 'Vehicle Make',
        'Issuing Agency', 'Street Code1', 'Street Code2', 'Street Code3',
        'Vehicle Expiration Date', 'Violation Location', 'Violation Precinct',
        'Issuer Precinct', 'Issuer Code', 'Issuer Command', 'Issuer Squad',
        'Violation Time', 'Time First Observed', 'Violation County',
        'Violation In Front Of Or Opposite', 'Number', 'Street',
        'Intersecting Street', 'Date First Observed', 'Law Section',
        'Sub Division', 'Violation Legal Code', 'Days Parking In Effect    ',
        'From Hours In Effect', 'To Hours In Effect', 'Vehicle Color',
        'Unregistered Vehicle?', 'Vehicle Year', 'Meter Number',
        'Feet From Curb', 'Violation Post Code', 'Violation Description',
        'No Standing or Stopping Violation', 'Hydrant Violation',
        'Double Parking Violation']
    dtype = {col.strip(): "object" for col in cols}

    ddf = dd.read_csv(glob_pattern, dtype=dtype)
    ddf.columns = ddf.columns.str.strip()
    print("Column names:", ddf.columns)
    for col in ddf.columns:
        if ddf[col].dtype == 'string':
            ddf[col] = ddf[col].astype('object')

    ddf.to_hdf('/d/hpc/projects/FRI/bigdata/students/dp8949/hdf5_data/data_*.h5', key='data', format='table')

    client.close()

if __name__ == '__main__':
    main()

