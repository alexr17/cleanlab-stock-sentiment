import pandas as pd

def round_column_values(file_path, column_name):
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Check if the column exists in the dataframe
    if column_name in df.columns:
        # Round the values in the specified column to the nearest single decimal
        df[column_name] = df[column_name].round(1)
        
        # Save the modified dataframe back to a CSV file
        df.to_csv(file_path, index=False)
        print(f"Values in column '{column_name}' have been rounded to the nearest single decimal.")
    else:
        print(f"Column '{column_name}' does not exist in the CSV file.")

# Example usage
# file_path = 'path/to/your/file.csv'
# column_name = 'col'
# round_column_values(file_path, column_name)

