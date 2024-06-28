#!/bin/bash

# Directory containing the CSV files
DATA_DIR="data"

# Create a directory to store the extracted column names
mkdir -p columns

# Extract the first line (column names) from each CSV file, split by comma, and save each column name to a new line
for file in "$DATA_DIR"/*.csv; do
    basename=$(basename "$file")
    head -n 1 "$file" | tr ',' '\n' > "columns/${basename}_columns.txt"
done

# Get a list of the extracted column name files
column_files=(columns/*.txt)

# Compare each file with every other file
for ((i = 0; i < ${#column_files[@]} - 1; i++)); do
    for ((j = i + 1; j < ${#column_files[@]}; j++)); do
        diff_output=$(diff "${column_files[i]}" "${column_files[j]}")
        if [ -n "$diff_output" ]; then
            echo "Difference between ${column_files[i]} and ${column_files[j]}:"
            echo "$diff_output"
            echo
        fi
    done
done

# Clean up the temporary files
# Uncomment the following line to remove the temporary files after comparison
# rm -r columns
