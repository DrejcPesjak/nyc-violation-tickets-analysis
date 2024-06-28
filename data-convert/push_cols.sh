#!/bin/bash

# Directory containing the CSV files
DATA_DIR="data"

# Extract the first line (column names) from 2023.csv
header=$(head -n 1 "$DATA_DIR/2023.csv")

# Loop through each CSV file in the data directory, except 2023.csv
for file in "$DATA_DIR"/*.csv; do
    if [[ "$file" != "$DATA_DIR/2023.csv" ]]; then
        # Extract all lines except the first line from the current CSV file
        tail -n +2 "$file" > "${file}.tmp"

        # Write the header followed by the rest of the file
        echo "$header" > "$file"
        cat "${file}.tmp" >> "$file"

        # Remove the temporary file
        rm "${file}.tmp"
    fi
done

echo "Column names from 2023.csv have been pushed to all other CSV files."
