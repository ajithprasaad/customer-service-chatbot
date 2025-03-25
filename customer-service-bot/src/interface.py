"""
User Interface Module for the Customer Service Chatbot
Provides a Streamlit interface for interacting with the chatbot
"""
import streamlit as st
import pandas as pd
from .vector_store import VectorStore
from .retrieval import RetrievalEngine
from .triage import TriageEngine
from .response_generator import ResponseGenerator
from .feedback import FeedbackManager

class ChatInterface:
    def __init__(self, retrieval_engine=None, triage_engine=None, response_generator=None):
        """
        Initialize the chat interface

        Args:
            retrieval_engine (RetrievalEngine, optional): Retrieval engine instance
            triage_engine (TriageEngine, optional): Triage engine instance
            response_generator (ResponseGenerator, optional): Response generator instance
        """
        # Initialize components if not provided
        vector_store = VectorStore()
        self.retrieval_engine = retrieval_engine or RetrievalEngine(vector_store)
        self.triage_engine = triage_engine or TriageEngine()
        self.response_generator = response_generator or ResponseGenerator()
        self.feedback_manager = FeedbackManager()

    def load_data(self, file_path):
        """
        Load data into the vector store

        Args:
            file_path (str): Path to the processed data file

        Returns:
            int: Number of tickets loaded
        """
        df = pd.read_csv(file_path)
        return self.retrieval_engine.vector_store.add_tickets(df)

    def process_query(self, query):
        """
        Process a user query and generate a response

        Args:
            query (str): User query

        Returns:
            dict: Generated response with metadata
        """
        print("\n" + "=" * 80)
        print(f"PROCESSING QUERY: \"{query}\"")
        print("=" * 80)

        # Retrieve relevant context
        print("\nRETRIEVAL PHASE:")
        retrieval_result = self.retrieval_engine.format_context_for_prompt(query)
        top_similarity = retrieval_result["top_similarity"]
        print(f"- Top similarity score: {top_similarity:.4f}")
        print(f"- Retrieved ticket IDs: {', '.join(retrieval_result['ticket_ids'])}")

        # Determine if escalation is needed
        print("\nTRIAGE PHASE:")
        triage_result = self.triage_engine.should_escalate(
            query,
            retrieval_result["top_similarity"]
        )
        print(f"- Confidence level: {triage_result['confidence'].upper()}")
        print(f"- Should escalate: {triage_result['escalate']}")
        print(f"- Reason: {triage_result['reason']}")

        # Generate response
        print("\nRESPONSE GENERATION PHASE:")
        response = self.response_generator.generate_response(
            query,
            retrieval_result["formatted_context"],
            triage_result
        )

        # Add retrieved ticket IDs and similarity to the response
        response["relevant_ticket_ids"] = retrieval_result["ticket_ids"]
        response["similarity_score"] = top_similarity

        print(f"- Response generated ({len(response['response_text'])} chars)")
        print(f"- Final confidence: {response['confidence'].upper()}")
        print(f"- Final escalation decision: {response['should_escalate']}")
        print("=" * 80)

        return response

    def run_app(self):
        """Run the Streamlit app"""
        # Regular chat interface continues below
        st.title("🤖 Automated Support | CAFB")

        # Sidebar for configuration
        with st.sidebar:
            st.header("Configuration")
            data_file = st.file_uploader("Upload processed ticket data (CSV)", type="csv")

            if data_file:
                if st.button("Load Data"):
                    with st.spinner("Loading data into vector database..."):
                        # Save uploaded file temporarily
                        temp_path = "temp_data.csv"
                        with open(temp_path, "wb") as f:
                            f.write(data_file.getvalue())

                        # Load the data
                        num_loaded = self.load_data(temp_path)
                        st.success(f"Successfully loaded {num_loaded} tickets")

            # Debug options in sidebar
            st.divider()
            st.header("Debug Options")
            show_debug = st.checkbox("Show debug information", value=True)

            # Feedback Option
            st.divider()
            st.header("Feedback Summary")
            feedback_summary = self.feedback_manager.get_feedback_summary()
            st.write(f"Total feedback: {feedback_summary['total']}")
            if feedback_summary['total'] > 0:
                st.write(f"👍 Positive: {feedback_summary['positive_percent']}%")

                # Show export option if there's feedback
                if st.button("Export Feedback"):
                    export_path = self.feedback_manager.export_feedback_csv()
                    st.success(f"Feedback exported to {export_path}")

            st.divider()
            st.write("Customer Service Chatbot")
            st.write("Ask questions about orders, deliveries, returns, or other service issues.")

            # Add database explorer
            st.divider()
            st.header("Database Explorer")

            # Initialize a session state for storing relevant tickets
            if "relevant_tickets" not in st.session_state:
                st.session_state.relevant_tickets = []

            # Display currently relevant tickets if available
            if st.session_state.relevant_tickets:
                st.subheader(f"Relevant Documents ({len(st.session_state.relevant_tickets)})")

                for i, (ticket_id, ticket_content) in enumerate(st.session_state.relevant_tickets):
                    with st.expander(f"Document: {ticket_id}"):
                        st.text(ticket_content[:800] + "..." if len(ticket_content) > 800 else ticket_content)
            else:
                st.write("No documents retrieved yet. Ask a question to see relevant tickets.")

        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # Show debug information if it exists and debug is enabled
                if show_debug and message["role"] == "assistant" and "metadata" in message:
                    with st.expander("View Response Details"):
                        metadata = message["metadata"]

                        st.write("**Confidence Level:**", metadata.get("confidence", "Unknown").upper())

                        if metadata.get("should_escalate"):
                            st.warning(f"⚠️ This query may need human attention: {metadata.get('reason')}")

                        if "relevant_ticket_ids" in metadata:
                            st.write("**Based on these tickets:**")
                            for ticket_id in metadata["relevant_ticket_ids"]:
                                st.write(f"- {ticket_id}")

                        if "similarity_score" in metadata:
                            st.write(f"**Top Similarity Score:** {metadata['similarity_score']:.4f}")

        # Chat input
        if prompt := st.chat_input("How can I help with your order today?"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate and display response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                with st.spinner("Thinking..."):
                    # Retrieve context and calculate similarity
                    retrieval_result = self.retrieval_engine.format_context_for_prompt(prompt)
                    top_similarity = retrieval_result["top_similarity"]

                    # Store the relevant tickets in session state for sidebar display
                    st.session_state.relevant_tickets = []

                    # Use existing methods to get documents
                    for ticket_id in retrieval_result["ticket_ids"]:
                        try:
                            # Get the document directly from the collection
                            ticket_result = self.retrieval_engine.vector_store.collection.get(
                                ids=[ticket_id]
                            )

                            if ticket_result and ticket_result['documents'] and len(ticket_result['documents']) > 0:
                                ticket_doc = ticket_result['documents'][0]
                                st.session_state.relevant_tickets.append((ticket_id, ticket_doc))
                        except Exception as e:
                            print(f"Error retrieving document {ticket_id}: {e}")

                    # Determine confidence and escalation need
                    triage_result = self.triage_engine.should_escalate(
                        prompt, top_similarity
                    )

                    response = self.response_generator.generate_response(
                        prompt,
                        retrieval_result["formatted_context"],
                        triage_result
                    )

                    # Add retrieved ticket IDs and similarity to the response
                    response["relevant_ticket_ids"] = retrieval_result["ticket_ids"]
                    response["similarity_score"] = top_similarity

                    # Display confidence indicator if enabled
                    if show_debug:
                        confidence_color = {
                            "high": "green",
                            "medium": "orange",
                            "low": "red"
                        }.get(response["confidence"], "gray")

                        st.markdown(
                            f"<span style='color:{confidence_color};font-weight:bold'>Confidence: {response['confidence'].upper()}</span>",
                            unsafe_allow_html=True)

                    if response["should_escalate"]:
                        st.warning(f"⚠️ This query may need human attention: {response['reason']}")

                    # Display the response
                    message_placeholder.markdown(response["response_text"])

                    # Show debug information if enabled
                    if show_debug:
                        with st.expander("View Response Details"):
                            st.write("**Query:**", prompt)
                            st.write("**Confidence Level:**", response["confidence"].upper())
                            st.write("**Should Escalate:**", response["should_escalate"])
                            st.write("**Reason:**", response["reason"])
                            st.write("**Top Similarity Score:**", f"{top_similarity:.4f}")

                    # End of the with spinner block
                    # IMPORTANT: Move the button outside the spinner block

                    # Store the current query and response for potential human agent handoff
                    st.session_state.current_query = prompt
                    st.session_state.current_bot_response = response["response_text"]
                    st.session_state.current_reason = response["reason"]
                    st.session_state.current_should_escalate = response["should_escalate"]
                    st.session_state.current_confidence = response["confidence"]

            # Add a human agent button if needed
            if st.session_state.get("current_should_escalate", False) or st.session_state.get("current_confidence",
                                                                                              "high") != "high":

                # Somewhere in your chat response area, add this simple button:
                if st.button("Talk to a Human Agent", key="simple_agent_button"):
                    st.session_state.show_agent = True
                    st.rerun()

            # Inside the assistant chat message block, after displaying the response
            # Add feedback buttons
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("👍 Helpful", key=f"helpful_{len(st.session_state.messages)}"):
                    self.feedback_manager.save_feedback(
                        query=prompt,
                        response=response["response_text"],
                        feedback_type="positive",
                        confidence=response["confidence"],
                        ticket_ids=response["relevant_ticket_ids"],
                        similarity=top_similarity
                    )
                    st.success("Thanks for your feedback!")

            with col2:
                if st.button("👎 Not Helpful", key=f"not_helpful_{len(st.session_state.messages)}"):
                    feedback_text = st.text_input(
                        "What was wrong with the response?",
                        key=f"feedback_text_{len(st.session_state.messages)}"
                    )
                    if st.button("Submit Feedback", key=f"submit_feedback_{len(st.session_state.messages)}"):
                        self.feedback_manager.save_feedback(
                            query=prompt,
                            response=response["response_text"],
                            feedback_type="negative",
                            confidence=response["confidence"],
                            ticket_ids=response["relevant_ticket_ids"],
                            similarity=top_similarity,
                            comments=feedback_text
                        )
                        st.success("Thanks for your feedback!")

            # Add assistant response to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": response["response_text"],
                "metadata": {
                    "confidence": response["confidence"],
                    "should_escalate": response["should_escalate"],
                    "reason": response["reason"],
                    "relevant_ticket_ids": response["relevant_ticket_ids"],
                    "similarity_score": top_similarity
                }
            })