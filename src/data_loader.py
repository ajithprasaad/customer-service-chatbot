"""
Data Loader Module - Handles loading data files for the customer service chatbot
"""
import os
import pandas as pd

def validate_file_exists(file_path):
    """
    Check if the file exists and is readable.

    Args:
        file_path (str): Path to the file

    Returns:
        bool: True if file exists and is readable, False otherwise
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return False

    if not os.path.isfile(file_path):
        print(f"Error: {file_path} is not a file")
        return False

    if not os.access(file_path, os.R_OK):
        print(f"Error: No permission to read {file_path}")
        return False

    return True

def get_file_info(file_path):
    """
    Get basic information about the file.

    Args:
        file_path (str): Path to the file

    Returns:
        dict: Dictionary containing file information
    """
    if not validate_file_exists(file_path):
        return None

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path) / 1024  # Size in KB
    file_extension = os.path.splitext(file_path)[1].lower()

    return {
        "file_name": file_name,
        "file_path": file_path,
        "file_size_kb": round(file_size, 2),
        "file_extension": file_extension
    }

def load_data_file(file_path):
    """
    Load data from a file based on its extension.

    Args:
        file_path (str): Path to the file

    Returns:
        object: Loaded data or None if file could not be loaded
    """
    if not validate_file_exists(file_path):
        return None

    file_extension = os.path.splitext(file_path)[1].lower()

    try:
        # Excel file
        if file_extension in ['.xlsx', '.xls']:
            print(f"Loading Excel file: {file_path}")
            return pd.read_excel(file_path)

        # CSV file
        elif file_extension == '.csv':
            print(f"Loading CSV file: {file_path}")
            return pd.read_csv(file_path)

        # Text file
        elif file_extension == '.txt':
            print(f"Loading text file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()

        # PDF file - just note it's detected, we'll implement PDF parsing later
        elif file_extension == '.pdf':
            print(f"Detected PDF file: {file_path} (PDF parsing will be implemented later)")
            return None

        # Unsupported file type
        else:
            print(f"Unsupported file type: {file_extension}")
            return None

    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return None