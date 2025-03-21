import streamlit as st
import pandas as pd
import os
from survey_analytics import SurveyAnalytics
from survey_chatbot import SurveyChatbot

def main():
    st.set_page_config(page_title="Survey Analytics", page_icon="📊", layout="wide")
    st.title("Surveyed - Survey Analytics Dashboard")
    
    # Sidebar for data source selection
    st.sidebar.header("Data Settings")
    json_dir = st.sidebar.text_input("JSON Data Directory", "survey_data")
    
    # Initialize analytics with the selected data directory
    analytics = SurveyAnalytics(json_dir)
    
    # Check if directory exists
    if not os.path.exists(json_dir):
        st.sidebar.warning(f"Directory '{json_dir}' does not exist.")
        if st.sidebar.button("Create Sample JSON Data"):
            from json_data_loader import SurveyJSONLoader
            loader = SurveyJSONLoader(json_dir)
            if loader.create_sample_data():
                st.sidebar.success(f"Created sample data in '{json_dir}' directory")
                # Reload analytics with new data
                analytics = SurveyAnalytics(json_dir)
            else:
                st.sidebar.error("Failed to create sample data")
    
    # Display survey information
    metadata = analytics.get_survey_metadata()
    st.sidebar.subheader("Survey Information")
    st.sidebar.write(f"**Title:** {metadata.get('survey_title', 'N/A')}")
    st.sidebar.write(f"**ID:** {metadata.get('survey_id', 'N/A')}")
    st.sidebar.write(f"**Created:** {metadata.get('created_at', 'N/A')}")
    st.sidebar.write(f"**Questions:** {len(metadata.get('questions', {}))}")
    
    # Get basic stats
    stats = analytics.get_basic_stats()
    response_counts = analytics.get_response_counts()
    
    # Display basic statistics
    st.header("Survey Overview")
    
    # Check if we have data
    if stats["total_responses"] == 0:
        st.warning("No survey data available. Please check your data directory or create sample data.")
    else:
        # Display key metrics that work for any survey
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Responses", stats["total_responses"])
        
        with col2:
            st.metric("Average Completion Time", f"{stats['avg_completion_time']:.0f} sec" if stats['avg_completion_time'] > 0 else "N/A")
        
        # Display survey questions and response counts
        st.subheader("Survey Questions")
        questions = analytics.get_questions_summary()
        
        if questions:
            # Create tabs for each question
            question_ids = list(questions.keys())
            if question_ids:
                # Group questions into tabs (max 5 per tab to avoid crowding)
                tab_size = 5
                tab_groups = [question_ids[i:i + tab_size] for i in range(0, len(question_ids), tab_size)]
                
                # Create tabs for each group
                tabs = st.tabs([f"Questions {i*tab_size+1}-{min((i+1)*tab_size, len(question_ids))}" for i in range(len(tab_groups))])
                
                for i, tab in enumerate(tabs):
                    with tab:
                        for q_id in tab_groups[i]:
                            with st.expander(f"{questions[q_id]}", expanded=False):
                                # Get data for this question
                                q_data = analytics.get_data_for_question(q_id)
                                
                                if not q_data.empty:
                                    # Show basic stats for this question
                                    if pd.api.types.is_numeric_dtype(q_data):
                                        # For numeric questions
                                        st.write(f"**Average**: {q_data.mean():.2f}")
                                        st.write(f"**Median**: {q_data.median():.2f}")
                                        st.write(f"**Range**: {q_data.min()} to {q_data.max()}")
                                    else:
                                        # For categorical/text questions
                                        # Show top 5 responses
                                        value_counts = q_data.value_counts().head(5)
                                        if not value_counts.empty:
                                            st.write("**Top Responses:**")
                                            for val, count in value_counts.items():
                                                st.write(f"- {val}: {count} responses ({count/len(q_data)*100:.1f}%)")
                                else:
                                    st.write("No data available for this question.")
        else:
            st.info("No questions found in the survey data.")
        
        # Display response counts by user type if available
        if response_counts:
            st.subheader("Responses by User Type")
            
            # Create a DataFrame for better display
            user_type_df = pd.DataFrame({
                'User Type': list(response_counts.keys()),
                'Count': list(response_counts.values())
            })
            
            # Display as a table
            st.table(user_type_df)
    
    # Display questions
    # questions = analytics.get_questions_summary()
    # if questions:
    #     with st.expander("Survey Questions", expanded=False):
    #         st.subheader("Available Survey Questions")
            
    #         # Display each question with its corresponding column name
    #         for column, question_text in questions.items():
    #             st.write(f"**{column}**: {question_text}")
    
    # Survey Chatbot section
    st.header("Survey Chatbot")
    st.write("Ask questions about your survey data to gain insights.")
    
    # Initialize chatbot
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = SurveyChatbot(analytics)
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "visualization" in message and message["visualization"]:
                st.image(f"data:image/png;base64,{message['visualization']}")
    
    # Get user input
    if prompt := st.chat_input("Ask about your survey data"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get response from chatbot
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.chatbot.ask(prompt)
                st.write(response["text"])
                if response["visualization"]:
                    st.image(f"data:image/png;base64,{response['visualization']}")
        
        # Add assistant response to chat history
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response["text"],
            "visualization": response["visualization"]
        })

if __name__ == "__main__":
    main()
