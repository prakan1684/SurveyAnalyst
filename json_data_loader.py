
import json
import pandas as pd
import os
from datetime import datetime

class SurveyJSONLoader:
    """
    Loads and manages survey data from JSON files that mimic Firebase API responses.
    Provides easy methods to add, remove, and update questions and responses.
    """
    
    def __init__(self, data_directory="survey_data"):
        """
        Initialize the JSON data loader.
        
        Args:
            data_directory (str): Directory where JSON files are stored
        """
        self.data_directory = data_directory
        
        # Create the directory if it doesn't exist
        if not os.path.exists(data_directory):
            os.makedirs(data_directory)
            
        # Default file paths
        self.questions_file = os.path.join(data_directory, 'questions.json')
        self.responses_file = os.path.join(data_directory, 'responses.json')
        
        # Initialize with empty data if files don't exist
        if not os.path.exists(self.questions_file):
            self._create_default_questions_file()
            
        if not os.path.exists(self.responses_file):
            self._create_default_responses_file()
    
    def _create_default_questions_file(self):
        """Create a default questions file with a basic structure"""
        questions_data = {
            "survey_id": "survey_123",
            "title": "Customer Satisfaction Survey",
            "description": "Help us improve our services by providing your feedback",
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "questions": []
        }
        
        with open(self.questions_file, 'w') as f:
            json.dump(questions_data, f, indent=2)
    
    def _create_default_responses_file(self):
        """Create a default responses file with a basic structure"""
        responses_data = {
            "survey_id": "survey_123",
            "responses": []
        }
        
        with open(self.responses_file, 'w') as f:
            json.dump(responses_data, f, indent=2)
    
    def load_survey_data(self):
        """
        Load survey data from JSON files.
        
        Returns:
            dict: Survey data in the format expected by the chatbot
        """
        try:
            # Load questions data
            with open(self.questions_file, 'r') as f:
                questions_data = json.load(f)
            
            # Load responses data
            with open(self.responses_file, 'r') as f:
                responses_data = json.load(f)
            
            # Process the data
            return self._process_json_data(questions_data, responses_data)
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading JSON data: {e}")
            return None
    
    def _process_json_data(self, questions_data, responses_data):
        """
        Process the JSON data into the format expected by the chatbot.
        
        Args:
            questions_data (dict): Questions data from JSON
            responses_data (dict): Responses data from JSON
            
        Returns:
            dict: Processed survey data
        """
        # Extract questions mapping
        questions = {}
        for q in questions_data.get('questions', []):
            questions[q.get('id', f"q_{len(questions)}")] = q.get('text', 'Unknown question')
        
        # Process responses into a DataFrame
        responses_list = []
        for resp in responses_data.get('responses', []):
            response_dict = {
                'response_id': resp.get('id', ''),
                'timestamp': resp.get('submitted_at', ''),
                'user_type': resp.get('user_type', 'Unknown'),
                'completion_time': resp.get('completion_time', 0)
            }
            
            # Add answers to the response dict
            answers = resp.get('answers', {})
            for q_id, answer in answers.items():
                response_dict[q_id] = answer
            
            # Add any additional fields
            for key, value in resp.items():
                if key not in ['id', 'submitted_at', 'user_type', 'completion_time', 'answers']:
                    response_dict[key] = value
                
            responses_list.append(response_dict)
        
        # Create DataFrame from responses
        df = pd.DataFrame(responses_list) if responses_list else pd.DataFrame()
        
        # Create metadata
        metadata = {
            'survey_id': responses_data.get('survey_id', 'UNKNOWN'),
            'survey_title': questions_data.get('title', 'Survey'),
            'survey_description': questions_data.get('description', ''),
            'created_at': questions_data.get('created_at', ''),
            'questions': questions
        }
        
        return {'data': df, 'metadata': metadata}
    
    # Question Management Methods
    
    def get_questions(self):
        """
        Get all questions from the questions file.
        
        Returns:
            list: List of question dictionaries
        """
        try:
            with open(self.questions_file, 'r') as f:
                questions_data = json.load(f)
            return questions_data.get('questions', [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def add_question(self, question_id, question_text, question_type="text", options=None, scale=None):
        """
        Add a new question to the questions file.
        
        Args:
            question_id (str): Unique identifier for the question
            question_text (str): The text of the question
            question_type (str): Type of question (text, multiple_choice, rating)
            options (list, optional): Options for multiple choice questions
            scale (int, optional): Scale for rating questions
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load current questions
            with open(self.questions_file, 'r') as f:
                questions_data = json.load(f)
            
            # Check if question_id already exists
            for q in questions_data.get('questions', []):
                if q.get('id') == question_id:
                    print(f"Question with ID '{question_id}' already exists.")
                    return False
            
            # Create new question
            new_question = {
                "id": question_id,
                "text": question_text,
                "type": question_type
            }
            
            if options and question_type == "multiple_choice":
                new_question["options"] = options
                
            if scale and question_type == "rating":
                new_question["scale"] = scale
            
            # Add to questions list
            if 'questions' not in questions_data:
                questions_data['questions'] = []
                
            questions_data['questions'].append(new_question)
            
            # Save updated questions
            with open(self.questions_file, 'w') as f:
                json.dump(questions_data, f, indent=2)
                
            print(f"Question '{question_text}' added successfully with ID '{question_id}'.")
            return True
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error adding question: {e}")
            return False
    
    def update_question(self, question_id, question_text=None, question_type=None, options=None, scale=None):
        """
        Update an existing question.
        
        Args:
            question_id (str): ID of the question to update
            question_text (str, optional): New text for the question
            question_type (str, optional): New type for the question
            options (list, optional): New options for multiple choice questions
            scale (int, optional): New scale for rating questions
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load current questions
            with open(self.questions_file, 'r') as f:
                questions_data = json.load(f)
            
            # Find the question to update
            found = False
            for q in questions_data.get('questions', []):
                if q.get('id') == question_id:
                    found = True
                    if question_text:
                        q['text'] = question_text
                    if question_type:
                        q['type'] = question_type
                    if options and (question_type == "multiple_choice" or q.get('type') == "multiple_choice"):
                        q['options'] = options
                    if scale and (question_type == "rating" or q.get('type') == "rating"):
                        q['scale'] = scale
                    break
            
            if not found:
                print(f"Question with ID '{question_id}' not found.")
                return False
            
            # Save updated questions
            with open(self.questions_file, 'w') as f:
                json.dump(questions_data, f, indent=2)
                
            print(f"Question with ID '{question_id}' updated successfully.")
            return True
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error updating question: {e}")
            return False
    
    def remove_question(self, question_id):
        """
        Remove a question from the questions file.
        
        Args:
            question_id (str): ID of the question to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load current questions
            with open(self.questions_file, 'r') as f:
                questions_data = json.load(f)
            
            # Find and remove the question
            initial_count = len(questions_data.get('questions', []))
            questions_data['questions'] = [q for q in questions_data.get('questions', []) if q.get('id') != question_id]
            
            if len(questions_data.get('questions', [])) == initial_count:
                print(f"Question with ID '{question_id}' not found.")
                return False
            
            # Save updated questions
            with open(self.questions_file, 'w') as f:
                json.dump(questions_data, f, indent=2)
                
            print(f"Question with ID '{question_id}' removed successfully.")
            return True
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error removing question: {e}")
            return False
    
    # Response Management Methods
    
    def get_responses(self):
        """
        Get all responses from the responses file.
        
        Returns:
            list: List of response dictionaries
        """
        try:
            with open(self.responses_file, 'r') as f:
                responses_data = json.load(f)
            return responses_data.get('responses', [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def add_response(self, response_data):
        """
        Add a new response to the responses file.
        
        Args:
            response_data (dict): Response data including answers
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load current responses
            with open(self.responses_file, 'r') as f:
                responses_data = json.load(f)
            
            # Ensure response has an ID
            if 'id' not in response_data:
                response_data['id'] = f"resp_{len(responses_data.get('responses', [])) + 1}"
            
            # Ensure response has a timestamp
            if 'submitted_at' not in response_data:
                response_data['submitted_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Add to responses list
            if 'responses' not in responses_data:
                responses_data['responses'] = []
                
            responses_data['responses'].append(response_data)
            
            # Save updated responses
            with open(self.responses_file, 'w') as f:
                json.dump(responses_data, f, indent=2)
                
            print(f"Response with ID '{response_data['id']}' added successfully.")
            return True
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error adding response: {e}")
            return False
    
    def remove_response(self, response_id):
        """
        Remove a response from the responses file.
        
        Args:
            response_id (str): ID of the response to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load current responses
            with open(self.responses_file, 'r') as f:
                responses_data = json.load(f)
            
            # Find and remove the response
            initial_count = len(responses_data.get('responses', []))
            responses_data['responses'] = [r for r in responses_data.get('responses', []) if r.get('id') != response_id]
            
            if len(responses_data.get('responses', [])) == initial_count:
                print(f"Response with ID '{response_id}' not found.")
                return False
            
            # Save updated responses
            with open(self.responses_file, 'w') as f:
                json.dump(responses_data, f, indent=2)
                
            print(f"Response with ID '{response_id}' removed successfully.")
            return True
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error removing response: {e}")
            return False
    
    def create_sample_data(self, num_responses=100):
        """
        Create sample questions and responses for testing.
        
        Args:
            num_responses (int): Number of sample responses to generate
            
        Returns:
            bool: True if successful, False otherwise
        """
        import random
        from datetime import timedelta
        
        try:
            # Create sample questions
            questions_data = {
                "survey_id": "survey_123",
                "title": "Customer Satisfaction Survey",
                "description": "Help us improve our services by providing your feedback",
                "created_at": datetime.now().strftime("%Y-%m-%d"),
                "questions": [
                    {
                        "id": "satisfaction",
                        "text": "How satisfied are you with our product?",
                        "type": "rating",
                        "scale": 5
                    },
                    {
                        "id": "recommendation",
                        "text": "How likely are you to recommend our product to others?",
                        "type": "rating",
                        "scale": 10
                    },
                    {
                        "id": "ease_of_use",
                        "text": "How easy was it to use our product?",
                        "type": "rating",
                        "scale": 5
                    },
                    {
                        "id": "features",
                        "text": "Which features do you use most often?",
                        "type": "multiple_choice",
                        "options": ["Dashboard", "Reports", "Analytics", "Customization", "Integration"]
                    },
                    {
                        "id": "improvement",
                        "text": "What area needs the most improvement?",
                        "type": "multiple_choice",
                        "options": ["UI/UX", "Performance", "Features", "Support", "Documentation"]
                    }
                ]
            }
            
            # Save questions
            with open(self.questions_file, 'w') as f:
                json.dump(questions_data, f, indent=2)
            
            # Create sample responses
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            responses = []
            for i in range(num_responses):
                response_date = start_date + timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
                
                response = {
                    "id": f"resp_{i+1}",
                    "submitted_at": response_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "user_type": random.choice(["Free", "Basic", "Premium", "Enterprise"]),
                    "completion_time": random.randint(60, 600),
                    "answers": {
                        "satisfaction": random.randint(1, 5),
                        "recommendation": random.randint(0, 10),
                        "ease_of_use": random.randint(1, 5),
                        "features": random.choice(["Dashboard", "Reports", "Analytics", "Customization", "Integration"]),
                        "improvement": random.choice(["UI/UX", "Performance", "Features", "Support", "Documentation"])
                    }
                }
                
                # Add age_group to some responses to simulate optional fields
                if random.random() > 0.2:  # 80% of responses have age_group
                    response["age_group"] = random.choice(["18-24", "25-34", "35-44", "45-54", "55+"])
                
                responses.append(response)
            
            responses_data = {
                "survey_id": "survey_123",
                "responses": responses
            }
            
            # Save responses
            with open(self.responses_file, 'w') as f:
                json.dump(responses_data, f, indent=2)
            
            print(f"Created sample data with {len(questions_data['questions'])} questions and {len(responses)} responses.")
            return True
            
        except Exception as e:
            print(f"Error creating sample data: {e}")
            return False


# Example usage
if __name__ == "__main__":
    loader = SurveyJSONLoader()
    
    # Create sample data
    loader.create_sample_data()
    
    # Load survey data
    survey_data = loader.load_survey_data()
    
    if survey_data:
        print("\nSuccessfully loaded survey data:")
        print(f"Survey title: {survey_data['metadata']['survey_title']}")
        print(f"Number of responses: {len(survey_data['data'])}")
        print(f"Number of questions: {len(survey_data['metadata']['questions'])}")
        
        # Preview the data
        if not survey_data['data'].empty:
            print("\nData preview:")
            print(survey_data['data'].head())
    
    # Example of adding a new question
    print("\nAdding a new question...")
    loader.add_question(
        question_id="feedback",
        question_text="Do you have any additional feedback for us?",
        question_type="text"
    )
    
    # Example of updating a question
    print("\nUpdating a question...")
    loader.update_question(
        question_id="satisfaction",
        question_text="How would you rate your overall satisfaction with our product?"
    )
    
    # Example of adding a new response
    print("\nAdding a new response...")
    new_response = {
        "id": "custom_response_1",
        "user_type": "Premium",
        "completion_time": 120,
        "answers": {
            "satisfaction": 5,
            "recommendation": 9,
            "ease_of_use": 4,
            "features": "Analytics",
            "improvement": "Performance",
            "feedback": "Great product overall, but could use some performance improvements."
        },
        "age_group": "25-34"
    }
    loader.add_response(new_response)