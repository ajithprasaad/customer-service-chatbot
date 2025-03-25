"""
Triage Module for the Customer Service Chatbot
Determines confidence levels and whether to escalate to humans
"""
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class TriageEngine:
    def __init__(self):
        """Initialize the triage engine"""
        self.confidence_thresholds = {
            "high": 0.65,    # Very similar to existing tickets
            "medium": 0.45,  # Somewhat similar
            "low": 0.0      # Not similar enough
        }

    def determine_confidence(self, top_similarity):
        """
        Determine confidence level based on similarity score

        Args:
            top_similarity (float): Similarity score (0-1)

        Returns:
            str: Confidence level ('high', 'medium', or 'low')
        """
        if top_similarity >= self.confidence_thresholds["high"]:
            return "high"
        elif top_similarity >= self.confidence_thresholds["medium"]:
            return "medium"
        else:
            return "low"

    def check_sentiment(self, query):
        """
        Check if query contains urgent or negative sentiment

        Args:
            query (str): User query

        Returns:
            dict: Sentiment analysis results
        """
        # Use OpenAI to analyze sentiment
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a sentiment analyzer. Analyze the following customer service query for urgency and sentiment. Respond with a JSON object containing 'urgency' (high/medium/low) and 'sentiment' (positive/neutral/negative)."},
                {"role": "user", "content": query}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )

        # Parse the response
        try:
            import json
            sentiment_data = json.loads(response.choices[0].message.content)
            return sentiment_data
        except:
            # Fallback if parsing fails
            return {"urgency": "low", "sentiment": "neutral"}

    def should_escalate(self, query, top_similarity, previous_escalations=None):
        """
        Determine if a query should be escalated to a human

        Args:
            query (str): User query
            top_similarity (float): Similarity score from retrieval
            previous_escalations (list, optional): List of previous escalation decisions

        Returns:
            dict: Escalation decision with reason
        """
        confidence = self.determine_confidence(top_similarity)

        # Check for explicit requests for human assistance
        human_keywords = ["speak to human", "talk to agent", "real person", "human agent"]
        explicit_request = any(keyword in query.lower() for keyword in human_keywords)

        # Low confidence is an automatic escalation
        if confidence == "low":
            return {
                "escalate": True,
                "reason": "Low confidence in automated response",
                "confidence": confidence
            }

        # Explicit request for human is automatic escalation
        if explicit_request:
            return {
                "escalate": True,
                "reason": "Customer explicitly requested human assistance",
                "confidence": confidence
            }

        # For medium confidence, check sentiment
        if confidence == "medium":
            sentiment = self.check_sentiment(query)
            if sentiment.get("urgency") == "high" or sentiment.get("sentiment") == "negative":
                return {
                    "escalate": True,
                    "reason": f"Customer query shows {sentiment.get('sentiment')} sentiment with {sentiment.get('urgency')} urgency",
                    "confidence": confidence
                }

        # Default case - no need to escalate
        return {
            "escalate": False,
            "reason": f"{confidence.capitalize()} confidence in automated response",
            "confidence": confidence
        }