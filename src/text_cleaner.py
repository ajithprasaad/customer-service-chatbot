"""
Text Cleaning Module - Functions for cleaning and processing text from Jira tickets
"""
import re
import pandas as pd
import urllib.parse


def clean_text(text):
    """
    Basic text cleaning function for simple text fields

    Args:
        text: Text to clean

    Returns:
        str: Cleaned text
    """
    if pd.isna(text) or text is None:
        return ""

    # Convert to string if not already
    text = str(text)

    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    # Remove Jira formatting
    text = re.sub(r'\{quote\}|\{code\}', '', text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def clean_complex_text(text):
    """
    Advanced text cleaning for complex Jira tickets with HTML/JSON/color formatting

    Args:
        text (str): Raw text with complex formatting

    Returns:
        str: Cleaned text with important content preserved
    """
    if pd.isna(text) or text is None:
        return ""

    # Convert to string if not already
    text = str(text)

    # Step 1: Extract order numbers, case numbers, and other key identifiers
    order_numbers = re.findall(r'SO?[-\d]+', text)
    case_numbers = re.findall(r'CASE \d+', text)

    # Step 2: Handle color tags and formatting
    # Replace color tags with empty string
    text = re.sub(r'\{color:[^}]+\}', '', text)
    text = re.sub(r'\{color\}', '', text)

    # Step 3: Handle JSON-like formatting in a careful way
    # Extract content from expand/paragraph/text structures
    content_matches = re.findall(r'"text":"([^"]+)"', text)
    extracted_content = ' '.join(content_matches)

    # Step 4: Handle links but preserve URLs that might be important
    # Replace link protect wrappers with actual URLs
    link_pattern = r'https://linkprotect\.cudasvc\.com/url\?a=([^&]+)&[^"]*'

    def decode_url(match):
        encoded_url = match.group(1)
        try:
            # URL decode the actual URL
            return urllib.parse.unquote(encoded_url)
        except:
            return match.group(0)

    text = re.sub(link_pattern, decode_url, text)

    # Step 5: Handle email formatting
    # Extract email headers in a readable format
    email_headers = []
    if '*From:*' in text:
        from_match = re.search(r'\*From:\*\s*([^\s*]+)', text)
        if from_match:
            email_headers.append(f"From: {from_match.group(1)}")

    if '*Sent:*' in text:
        sent_match = re.search(r'\*Sent:\*\s*([^*]+)', text)
        if sent_match:
            email_headers.append(f"Sent: {sent_match.group(1).strip()}")

    if '*Subject:*' in text:
        subject_match = re.search(r'\*Subject:\*\s*([^|{]+)', text)
        if subject_match:
            email_headers.append(f"Subject: {subject_match.group(1).strip()}")

    # Step 6: Clean up special characters and normalize whitespace
    # Remove unicode markers and normalize whitespace
    text = re.sub(r'â€™|â€œ|â€|Â', "'", text)
    text = re.sub(r'\\+', ' ', text)  # Replace backslashes with spaces
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace

    # Step 7: Handle specific item requests and changes
    item_requests = []
    if "remove" in text.lower() and "case" in text.lower():
        item_match = re.search(r'remove the:?\s*([^.]+)', text, re.IGNORECASE)
        if item_match:
            item_requests.append(f"Request to remove: {item_match.group(1).strip()}")

    if "change" in text.lower() and "time" in text.lower():
        time_match = re.search(r'change our time to a ([^,?]+)', text, re.IGNORECASE)
        if time_match:
            item_requests.append(f"Request to change time to: {time_match.group(1).strip()}")

    # Combine all extracted information
    result_parts = []

    # Add email headers if found
    if email_headers:
        result_parts.append("EMAIL HEADERS:")
        result_parts.extend(email_headers)
        result_parts.append("")

    # Add order/case information if found
    if order_numbers or case_numbers:
        result_parts.append("REFERENCE NUMBERS:")
        if order_numbers:
            result_parts.append(f"Order Numbers: {', '.join(order_numbers)}")
        if case_numbers:
            result_parts.append(f"Case Numbers: {', '.join(case_numbers)}")
        result_parts.append("")

    # Add specific requests if found
    if item_requests:
        result_parts.append("CUSTOMER REQUESTS:")
        result_parts.extend(item_requests)
        result_parts.append("")

    # Add the main content with no special formatting
    cleaned_base_text = re.sub(r'\{[^}]+\}|\[|]|\*|\\|\/\/', ' ', text)
    cleaned_base_text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                               '[URL]', cleaned_base_text)
    cleaned_base_text = re.sub(r'\s+', ' ', cleaned_base_text).strip()

    # If we extracted content from JSON-like structures and it's substantial, use it
    if len(extracted_content) > 100:
        result_parts.append("MAIN CONTENT:")
        result_parts.append(extracted_content)
    else:
        result_parts.append("MAIN CONTENT:")
        result_parts.append(cleaned_base_text)

    # Join all parts with newlines
    return '\n'.join(result_parts)


def clean_comment(text):
    """
    Special cleaning function for comments to preserve more original content

    Args:
        text: Comment text to clean

    Returns:
        str: Cleaned comment text
    """
    if pd.isna(text) or text is None:
        return ""

    # Convert to string if not already
    text = str(text)

    # Handle date and user ID format: "07/10/2023 01:07;5fb17b020dd553006f17ff0a;Hi Darb,"
    comment_parts = text.split(';', 2)

    if len(comment_parts) >= 3:
        date_str, user_id, content = comment_parts

        # Clean the content part but preserve original meaning
        cleaned_content = re.sub(r'\{color:[^}]+\}|\{color\}', '', content)
        cleaned_content = re.sub(r'â€™|â€œ|â€|Â', "'", cleaned_content)

        # Format as a clean comment
        return f"[{date_str}] {cleaned_content}"
    else:
        # If not in expected format, just clean up the text
        cleaned_text = re.sub(r'\{color:[^}]+\}|\{color\}', '', text)
        cleaned_text = re.sub(r'â€™|â€œ|â€|Â', "'", cleaned_text)
        return cleaned_text