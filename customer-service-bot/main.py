"""
Main script for the customer service chatbot
This is the entry point that controls the overall flow of the application
"""
import os
import streamlit as st
from src.interface import ChatInterface

def main():
    """Main function that controls the application flow"""
    # Create the chat interface
    interface = ChatInterface()

    # Run the Streamlit app
    interface.run_app()

if __name__ == "__main__":
    main()