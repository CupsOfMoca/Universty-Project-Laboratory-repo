import os
import pandas as pd

# Get the current working directory
current_dir = os.getcwd()

# Directory containing the CSV files
data_dir = os.path.join(current_dir, "training_data_final")

# List to store documents
documents = []

# Traverse through the directory and its subfolders
for root, dirs, files in os.walk(data_dir):
    for file in files:
        # Read the contents of each CSV file
        file_path = os.path.join(root, file)
        df = pd.read_csv(file_path)
        
        # Iterate over each row in the CSV file
        for index, row in df.iterrows():
            # Replace None objects with "None" string
            row_dict = row.to_dict()
            for key, value in row_dict.items():
                if value is None or value == "":
                    row_dict[key] = "None"
            
            # Add document to the list
            documents.append(row_dict)
            
        print("File processed:", file_path)

# Convert documents to DataFrame
df = pd.DataFrame(documents)

# Write DataFrame to CSV
csv_path = "combined_data.csv"
df.to_csv(csv_path, index=False)
