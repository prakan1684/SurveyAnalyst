import streamlit as st
import os
from survey_analytics import SurveyAnalytics
from survey_chatbot import SurveyChatbot
from chat_history.chat_history_manager import ChatHistoryManager

# Set page config must be the first Streamlit command
st.set_page_config(page_title="Survey Insight Bot", page_icon="📊", layout="wide")

# Initialize session state for analytics and chatbot - do this outside the main function
if 'analytics' not in st.session_state:
    print("Loaded survey data from JSON files in 'survey_data'")
    st.session_state.analytics = SurveyAnalytics("survey_data")
    
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = SurveyChatbot(st.session_state.analytics)

# Initialize chat history manager
if 'chat_history_manager' not in st.session_state:
    st.session_state.chat_history_manager = ChatHistoryManager()

# Initialize current chat ID
if 'current_chat_id' not in st.session_state:
    # Try to get the most recent chat or create a new one
    chats = st.session_state.chat_history_manager.get_all_chats()
    if chats:
        st.session_state.current_chat_id = chats[0]['id']
        st.session_state.messages = chats[0].get('messages', [])
    else:
        st.session_state.current_chat_id = st.session_state.chat_history_manager.create_new_chat()
        st.session_state.messages = []
elif 'messages' not in st.session_state:
    # Load messages for the current chat
    current_chat = st.session_state.chat_history_manager.get_chat(st.session_state.current_chat_id)
    if current_chat:
        st.session_state.messages = current_chat.get('messages', [])
    else:
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

# Function to create a new chat
def create_new_chat():
    st.session_state.current_chat_id = st.session_state.chat_history_manager.create_new_chat()
    st.session_state.messages = []
    st.rerun()

# Function to switch to a different chat
def switch_to_chat(chat_id):
    st.session_state.current_chat_id = chat_id
    current_chat = st.session_state.chat_history_manager.get_chat(chat_id)
    st.session_state.messages = current_chat.get('messages', [])
    st.rerun()

# Function to delete a chat
def delete_chat(chat_id):
    st.session_state.chat_history_manager.delete_chat(chat_id)
    
    # If we deleted the current chat, switch to another
    if chat_id == st.session_state.current_chat_id:
        chats = st.session_state.chat_history_manager.get_all_chats()
        if chats:
            st.session_state.current_chat_id = chats[0]['id']
            st.session_state.messages = chats[0].get('messages', [])
        else:
            # No chats left, create a new one
            st.session_state.current_chat_id = st.session_state.chat_history_manager.create_new_chat()
            st.session_state.messages = []
    
    st.rerun()

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
    
    /* Hide fullscreen button and other menu options */
    .stDeployButton, .stToolbar {
        display: none !important;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #222222;
        border-right: 1px solid #333333;
        padding: 1rem;
        width: 250px;
    }
    
    section[data-testid="stSidebar"] > div {
        background-color: #222222;
    }
    
    /* Make sure the sidebar is visible */
    [data-testid="stSidebar"][aria-expanded="true"] {
        margin-left: 0px;
        visibility: visible !important;
    }
    
    /* Sidebar toggle button */
    button[kind="headerNoPadding"] {
        display: block !important;
    }
    
    /* Layout adjustments for main content */
    .main .block-container {
        max-width: calc(100% - 250px);
        padding: 2rem;
        margin-left: 250px;
    }
    
    /* Chat history item styling */
    .chat-item {
        display: flex;
        align-items: center;
        padding: 10px 12px;
        border-radius: 8px;
        margin-bottom: 10px;
        cursor: pointer;
        transition: all 0.2s ease;
        color: #e0e0e0;
        text-decoration: none;
        background-color: #333333;
    }
    
    .chat-item:hover {
        background-color: #444444;
    }
    
    .chat-item.active {
        background-color: #4CAF50;
        color: white;
        font-weight: 500;
    }
    
    .chat-item-icon {
        margin-right: 10px;
        font-size: 16px;
    }
    
    .chat-item-text {
        flex-grow: 1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .chat-item-delete {
        opacity: 0.6;
        transition: opacity 0.2s ease;
        cursor: pointer;
        font-size: 16px;
        margin-left: 5px;
    }
    
    .chat-item-delete:hover {
        opacity: 1;
    }
    
    /* Sidebar divider */
    .sidebar-divider {
        margin: 20px 0;
        border-top: 1px solid #444444;
    }
    
    /* New chat button styling */
    .new-chat-btn {
        display: block;
        width: 100%;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 0;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        margin-bottom: 20px;
        text-align: center;
        transition: background-color 0.2s ease;
    }
    
    .new-chat-btn:hover {
        background-color: #3d8b40;
    }
    
    /* Sidebar header */
    .sidebar-header {
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 20px;
        color: white;
    }
    
    /* Hide default Streamlit elements in sidebar */
    section[data-testid="stSidebar"] .stMarkdown p {
        font-size: 14px;
        color: #e0e0e0;
    }
    
    /* Style buttons in sidebar */
    section[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #333333;
        color: #e0e0e0;
        border: none;
    }
    
    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #444444;
        color: white;
    }
    
    </style>
    """, unsafe_allow_html=True)
    
    # Chat history sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-header">Chat History</div>', unsafe_allow_html=True)
        
        # New chat button - only one button now
        if st.button("+ New Chat", key="new_chat_btn", use_container_width=True):
            create_new_chat()
        
        st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)
        
        # List all chats with improved styling
        chats = st.session_state.chat_history_manager.get_all_chats()
        if not chats:
            st.markdown("<p style='color: #888; text-align: center; padding: 20px 0;'>No chat history yet</p>", unsafe_allow_html=True)
        else:
            for chat in chats:
                chat_id = chat['id']
                chat_name = chat['name']
                
                # Create a clickable chat item with better styling
                is_active = chat_id == st.session_state.current_chat_id
                active_class = "active" if is_active else ""
                
                col1, col2 = st.columns([9, 1])
                
                with col1:
                    if st.button(chat_name, key=f"chat_{chat_id}", use_container_width=True, 
                                type="primary" if is_active else "secondary"):
                        switch_to_chat(chat_id)
                
                with col2:
                    if st.button("🗑️", key=f"delete_{chat_id}"):
                        delete_chat(chat_id)
    
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
            
            # Save to TinyDB
            st.session_state.chat_history_manager.add_message_to_chat(
                st.session_state.current_chat_id,
                "user",
                user_message
            )
            
            # Get response from chatbot
            with st.spinner("Thinking..."):
                response = st.session_state.chatbot.ask(user_message)
                
                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response["text"],
                    "visualization": response["visualization"] if "visualization" in response else None
                })
                
                # Save to TinyDB
                st.session_state.chat_history_manager.add_message_to_chat(
                    st.session_state.current_chat_id,
                    "assistant",
                    response["text"],
                    response["visualization"] if "visualization" in response else None
                )
            
            # Reset the flag
            st.session_state.process_message = False
            st.session_state.current_message = ""
            
            # Now we can safely rerun
            st.rerun()

if __name__ == "__main__":
    main()
