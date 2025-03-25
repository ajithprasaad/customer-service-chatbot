"""
Feedback Module for the Customer Service Chatbot
Handles user feedback on responses
"""
import os
import json
import pandas as pd
from datetime import datetime


class FeedbackManager:
    def __init__(self, feedback_file="data/feedback.json"):
        """
        Initialize the feedback manager

        Args:
            feedback_file (str): Path to store feedback data
        """
        self.feedback_file = feedback_file
        self.feedback_data = self._load_feedback()

        # Ensure the directory exists
        os.makedirs(os.path.dirname(feedback_file), exist_ok=True)

    def _load_feedback(self):
        """Load existing feedback data"""
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading feedback file: {e}")
                return {"feedback": []}
        else:
            return {"feedback": []}

    def save_feedback(self, query, response, feedback_type, confidence, ticket_ids=None, similarity=None,
                      comments=None):
        """
        Save user feedback on a response

        Args:
            query (str): The user's query
            response (str): The bot's response
            feedback_type (str): 'positive', 'negative', or 'neutral'
            confidence (str): Confidence level used for the response
            ticket_ids (list, optional): Relevant ticket IDs used
            similarity (float, optional): Similarity score
            comments (str, optional): Additional user comments

        Returns:
            bool: Success status
        """
        # Create feedback entry
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response_summary": response[:100] + "..." if len(response) > 100 else response,
            "feedback_type": feedback_type,
            "confidence_level": confidence,
            "ticket_ids": ticket_ids if ticket_ids else [],
            "similarity_score": similarity,
            "comments": comments,
        }

        # Add to existing feedback
        self.feedback_data["feedback"].append(feedback_entry)

        # Save to file
        try:
            with open(self.feedback_file, 'w') as f:
                json.dump(self.feedback_data, f, indent=2)
            print(f"Feedback saved: {feedback_type} for query '{query[:30] + '...' if len(query) > 30 else query}'")
            return True
        except Exception as e:
            print(f"Error saving feedback: {e}")
            return False

    def get_feedback_summary(self):
        """
        Get a summary of collected feedback

        Returns:
            dict: Feedback statistics
        """
        feedback = self.feedback_data["feedback"]

        if not feedback:
            return {"total": 0, "positive": 0, "negative": 0, "neutral": 0}

        positive = sum(1 for item in feedback if item["feedback_type"] == "positive")
        negative = sum(1 for item in feedback if item["feedback_type"] == "negative")
        neutral = sum(1 for item in feedback if item["feedback_type"] == "neutral")

        return {
            "total": len(feedback),
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "positive_percent": round(positive / len(feedback) * 100, 1) if feedback else 0,
            "recent_feedback": feedback[-5:] if len(feedback) >= 5 else feedback
        }

    def export_feedback_csv(self, output_file="data/feedback_export.csv"):
        """
        Export feedback data to CSV

        Args:
            output_file (str): Path for the output CSV file

        Returns:
            str: Path to the exported file
        """
        df = pd.DataFrame(self.feedback_data["feedback"])
        df.to_csv(output_file, index=False)
        return output_file