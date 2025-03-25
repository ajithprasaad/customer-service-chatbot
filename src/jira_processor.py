"""
JIRA Ticket Processor - Focused on extracting relevant fields and merging comments
"""
import os
import pandas as pd
import re
from .text_cleaner import clean_text, clean_complex_text, clean_comment

def detect_comment_columns(df):
    """
    Detect columns that contain comment data based on content patterns

    Args:
        df (DataFrame): Raw JIRA data

    Returns:
        list: List of column names that appear to contain comments
    """
    comment_cols = []

    # Check for standard "Comment" columns first
    standard_comment_cols = [col for col in df.columns if col.startswith('Comment')]
    comment_cols.extend(standard_comment_cols)

    # If standard comment columns were found, return them
    if comment_cols:
        print(f"Found standard comment columns: {comment_cols}")
        return comment_cols

    # Otherwise, check for columns that might contain comment data based on content patterns
    for col in df.columns:
        # Skip columns that are clearly not comments
        if any(keyword in col.lower() for keyword in ['key', 'id', 'status', 'priority', 'created', 'resolved']):
            continue

        # Sample some values from the column
        sample_values = df[col].dropna().astype(str).head(5).tolist()

        # Check for patterns that look like comments
        comment_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}\s\d{1,2}:\d{2}',  # Date pattern like 07/10/2023 01:07
            r'[0-9a-f]{20,}',  # Hex IDs like 5fb17b020dd553006f17ff0a
            r'Message originally posted',  # Common phrase in comments
            r'Hi\s+\w+',  # Greeting patterns
            r';',  # Semicolons are often used in comment formatting
        ]

        # Check if any sample matches our patterns
        for sample in sample_values:
            if any(re.search(pattern, sample) for pattern in comment_patterns):
                comment_cols.append(col)
                break

    if comment_cols:
        print(f"Detected non-standard comment columns: {comment_cols}")
    else:
        print("No comment columns detected in the data.")

    return comment_cols

def merge_comments(df):
    """
    Merge all comment fields into a single field with timestamps

    Args:
        df (DataFrame): Raw JIRA data

    Returns:
        Series: Series containing merged comments for each ticket
    """
    # Check if "Merged Comments" column already exists
    if 'Merged Comments' in df.columns:
        print("'Merged Comments' column already exists, using it as is.")
        return df['Merged Comments']

    # Find all comment columns
    comment_cols = detect_comment_columns(df)

    if not comment_cols:
        # Return empty series if no comment columns are found
        print("No comment columns found for merging.")
        return pd.Series([''] * len(df))

    print(f"Merging {len(comment_cols)} comment columns")

    # Initialize an empty list for the merged comments
    merged_comments = []

    # For each row in the DataFrame
    for _, row in df.iterrows():
        ticket_comments = []

        # Process each comment column
        for col in comment_cols:
            if pd.notna(row.get(col)) and row.get(col):
                # Extract comment content
                comment_text = str(row[col])

                # Apply comment-specific cleaning
                cleaned_comment = clean_comment(comment_text)

                # Only add if the cleaned comment has content
                if cleaned_comment.strip():
                    ticket_comments.append(cleaned_comment)

        # Join all comments for the ticket with line breaks
        merged_comments.append('\n'.join(ticket_comments) if ticket_comments else "")

    return pd.Series(merged_comments)

def extract_relevant_fields(df):
    """
    Extract only the relevant fields from the DataFrame

    Args:
        df (DataFrame): Raw JIRA data

    Returns:
        DataFrame: Simplified DataFrame with only relevant fields
    """
    # List of fields to keep (adjust based on actual column names in your data)
    relevant_fields = [
        'Issue key', 'Summary', 'Description',
        'Custom field (Cause of issue)', 'Custom field (Request Category)',
        'Custom field (Request Type)', 'Custom field (Source)',
        'Status', 'Priority',
        'Created', 'Resolved',
        'Custom field (Time to first response)', 'Custom field (Time to resolution)'
    ]

    # Get available relevant fields (some might not exist in the data)
    available_fields = [col for col in relevant_fields if col in df.columns]

    # Create a new DataFrame with only the relevant fields
    simplified_df = df[available_fields].copy() if available_fields else pd.DataFrame()

    # Apply enhanced cleaning to Description field
    if 'Description' in simplified_df.columns:
        simplified_df['Description'] = simplified_df['Description'].apply(clean_complex_text)

    # Process comments
    merged_comments = merge_comments(df)
    if not simplified_df.empty:
        simplified_df['Merged Comments'] = merged_comments

    # Clean text fields (except Description which was already cleaned with our advanced function)
    for col in simplified_df.columns:
        if col != 'Description' and col != 'Merged Comments' and simplified_df[col].dtype == 'object':
            simplified_df[col] = simplified_df[col].apply(clean_text)

    return simplified_df

def process_jira_data(input_file, output_dir):
    """
    Main function to process JIRA data files

    Args:
        input_file (str): Path to the input JIRA data file
        output_dir (str): Directory where processed files will be saved

    Returns:
        DataFrame: Processed DataFrame
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Get file extension
    file_extension = os.path.splitext(input_file)[1].lower()

    # Load the data based on file type
    if file_extension in ['.xlsx', '.xls']:
        df = pd.read_excel(input_file)
    elif file_extension == '.csv':
        df = pd.read_csv(input_file)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}. Please provide Excel or CSV.")

    print(f"Loaded file with {df.shape[0]} rows and {df.shape[1]} columns.")
    print(f"Column names: {', '.join(df.columns)}")

    # Extract relevant fields and merge comments
    processed_df = extract_relevant_fields(df)

    if processed_df.empty:
        print("Warning: No relevant columns found in input data.")
        # Use the original DataFrame as a fallback
        processed_df = df.copy()
        processed_df['Merged Comments'] = merge_comments(df)

    print(f"Processed data contains {processed_df.shape[0]} rows and {processed_df.shape[1]} columns.")

    # Save the processed data
    output_file = os.path.join(output_dir, 'processed_jira_data.csv')
    processed_df.to_csv(output_file, index=False)

    # Also save an Excel version for better formatting
    excel_output_file = os.path.join(output_dir, 'processed_jira_data.xlsx')
    processed_df.to_excel(excel_output_file, index=False)

    print(f"Processed data saved to {output_file} and {excel_output_file}")

    return processed_df