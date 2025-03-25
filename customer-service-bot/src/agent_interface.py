"""
Agent Interface Module - Allows human agents to respond to escalated conversations
"""
import streamlit as st
import time
import pandas as pd
from datetime import datetime


class AgentInterface:
    def __init__(self, feedback_manager=None):
        """Initialize the agent interface"""
        self.feedback_manager = feedback_manager

    def run_agent_app(self):
        """Run the agent interface app"""
        st.title("Customer Service - Agent Portal")

        # Simple authentication (in a real app, you'd use proper authentication)
        if "agent_authenticated" not in st.session_state:
            st.session_state.agent_authenticated = False

        if not st.session_state.agent_authenticated:
            with st.form("login_form"):
                st.subheader("Agent Login")
                agent_name = st.text_input("Agent Name")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")

                if submit and agent_name and password == "agent123":  # Very simple password for demo
                    st.session_state.agent_authenticated = True
                    st.session_state.agent_name = agent_name
                    st.rerun()
                elif submit:
                    st.error("Invalid credentials")

            return

        # Agent interface after authentication
        st.write(f"Logged in as: {st.session_state.agent_name}")

        # Get pending conversations that need agent attention
        pending_conversations = self._get_pending_conversations()

        if not pending_conversations:
            st.info("No pending conversations require your attention at this time.")

            # Add a refresh button
            if st.button("Refresh"):
                st.rerun()

            return

        # Display each conversation that needs attention
        for idx, conv in enumerate(pending_conversations):
            with st.expander(f"Conversation {idx + 1}: {conv['query'][:50]}...", expanded=True):
                st.write("**Customer Query:**")
                st.write(conv['query'])

                st.write("**Bot Response:**")
                st.write(conv['bot_response'])

                st.write("**Reason for Escalation:**")
                st.write(conv['reason'])

                st.write("**Time:**")
                st.write(conv['timestamp'])

                # Response form
                with st.form(f"response_form_{idx}"):
                    agent_response = st.text_area("Your Response:", key=f"response_{idx}")
                    submitted = st.form_submit_button("Send Response")

                    if submitted and agent_response:
                        # Handle the agent's response
                        self._handle_agent_response(conv, agent_response)
                        st.success("Response sent!")
                        time.sleep(1)  # Brief pause to show the success message
                        st.rerun()  # Refresh the page

    def _get_pending_conversations(self):
        """
        Get conversations that need agent attention
        In a real implementation, this would query a database
        """
        # For demo purposes, we'll use session state to store pending conversations
        if "pending_conversations" not in st.session_state:
            st.session_state.pending_conversations = []

        return st.session_state.pending_conversations

    def _handle_agent_response(self, conversation, response):
        """Handle the agent's response to a conversation"""
        # In a real implementation, this would update a database
        # For demo purposes, we'll just remove from pending
        if "pending_conversations" in st.session_state:
            # Mark this conversation as handled
            st.session_state.pending_conversations = [
                conv for conv in st.session_state.pending_conversations
                if conv['id'] != conversation['id']
            ]

            # Store the agent response in session state
            if "agent_responses" not in st.session_state:
                st.session_state.agent_responses = {}

            st.session_state.agent_responses[conversation['id']] = {
                'response': response,
                'agent': st.session_state.agent_name,
                'timestamp': datetime.now().isoformat()
            }

            # Log the agent response if feedback manager exists
            if self.feedback_manager:
                self.feedback_manager.save_feedback(
                    query=conversation['query'],
                    response=response,
                    feedback_type="agent_response",
                    confidence="human",
                    comments=f"Agent: {st.session_state.agent_name}"
                )


def add_to_agent_queue(query, bot_response, reason):
    """
    Add a conversation to the agent queue
    This function can be called from the main interface
    """
    if "pending_conversations" not in st.session_state:
        st.session_state.pending_conversations = []

    # Generate a unique ID for this conversation
    conv_id = f"conv_{int(time.time())}_{len(st.session_state.pending_conversations)}"

    # Add to pending conversations
    st.session_state.pending_conversations.append({
        'id': conv_id,
        'query': query,
        'bot_response': bot_response,
        'reason': reason,
        'timestamp': datetime.now().isoformat()
    })

    return conv_id


def get_agent_response(conv_id):
    """Check if there's an agent response for a specific conversation"""
    if "agent_responses" in st.session_state and conv_id in st.session_state.agent_responses:
        return st.session_state.agent_responses[conv_id]
    return None