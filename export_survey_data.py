import os
import pandas as pd
from survey_analytics import SurveyAnalytics

def export_survey_data_to_csv():
    """
    Export the sample survey data and questions to CSV files for Firebase integration.
    
    This creates two CSV files:
    1. survey_data.csv - Contains all the survey responses
    2. survey_questions.csv - Contains the mapping of column names to question text
    """
    # Initialize the SurveyAnalytics class to generate dummy data
    analytics = SurveyAnalytics()
    
    # Get the survey data and metadata
    survey_data = analytics.survey_data
    
    # Extract the dataframe and questions
    df = survey_data['data']
    questions = survey_data['metadata']['questions']
    
    # Create a directory for exports if it doesn't exist
    export_dir = 'exports'
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    
    # Export the survey response data
    data_file_path = os.path.join(export_dir, 'survey_data.csv')
    df.to_csv(data_file_path, index=False)
    print(f"Survey data exported to {data_file_path}")
    
    # Export the questions as a separate CSV
    questions_df = pd.DataFrame([
        {"column_name": col, "question_text": text} 
        for col, text in questions.items()
    ])
    
    # Add other columns that aren't in the questions dictionary
    for col in df.columns:
        if col not in questions:
            if col == 'response_id':
                description = 'Unique identifier for each survey response'
            elif col == 'timestamp':
                description = 'Date and time when the survey was submitted'
            elif col == 'age_group':
                description = 'Age group of the respondent'
            elif col == 'user_type':
                description = 'Type of user account (Free, Basic, Premium, Enterprise)'
            elif col == 'completion_time':
                description = 'Time taken to complete the survey in seconds'
            else:
                description = f'Additional data field: {col}'
            
            questions_df = pd.concat([
                questions_df, 
                pd.DataFrame([{"column_name": col, "question_text": description}])
            ])
    
    questions_file_path = os.path.join(export_dir, 'survey_questions.csv')
    questions_df.to_csv(questions_file_path, index=False)
    print(f"Survey questions exported to {questions_file_path}")
    
    # Export metadata as JSON for additional context
    metadata = survey_data['metadata']
    metadata_df = pd.DataFrame([{
        "key": key,
        "value": value
    } for key, value in metadata.items() if key != 'questions'])
    
    metadata_file_path = os.path.join(export_dir, 'survey_metadata.csv')
    metadata_df.to_csv(metadata_file_path, index=False)
    print(f"Survey metadata exported to {metadata_file_path}")
    
    return {
        'data_path': data_file_path,
        'questions_path': questions_file_path,
        'metadata_path': metadata_file_path
    }

if __name__ == "__main__":
    export_survey_data_to_csv()