import streamlit as st
import os
from survey_analytics import SurveyAnalytics
from survey_chatbot import SurveyChatbot

# Set page config must be the first Streamlit command
st.set_page_config(page_title="Survey Insight Bot", page_icon="📊", layout="wide")

# Initialize session state for analytics and chatbot - do this outside the main function
if 'analytics' not in st.session_state:
    print("Loaded survey data from JSON files in 'survey_data'")
    st.session_state.analytics = SurveyAnalytics("survey_data")
    
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = SurveyChatbot(st.session_state.analytics)
    
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Add a flag to track if we need to process a message
if 'process_message' not in st.session_state:
    st.session_state.process_message = False
    
if 'current_message' not in st.session_state:
    st.session_state.current_message = ""

# Function to set the message processing flag
def set_message_to_process():
    if st.session_state.input_field and st.session_state.input_field.strip():
        st.session_state.current_message = st.session_state.input_field
        st.session_state.process_message = True
        st.session_state.input_field = ""  # Clear the input box

def main():
    # Custom CSS to match the design in the images
    st.markdown("""
    <style>
    /* Main theme colors */
    :root {
        --main-bg-color: #ffffff;
        --accent-color: #4CAF50;  /* Green accent color from the send button */
        --border-color: #e0e0e0;
        --text-color: #333333;
        --light-bg: #f8f9fa;
    }
    
    /* Page styling */
    .stApp {
        background-color: var(--main-bg-color);
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: var(--text-color);
        font-weight: 600;
    }
    
    /* Chat container styling */
    .chat-container {
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 20px;
        margin: 20px auto;
        max-width: 800px;
        background-color: var(--main-bg-color);
    }
    
    /* Message styling - improved colors */
    .user-message {
        background-color: #E9F7EF;  /* Light green background */
        color: #333333;  /* Dark text for contrast */
        border-radius: 18px;
        padding: 10px 15px;
        margin: 5px 0;
        max-width: 80%;
        align-self: flex-end;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    .assistant-message {
        background-color: #F5F5F5;  /* Light gray background */
        color: #333333;  /* Dark text for contrast */
        border-radius: 18px;
        padding: 10px 15px;
        margin: 5px 0;
        max-width: 80%;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Custom button styling */
    .stButton>button {
        background-color: var(--accent-color);
        color: white;
        border-radius: 20px;
        border: none;
        padding: 5px 15px;
    }
    
    /* Chat input styling - cleaner edges and better focus */
    .stTextInput>div>div>input {
        border-radius: 20px;
        border: 1px solid #e0e0e0;  /* Lighter border */
        padding: 10px 15px;
        background-color: white;
        color: #000000;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);  /* Subtle shadow */
        transition: all 0.2s ease;
    }
    
    /* Input focus state */
    .stTextInput>div>div>input:focus {
        border-color: var(--accent-color);
        box-shadow: 0 1px 3px rgba(76, 175, 80, 0.2);
        outline: none;
    }
    
    /* Send button styling */
    div[data-testid="stButton"] > button {
        background-color: #4CAF50;
        color: white;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        border: none;
        box-shadow: none;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    div[data-testid="stButton"] > button:hover {
        background-color: #3d8b40;  /* Darker green on hover */
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Hide sidebar by default */
    [data-testid="stSidebar"][aria-expanded="true"] {
        display: none;
    }
    
    /* Center the main content */
    .main .block-container {
        max-width: 1000px;
        padding-top: 2rem;
        padding-bottom: 2rem;
        margin: 0 auto;
    }
    
    /* Remove padding from the main container */
    .stApp {
        padding-top: 0;
    }
    
    /* Hide fullscreen button and other menu options */
    .stDeployButton, .stToolbar {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main chat interface container
    with st.container():
        # Header section with title and description
        st.markdown("""
        <div class="chat-container">
            <h2 style="color: #333; margin-bottom: 20px; text-align: center;">
                How can we <span style="color: #4CAF50;">assist</span> you today?
            </h2>
            <p style="color: #666; margin-bottom: 30px; text-align: center;">
                Ask Insight Bot anything about your survey responses! Get real-time analytics, 
                trends, and key insights in seconds. Just type your question and uncover the 
                data-driven answers you need.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create a container for chat messages
        chat_container = st.container()
        
        # Display chat messages with custom styling
        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(f"""
                    <div style="display: flex; justify-content: flex-end;">
                        <div class="user-message">
                            {message["content"]}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="display: flex; justify-content: flex-start;">
                        <div class="assistant-message">
                            {message["content"]}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if "visualization" in message and message["visualization"]:
                        st.image(f"data:image/png;base64,{message['visualization']}")
        
        # Simple input and button with callback for Enter key
        st.markdown('<div style="max-width: 800px; margin: 0 auto;">', unsafe_allow_html=True)
        col1, col2 = st.columns([6, 1])
        
        with col1:
            # Use on_change to handle Enter key press but don't process in the callback
            st.text_input(
                "Ask anything", 
                key="input_field", 
                label_visibility="collapsed",
                on_change=set_message_to_process
            )
        
        with col2:
            if st.button("Send", key="send_button"):
                set_message_to_process()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Process message outside of any callbacks
        if st.session_state.process_message:
            user_message = st.session_state.current_message
            
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_message})
            
            # Get response from chatbot
            with st.spinner("Thinking..."):
                response = st.session_state.chatbot.ask(user_message)
                
                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response["text"],
                    "visualization": response["visualization"] if "visualization" in response else None
                })
            
            # Reset the flag
            st.session_state.process_message = False
            st.session_state.current_message = ""
            
            # Now we can safely rerun
            st.rerun()

if __name__ == "__main__":
    main()
