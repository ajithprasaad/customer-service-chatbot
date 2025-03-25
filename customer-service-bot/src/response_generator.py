"""
Response Generator Module for the Customer Service Chatbot
Generates responses based on retrieved context and triage results
"""
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class ResponseGenerator:
    def __init__(self, model="gpt-3.5-turbo"):
        """
        Initialize the response generator

        Args:
            model (str): OpenAI model to use
        """
        self.model = model

    def generate_response(self, query, context, triage_result):
        """
        Generate a response based on the query, context, and triage result

        Args:
            query (str): User query
            context (str): Retrieved context
            triage_result (dict): Triage result

        Returns:
            dict: Generated response with metadata
        """
        confidence = triage_result["confidence"]
        escalate = triage_result["escalate"]

        # Create prompt based on confidence level
        if escalate:
            system_prompt = f"""You are a helpful customer service assistant for Capital Area Food bank organization. 
            The customer has asked: "{query}"
            
            Based on our analysis, this query should be handled by a human agent because: {triage_result['reason']}
            
            However, you can still provide a helpful initial response. Use the following similar past tickets as reference:
            
            {context}
            
            Respond in a helpful manner, but clearly indicate that you'll connect them with a human agent for further assistance.
            """
        elif confidence == "high":
            system_prompt = f"""You are a helpful customer service assistant for a food bank organization.
            The customer has asked: "{query}"
            
            Based on our records, we have high confidence in addressing this query. Use the following similar past tickets as reference:
            
            {context}
            
            Provide a clear, direct answer based on these similar cases. Be concise but thorough.
            """
        else:  # Medium confidence
            system_prompt = f"""You are a helpful customer service assistant for a food bank organization.
            The customer has asked: "{query}"
            
            We have found some potentially relevant past tickets, but they may not fully address the question. Use them as guidance:
            
            {context}
            
            Provide a helpful response based on the information available, but indicate any areas where you're uncertain or where the customer might need additional assistance.
            """

        # Generate response using OpenAI
        response = openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.7,
            max_tokens=500
        )

        return {
            "response_text": response.choices[0].message.content,
            "confidence": confidence,
            "should_escalate": escalate,
            "reason": triage_result["reason"]
        }