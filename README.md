**Component Descriptions**
User: Interacts with the system by asking questions about customer service issues
Chat Interface: Streamlit UI that handles user interaction
Retrieval Engine: Finds relevant past tickets from the vector database
Triage Engine: Determines confidence level and escalation needs
Response Generator: Creates AI-generated responses using retrieved context
Human Agent Interface: Used when escalation is needed
OpenAI API: External service that powers the AI responses
Feedback Manager: Collects and processes user feedback
Vector Database: Stores embeddings of ticket data for semantic search
CSV Data: Source of JIRA ticket exports

**Key Flows**
Data Loading: JIRA tickets are loaded and embedded
Query Processing: User question → retrieval → triage
Response Generation: AI response created and displayed
Human Escalation: When AI confidence is low
Feedback Loop: User feedback improves system

![WhatsApp Image 2025-03-24 at 22 38 54_34db4748](https://github.com/user-attachments/assets/e99e1fba-1d16-4b17-8902-2c10f66b1fc3)
