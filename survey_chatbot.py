import os
import openai
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
from collections import Counter
import time

class SurveyChatbot:
    def __init__(self, analytics_engine):
        """
        Initialize the survey chatbot with an analytics engine.
        
        Args:
            analytics_engine: An instance of SurveyAnalytics
        """
        # Load environment variables
        load_dotenv()
        
        # Set OpenAI API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Warning: OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=api_key)
        self.analytics = analytics_engine
        self.conversation_history = []
        
        # Analyze the survey data structure once during initialization
        self._analyze_survey_structure()
        
    def _analyze_survey_structure(self):
        """
        Analyze the survey data structure to understand available fields and their types.
        This helps the chatbot adapt to any survey structure.
        """
        df = self.analytics.survey_data['data']
        
        # Store column information
        self.columns = list(df.columns) if not df.empty else []
        self.column_types = {}
        self.numeric_columns = []
        self.categorical_columns = []
        self.datetime_columns = []
        self.text_columns = []
        
        # If dataframe is empty, we can't analyze columns
        if df.empty:
            return
            
        # Analyze each column
        for col in self.columns:
            # Skip metadata columns
            if col in ['response_id']:
                continue
                
            # Check column type
            if pd.api.types.is_numeric_dtype(df[col]):
                self.numeric_columns.append(col)
                self.column_types[col] = 'numeric'
            elif pd.api.types.is_datetime64_dtype(df[col]):
                self.datetime_columns.append(col)
                self.column_types[col] = 'datetime'
            else:
                # Check if it's categorical (few unique values) or text
                unique_ratio = df[col].nunique() / len(df)
                if unique_ratio < 0.2:  # If less than 20% of values are unique
                    self.categorical_columns.append(col)
                    self.column_types[col] = 'categorical'
                else:
                    self.text_columns.append(col)
                    self.column_types[col] = 'text'
        
        # Get question text mappings
        self.questions = self.analytics.get_questions_summary()
        
    def _identify_relevant_columns(self, query):
        """
        Identify columns in the survey data that are relevant to the user's query.
        
        Args:
            query (str): The user's query
            
        Returns:
            list: List of relevant column names
        """
        # If no data is available, return empty list
        if not self.columns:
            return []
            
        # Get question text for each column
        question_texts = {}
        for col in self.columns:
            if col in self.questions:
                question_texts[col] = self.questions[col]
            else:
                question_texts[col] = col.replace('_', ' ').title()
        
        # Create a prompt to identify relevant columns
        prompt = f"""
        I have survey data with the following columns:
        {', '.join([f"{col} ({question_texts.get(col, col)})" for col in self.columns])}
        
        The user is asking: "{query}"
        
        Which columns are most relevant to answering this query? Return only the column names separated by commas, with no additional text.
        If no columns are relevant, return "None".
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100
            )
            
            relevant_columns = response.choices[0].message.content.strip()
            
            if relevant_columns.lower() == "none":
                return []
                
            # Parse the response and clean up column names
            columns = [col.strip() for col in relevant_columns.split(',')]
            
            # Filter to only include actual columns in the dataset
            valid_columns = [col for col in columns if col in self.columns]
            
            return valid_columns
        except Exception as e:
            print(f"Error identifying relevant columns: {e}")
            return []

    def ask(self, query):
        """
        Process a user query about the survey data.
        
        Args:
            query (str): The user's question about the survey data
            
        Returns:
            dict: A dictionary containing the response text and optional visualization
        """
        # Check if we have data
        if not self.columns or self.analytics.survey_data['data'].empty:
            return {
                "text": "I don't have any survey data to analyze. Please make sure the survey data is loaded correctly.",
                "visualization": None
            }
        
        # Add user query to conversation history
        self.conversation_history.append({"role": "user", "content": query})
        
        # Identify relevant columns
        relevant_columns = self._identify_relevant_columns(query)
        
        # Prepare data summary for the AI
        data_summary = self._prepare_data_summary(relevant_columns)
        
        # Prepare survey metadata
        metadata = self.analytics.get_survey_metadata()
        survey_info = f"""
        Survey Title: {metadata.get('survey_title', 'Unknown')}
        Survey Description: {metadata.get('survey_description', 'No description')}
        Number of Responses: {len(self.analytics.survey_data['data'])}
        Number of Questions: {len(metadata.get('questions', {}))}
        """
        
        # Check if this is a visualization request
        is_visualization_request = any(term in query.lower() for term in 
                                      ['chart', 'graph', 'plot', 'visual', 'show me', 'display', 'histogram', 'bar', 'pie'])
        
        # Prepare the system prompt
        if is_visualization_request:
            # Prompt for visualization generation
            system_prompt = f"""
            You are a helpful survey analysis assistant with expertise in data visualization using matplotlib and seaborn.
            
            The survey information is:
            {survey_info}
            
            The data summary is:
            {data_summary}
            
            The user is asking for a visualization. You must:
            1. Analyze what type of visualization would best answer their query
            2. Generate Python code using matplotlib/seaborn to create this visualization
            3. Format your response in two parts:
               a. A brief explanation of the insights from the data
               b. The Python code for the visualization, enclosed in [CODE] tags
            
            Available data:
            - df: pandas DataFrame containing the survey data
            - The following columns are available: {self.columns}
            
            Example response format:
            The satisfaction ratings show that most users are highly satisfied with the product.
            
            [CODE]
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Create the visualization
            plt.figure(figsize=(10, 6))
            sns.countplot(x='satisfaction', data=df)
            plt.title('Distribution of Satisfaction Ratings')
            plt.xlabel('Satisfaction (1-5)')
            plt.ylabel('Number of Responses')
            [/CODE]
            """
        else:
            # Standard analysis prompt
            system_prompt = f"""
            You are a helpful survey analysis assistant. You help analyze survey data and provide insights.
            
            The survey information is:
            {survey_info}
            
            The data summary is:
            {data_summary}
            
            When responding:
            1. Be concise and focus on insights from the data
            2. If you think a visualization would help, suggest that the user ask for a specific chart
            3. If you can't answer the question with the available data, explain why
            4. Use a friendly, professional tone
            """
        
        # Prepare messages for the API call
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history (limited to last 5 exchanges)
        for msg in self.conversation_history[-10:]:
            messages.append(msg)
        
        try:
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=800 if is_visualization_request else 500
            )
            
            # Get the response text
            response_text = response.choices[0].message.content.strip()
            
            # Add assistant response to conversation history
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            # Check if visualization code is included
            visualization = None
            if "[CODE]" in response_text and "[/CODE]" in response_text:
                # Extract code
                code_parts = response_text.split("[CODE]")
                explanation = code_parts[0].strip()
                code = code_parts[1].split("[/CODE]")[0].strip()
                
                # Generate visualization from code
                visualization = self._execute_visualization_code(code)
                
                # Update response text to remove code
                response_text = explanation + "\n\n(Visualization generated)"
            
            return {
                "text": response_text,
                "visualization": visualization
            }
        except Exception as e:
            error_message = f"I encountered an error while processing your question: {str(e)}"
            print(error_message)
            return {
                "text": error_message,
                "visualization": None
            }
            
    def _execute_visualization_code(self, code):
        """
        Execute the generated visualization code and return the resulting figure as base64.
        
        Args:
            code (str): The matplotlib/seaborn code to execute
            
        Returns:
            str: Base64 encoded image or None if execution failed
        """
        try:
            # Create a safe execution environment
            df = self.analytics.survey_data['data']
            
            # Create a new figure
            plt.figure(figsize=(10, 6))
            
            # Execute the code
            exec(code)
            
            # Adjust layout
            plt.tight_layout()
            
            # Convert to base64
            img_str = self._fig_to_base64(plt.gcf())
            
            # Close the figure to free memory
            plt.close()
            
            return img_str
        except Exception as e:
            print(f"Error executing visualization code: {e}")
            print(f"Code: {code}")
            return None

    def _prepare_data_summary(self, relevant_columns):
        """
        Prepare a summary of the data for the relevant columns.
        
        Args:
            relevant_columns (list): List of column names that are relevant to the query
            
        Returns:
            str: A text summary of the data
        """
        df = self.analytics.survey_data['data']
        
        if df.empty:
            return "No data available."
            
        if not relevant_columns:
            # Provide a general summary
            return f"The survey has {len(df)} responses across {len(self.columns)} fields."
        
        summary = []
        
        # Add summary for each relevant column
        for col in relevant_columns:
            if col not in df.columns:
                continue
                
            # Get question text if available
            question = self.questions.get(col, col.replace('_', ' ').title())
            
            # Summarize based on column type
            if col in self.numeric_columns:
                summary.append(f"{question} (numeric):")
                summary.append(f"  - Range: {df[col].min()} to {df[col].max()}")
                summary.append(f"  - Average: {df[col].mean():.2f}")
                summary.append(f"  - Median: {df[col].median()}")
            
            elif col in self.categorical_columns:
                summary.append(f"{question} (categorical):")
                value_counts = df[col].value_counts()
                for value, count in value_counts.items():
                    percentage = count / len(df) * 100
                    summary.append(f"  - {value}: {count} responses ({percentage:.1f}%)")
            
            elif col in self.datetime_columns:
                summary.append(f"{question} (date/time):")
                summary.append(f"  - Earliest: {df[col].min()}")
                summary.append(f"  - Latest: {df[col].max()}")
            
            else:
                # Text column or other type
                summary.append(f"{question} (text/other):")
                summary.append(f"  - {df[col].nunique()} unique values")
        
        return "\n".join(summary)
    
    def _fig_to_base64(self, fig):
        """
        Convert a matplotlib figure to a base64 encoded string.
        
        Args:
            fig (matplotlib.figure.Figure): The figure to convert
            
        Returns:
            str: Base64 encoded image
        """
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        return img_str
        
    def clear_conversation(self):
        """Clear the conversation history."""
        self.conversation_history = []