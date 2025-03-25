"""
Vector Database Module for the Customer Service Chatbot
Handles storing and retrieving ticket embeddings
"""
import os
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


class VectorStore:
    def __init__(self, persist_directory=None):
        """
        Initialize the vector store

        Args:
            persist_directory (str, optional): Directory to persist the database.
                If None, uses in-memory database.
        """
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-ada-002"
        )

        # Initialize Chroma client
        if persist_directory:
            self.client = chromadb.PersistentClient(path=persist_directory)
            print(f"Initialized persistent vector database at {persist_directory}")
        else:
            self.client = chromadb.Client()
            print("Initialized in-memory vector database")

        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="customer_service_tickets",
            embedding_function=self.embedding_function
        )

    def add_tickets(self, tickets_df):
        """
        Add tickets to the vector database

        Args:
            tickets_df (DataFrame): DataFrame containing processed ticket data

        Returns:
            int: Number of tickets added
        """
        # Prepare documents, metadata and IDs
        documents = []
        metadatas = []
        ids = []

        # Maximum token limit for the embedding model (with safety margin)
        MAX_TOKENS = 7000  # Setting below 8192 for safety

        for idx, ticket in tickets_df.iterrows():
            try:
                # Create a combined document with all relevant fields
                document = f"""
                Issue Key: {ticket.get('Issue key', 'N/A')}
                Summary: {ticket.get('Summary', 'N/A')}
                Description: {ticket.get('Description', 'N/A')}
                Status: {ticket.get('Status', 'N/A')}
                """

                # Add resolution/comments if it's not too large
                resolution = str(ticket.get('Merged Comments', ''))
                if len(resolution) > 5000:
                    # Truncate long resolutions
                    resolution = resolution[:5000] + "... [truncated due to length]"

                document += f"Resolution: {resolution}"

                # Truncate the entire document if it's still too large
                # Approximate token count (rough estimate: 4 chars ≈ 1 token)
                estimated_tokens = len(document) / 4
                if estimated_tokens > MAX_TOKENS:
                    truncation_point = int(MAX_TOKENS * 4)
                    document = document[:truncation_point] + "... [truncated due to length]"

                # Create metadata for filtering
                metadata = {
                    "issue_key": str(ticket.get('Issue key', '')),
                    "status": str(ticket.get('Status', '')),
                    "priority": str(ticket.get('Priority', '')),
                }

                # Use issue key as ID, or generate a unique one
                id_value = str(ticket.get('Issue key', f"ticket_{idx}"))

                documents.append(document)
                metadatas.append(metadata)
                ids.append(id_value)

            except Exception as e:
                print(f"Error processing ticket {idx}: {e}")

        # Add to collection in batches (to avoid potential size limitations)
        batch_size = 50  # Reduced from 100 to 50 for safety
        for i in range(0, len(documents), batch_size):
            end_idx = min(i + batch_size, len(documents))
            try:
                self.collection.add(
                    documents=documents[i:end_idx],
                    metadatas=metadatas[i:end_idx],
                    ids=ids[i:end_idx]
                )
                print(f"Added batch {i // batch_size + 1} ({end_idx - i} tickets)")
            except Exception as e:
                print(f"Error adding batch {i // batch_size + 1}: {e}")
                # If a batch fails, try adding documents one by one
                for j in range(i, end_idx):
                    try:
                        self.collection.add(
                            documents=[documents[j]],
                            metadatas=[metadatas[j]],
                            ids=[ids[j]]
                        )
                        print(f"Added individual ticket {ids[j]}")
                    except Exception as inner_e:
                        print(f"Error adding individual ticket {ids[j]}: {inner_e}")

        print(f"Successfully added {len(documents)} tickets to the vector database")
        return len(documents)

    def query_tickets(self, query_text, n_results=3):
        """
        Query the vector store for similar tickets

        Args:
            query_text (str): The query text
            n_results (int): Number of results to return

        Returns:
            dict: Query results containing documents, ids, and distances
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )

        return {
            "documents": results["documents"][0],
            "ids": results["ids"][0],
            "distances": results["distances"][0],
        }

    def get_collection_stats(self):
        """
        Get statistics about the collection

        Returns:
            dict: Collection statistics
        """
        count = self.collection.count()
        return {
            "count": count,
            "name": self.collection.name
        }