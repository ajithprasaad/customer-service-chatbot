"""
Main script for the customer service chatbot
This is the entry point that controls the overall flow of the application
"""
import os
import sys
from src.data_loader import load_data_file, get_file_info
from src.jira_processor import process_jira_data

def create_directory_structure():
    """Create the necessary directory structure if it doesn't exist"""
    directories = [
        'data/raw',
        'data/processed',
        'src'
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Ensured directory exists: {directory}")

def main():
    """Main function that controls the application flow"""
    print("===== Customer Service Chatbot - JIRA Data Processor =====")

    # Ensure directory structure exists
    create_directory_structure()

    # Get the path to the data file
    print("\nPlease enter the path to your JIRA data file (Excel or CSV):")
    # file_path = input().strip()
    file_path = "data/processed/processed_jira_data.xlsx"


    # Get file information
    file_info = get_file_info(file_path)
    if not file_info:
        print("Failed to get file information. Exiting.")
        return

    print("\nFile Information:")
    for key, value in file_info.items():
        print(f"  {key}: {value}")

    # Check if file is Excel or CSV
    if file_info['file_extension'] not in ['.xlsx', '.xls', '.csv']:
        print("This processor only supports Excel and CSV files. Please provide an Excel or CSV file.")
        return

    try:
        # Process the JIRA data
        processed_data = process_jira_data(file_path, 'data/processed')

        # Display a preview of the processed data
        print("\nPreview of processed data:")
        print(f"Shape: {processed_data.shape} (rows × columns)")
        print("Columns: " + ", ".join(processed_data.columns))

        # Display first 5 rows with limited columns for preview
        preview_cols = min(5, len(processed_data.columns))
        preview_data = processed_data.iloc[:5, :preview_cols]

        # Print the preview with proper formatting
        with pd.option_context('display.max_colwidth', 40):
            print(preview_data)

        print(f"\nFull processed data saved to: data/processed/processed_jira_data.csv and .xlsx")

        print("\n===== Processing Complete =====")

    except Exception as e:
        print(f"Error processing data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import pandas as pd
    main()