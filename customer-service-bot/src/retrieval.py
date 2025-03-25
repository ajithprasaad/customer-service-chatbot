"""
Retrieval Module for the Customer Service Chatbot
Handles retrieving relevant tickets based on user queries
"""
from .vector_store import VectorStore

class RetrievalEngine:
    def __init__(self, vector_store=None):
        """
        Initialize the retrieval engine

        Args:
            vector_store (VectorStore, optional): Vector store instance.
                If None, creates a new in-memory instance.
        """
        self.vector_store = vector_store if vector_store else VectorStore()

    def retrieve_relevant_tickets(self, query, n_results=3):
        """
        Retrieve the most relevant tickets for a given query

        Args:
            query (str): User query
            n_results (int): Number of results to retrieve

        Returns:
            dict: Retrieval results with documents, similarity scores, and IDs
        """
        results = self.vector_store.query_tickets(query, n_results=n_results)

        # Format the results for easier consumption
        formatted_results = []

        for i in range(len(results["documents"])):
            formatted_results.append({
                "content": results["documents"][i],
                "similarity": 1.0 - results["distances"][i],  # Convert distance to similarity
                "id": results["ids"][i]
            })

        return {
            "results": formatted_results,
            "top_similarity": 1.0 - results["distances"][0] if results["distances"] else 0
        }

    def format_context_for_prompt(self, query, n_results=3):
        """
        Format retrieved context for use in prompt

        Args:
            query (str): User query
            n_results (int): Number of results to retrieve

        Returns:
            dict: Formatted context and similarity score
        """
        retrieval_results = self.retrieve_relevant_tickets(query, n_results)

        # Format the context from the results
        context_parts = []

        for i, result in enumerate(retrieval_results["results"]):
            context_parts.append(
                f"RELEVANT TICKET #{i+1} (Similarity: {result['similarity']:.2f}):\n"
                f"{result['content']}\n"
            )

        # Combine into a single context string
        context = "\n".join(context_parts)

        return {
            "formatted_context": context,
            "top_similarity": retrieval_results["top_similarity"],
            "ticket_ids": [r["id"] for r in retrieval_results["results"]]
        }