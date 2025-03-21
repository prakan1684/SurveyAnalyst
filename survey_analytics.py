import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import random
import os


class SurveyAnalytics:
    def __init__(self, data_directory="survey_data"):
        """
        Initialize the SurveyAnalytics class.
        
        Args:
            data_directory (str): Directory containing the survey data JSON files
        """
        self.data_directory = data_directory
        self.survey_data = self._load_survey_data()
        
    def _load_survey_data(self):
        """
        Load survey data from JSON files.
        
        Returns:
            dict: Survey data with DataFrame and metadata
        """
        try:
            from json_data_loader import SurveyJSONLoader
            loader = SurveyJSONLoader(self.data_directory)
            survey_data = loader.load_survey_data()
            
            if survey_data:
                print(f"Loaded survey data from JSON files in '{self.data_directory}'")
                return survey_data
            
            # If no data found, create empty data structure
            return {
                "data": pd.DataFrame(),
                "metadata": {
                    "survey_id": "UNKNOWN",
                    "survey_title": "No Survey Data",
                    "survey_description": "",
                    "created_at": "",
                    "questions": {}
                }
            }
        except Exception as e:
            print(f"Error loading data from JSON: {e}")
            # Return empty data structure on error
            return {
                "data": pd.DataFrame(),
                "metadata": {
                    "survey_id": "ERROR",
                    "survey_title": "Error Loading Survey Data",
                    "survey_description": str(e),
                    "created_at": "",
                    "questions": {}
                }
            }

    def get_basic_stats(self):
        """
        Calculate basic statistics from the survey data.
        
        Returns:
            dict: Dictionary containing basic statistics
        """
        df = self.survey_data["data"]
        stats = {
            "total_responses": len(df),
            "avg_completion_time": 0,
            "question_count": len(self.survey_data["metadata"]["questions"])
        }
        
        if not df.empty:
            # Calculate average completion time if 'completion_time' column exists
            if 'completion_time' in df.columns:
                stats["avg_completion_time"] = df["completion_time"].mean()
                
            # Get column types
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            # Add counts of different question types
            stats["numeric_questions"] = len(numeric_columns)
            stats["categorical_questions"] = len(categorical_columns)
        
        return stats
        
    def get_questions_summary(self):
        """
        Get a summary of the survey questions.
        
        Returns:
            dict: Dictionary with question IDs and text
        """
        return self.survey_data["metadata"]["questions"]
    
    def get_data_for_question(self, question_id):
        """
        Get data for a specific question.
        
        Args:
            question_id (str): The column name/ID of the question
            
        Returns:
            pandas.Series: Data for the specified question
        """
        df = self.survey_data["data"]
        
        if df.empty or question_id not in df.columns:
            return pd.Series()
            
        return df[question_id]
    
    def get_response_counts(self):
        """
        Get counts of responses by user type.
        
        Returns:
            dict: Dictionary with user types and counts
        """
        df = self.survey_data["data"]
        if df.empty or 'user_type' not in df.columns:
            return {}
        
        return df['user_type'].value_counts().to_dict()
    
    def get_survey_metadata(self):
        """
        Get the survey metadata.
        
        Returns:
            dict: Survey metadata
        """
        return self.survey_data["metadata"]
    
    def plot_satisfaction_distribution(self):
        """
        Plots the satisfaction distribution graph.

        Returns:
            matplotlib.figure.Figure: The satisfaction distribution graph.
        """
        df = self.survey_data['data']
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plotting the histogram
        sns.histplot(data=df, x="satisfaction", kde=True, bins=5, ax=ax)
        ax.set_xlabel("Satisfaction (1-5)")
        ax.set_ylabel("number of responses")
        ax.set_title("Satisfaction Distribution")
        return fig
    
    def plot_recommendation_distribution(self):
        """
        Plots the recommendation distribution graph.

        Returns:
            matplotlib.figure.Figure: The recommendation distribution graph.
        """ 
        df = self.survey_data['data']
        fig, ax = plt.subplots(figsize=(12, 6))

        # Plotting the histogram
        sns.histplot(data=df, x="recommendation", kde=False, bins=11, ax=ax)
        
        #coloring bars accoring to NPS categories
        for i, p in enumerate(ax.patches):
            if i <= 6: #detractors (0-6)
                p.set_facecolor('red')
            elif i <= 8: #passives (7-8)
                p.set_facecolor('yellow')
            else: #promoters (9-10)
                p.set_facecolor('green')
            
        ax.set_title("Net promoter score distribution")
        ax.set_xlabel("Recommendation score (0-10)")
        ax.set_ylabel("number of responses")


        # Add NPS category labels
        ax.axvline(x=6.5, color='black', linestyle='--', alpha=0.7)
        ax.axvline(x=8.5, color='black', linestyle='--', alpha=0.7)
        ax.text(3, ax.get_ylim()[1]*0.9, "Detractors", ha='center')
        ax.text(7.5, ax.get_ylim()[1]*0.9, "Passives", ha='center')
        ax.text(9.5, ax.get_ylim()[1]*0.9, "Promoters", ha='center')
        
        return fig
    
    def plot_responses_over_time(self):
        """
        Creates a line plot showing survey responses over time.
        
        Returns:
            matplotlib.figure.Figure: The figure containing the plot
        """
        df = self.survey_data['data']
        
        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # Group by date and count responses
        daily_responses = df.groupby(df["timestamp"].dt.date).size()
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(daily_responses.index, daily_responses.values, marker='o')
        
        ax.set_title("Survey Responses Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Number of Responses")
        ax.grid(True, alpha=0.3)
        
        return fig

    def plot_improvement_areas(self):
        """
        Creates a bar plot showing the improvement areas.
        
        Returns:
            matplotlib.figure.Figure: The figure containing the plot
        """
        df = self.survey_data['data']
        fig, ax = plt.subplots(figsize=(12, 6))
        improvement_counts = df["improvement"].value_counts()

        ax.pie(improvement_counts, labels=improvement_counts.index, autopct='%1.1f%%', shadow=True)
        ax.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle
        ax.set_title("Improvement Areas")
        return fig


    def plot_user_type_distribution(self):
        """
        Creates a bar plot showing the user type distribution.
        
        Returns:
            matplotlib.figure.Figure: The figure containing the plot
        """
        df = self.survey_data['data']
        fig, ax = plt.subplots(figsize=(12, 6))
        user_type_counts = df["user_type"].value_counts()
        sns.barplot(x=user_type_counts.index, y=user_type_counts.values, ax=ax)
        total = user_type_counts.sum()
        for i, p in enumerate(ax.patches):
            percentage= f'{100 * p.get_height() / total:.1f}%'
            ax.annotate(percentage, (p.get_x() + p.get_width() / 2., p.get_height()),
                        ha='center', va='center', fontsize=10, color='black', xytext=(0, 5),
                        textcoords='offset points')

        ax.set_title("User Type Distribution")
        ax.set_xlabel("User Type")
        ax.set_ylabel("Number of Responses")
        return fig

    def plot_feature_usage(self):
        """
        Creates a plot showing the distribution of feature usage.
        
        Returns:
            matplotlib.figure.Figure: The figure containing the plot
        """
        df = self.survey_data['data']
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Count feature usage
        feature_counts = df["features"].value_counts()
        
        # Create bar plot
        sns.barplot(x=feature_counts.index, y=feature_counts.values, ax=ax)
        
        ax.set_title("Most Used Features")
        ax.set_xlabel("Feature")
        ax.set_ylabel("Number of Users")
        plt.xticks(rotation=45)
        
        return fig