#!/usr/bin/env python3
# survey_manager.py

import argparse
import json
import os
import sys
from json_data_loader import SurveyJSONLoader

def setup_parser():
    """Set up command line argument parser"""
    parser = argparse.ArgumentParser(description='Survey Data Management Utility')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List questions command
    list_questions_parser = subparsers.add_parser('list-questions', help='List all survey questions')
    list_questions_parser.add_argument('--dir', default='survey_data', help='Survey data directory')
    
    # List responses command
    list_responses_parser = subparsers.add_parser('list-responses', help='List all survey responses')
    list_responses_parser.add_argument('--dir', default='survey_data', help='Survey data directory')
    list_responses_parser.add_argument('--limit', type=int, default=5, help='Limit number of responses shown')
    
    # Add question command
    add_question_parser = subparsers.add_parser('add-question', help='Add a new survey question')
    add_question_parser.add_argument('--dir', default='survey_data', help='Survey data directory')
    add_question_parser.add_argument('--id', required=True, help='Question ID')
    add_question_parser.add_argument('--text', required=True, help='Question text')
    add_question_parser.add_argument('--type', default='text', choices=['text', 'multiple_choice', 'rating'], 
                                    help='Question type')
    add_question_parser.add_argument('--options', nargs='+', help='Options for multiple choice questions')
    add_question_parser.add_argument('--scale', type=int, help='Scale for rating questions')
    
    # Update question command
    update_question_parser = subparsers.add_parser('update-question', help='Update an existing question')
    update_question_parser.add_argument('--dir', default='survey_data', help='Survey data directory')
    update_question_parser.add_argument('--id', required=True, help='Question ID to update')
    update_question_parser.add_argument('--text', help='New question text')
    update_question_parser.add_argument('--type', choices=['text', 'multiple_choice', 'rating'], 
                                       help='New question type')
    update_question_parser.add_argument('--options', nargs='+', help='New options for multiple choice questions')
    update_question_parser.add_argument('--scale', type=int, help='New scale for rating questions')
    
    # Remove question command
    remove_question_parser = subparsers.add_parser('remove-question', help='Remove a question')
    remove_question_parser.add_argument('--dir', default='survey_data', help='Survey data directory')
    remove_question_parser.add_argument('--id', required=True, help='Question ID to remove')
    
    # Add response command
    add_response_parser = subparsers.add_parser('add-response', help='Add a new survey response')
    add_response_parser.add_argument('--dir', default='survey_data', help='Survey data directory')
    add_response_parser.add_argument('--file', help='JSON file containing the response data')
    add_response_parser.add_argument('--interactive', action='store_true', help='Add response interactively')
    
    # Remove response command
    remove_response_parser = subparsers.add_parser('remove-response', help='Remove a response')
    remove_response_parser.add_argument('--dir', default='survey_data', help='Survey data directory')
    remove_response_parser.add_argument('--id', required=True, help='Response ID to remove')
    
    # Create sample data command
    create_sample_parser = subparsers.add_parser('create-sample', help='Create sample survey data')
    create_sample_parser.add_argument('--dir', default='survey_data', help='Survey data directory')
    create_sample_parser.add_argument('--responses', type=int, default=100, 
                                     help='Number of sample responses to generate')
    
    return parser

def list_questions(args):
    """List all survey questions"""
    loader = SurveyJSONLoader(args.dir)
    questions = loader.get_questions()
    
    if not questions:
        print(f"No questions found in {args.dir}")
        return
    
    print(f"\nFound {len(questions)} questions:\n")
    for i, q in enumerate(questions, 1):
        print(f"{i}. ID: {q.get('id', 'N/A')}")
        print(f"   Text: {q.get('text', 'N/A')}")
        print(f"   Type: {q.get('type', 'N/A')}")
        
        if 'options' in q:
            print(f"   Options: {', '.join(q['options'])}")
        
        if 'scale' in q:
            print(f"   Scale: 1-{q['scale']}")
        
        print()

def list_responses(args):
    """List survey responses"""
    loader = SurveyJSONLoader(args.dir)
    responses = loader.get_responses()
    
    if not responses:
        print(f"No responses found in {args.dir}")
        return
    
    limit = min(args.limit, len(responses))
    print(f"\nShowing {limit} of {len(responses)} responses:\n")
    
    for i, resp in enumerate(responses[:limit], 1):
        print(f"{i}. ID: {resp.get('id', 'N/A')}")
        print(f"   Submitted: {resp.get('submitted_at', 'N/A')}")
        print(f"   User Type: {resp.get('user_type', 'N/A')}")
        
        if 'answers' in resp:
            print("   Answers:")
            for q_id, answer in resp['answers'].items():
                print(f"     {q_id}: {answer}")
        
        print()

def add_question(args):
    """Add a new survey question"""
    loader = SurveyJSONLoader(args.dir)
    result = loader.add_question(
        question_id=args.id,
        question_text=args.text,
        question_type=args.type,
        options=args.options,
        scale=args.scale
    )
    
    if result:
        print(f"Question '{args.id}' added successfully.")
    else:
        print(f"Failed to add question '{args.id}'.")

def update_question(args):
    """Update an existing question"""
    loader = SurveyJSONLoader(args.dir)
    result = loader.update_question(
        question_id=args.id,
        question_text=args.text,
        question_type=args.type,
        options=args.options,
        scale=args.scale
    )
    
    if result:
        print(f"Question '{args.id}' updated successfully.")
    else:
        print(f"Failed to update question '{args.id}'.")

def remove_question(args):
    """Remove a question"""
    loader = SurveyJSONLoader(args.dir)
    result = loader.remove_question(args.id)
    
    if result:
        print(f"Question '{args.id}' removed successfully.")
    else:
        print(f"Failed to remove question '{args.id}'.")

def add_response_interactive(loader):
    """Add a response interactively"""
    questions = loader.get_questions()
    if not questions:
        print("No questions found. Please add questions first.")
        return False
    
    response = {
        "id": input("Response ID (leave blank for auto-generated): ").strip() or None,
        "user_type": input("User Type (Free/Basic/Premium/Enterprise): ").strip() or "Unknown",
        "completion_time": int(input("Completion Time (seconds): ").strip() or "0"),
        "answers": {}
    }
    
    print("\nAnswering questions:")
    for q in questions:
        q_id = q.get('id')
        q_text = q.get('text')
        q_type = q.get('type', 'text')
        
        print(f"\n{q_text} (ID: {q_id}, Type: {q_type})")
        
        if q_type == 'multiple_choice' and 'options' in q:
            print("Options: " + ", ".join(q['options']))
            answer = input("Answer: ").strip()
        elif q_type == 'rating' and 'scale' in q:
            print(f"Rating (1-{q['scale']})")
            answer = input("Answer: ").strip()
            try:
                answer = int(answer)
            except ValueError:
                print(f"Invalid rating. Using 1 as default.")
                answer = 1
        else:
            answer = input("Answer: ").strip()
        
        response['answers'][q_id] = answer
    
    # Optional fields
    age_group = input("\nAge Group (18-24, 25-34, 35-44, 45-54, 55+) [optional]: ").strip()
    if age_group:
        response["age_group"] = age_group
    
    return loader.add_response(response)

def add_response(args):
    """Add a new survey response"""
    loader = SurveyJSONLoader(args.dir)
    
    if args.interactive:
        result = add_response_interactive(loader)
        if result:
            print("Response added successfully.")
        else:
            print("Failed to add response.")
        return
    
    if args.file:
        try:
            with open(args.file, 'r') as f:
                response_data = json.load(f)
            
            result = loader.add_response(response_data)
            if result:
                print(f"Response added successfully from file {args.file}.")
            else:
                print(f"Failed to add response from file {args.file}.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading response file: {e}")
    else:
        print("Please specify either --file or --interactive")

def remove_response(args):
    """Remove a response"""
    loader = SurveyJSONLoader(args.dir)
    result = loader.remove_response(args.id)
    
    if result:
        print(f"Response '{args.id}' removed successfully.")
    else:
        print(f"Failed to remove response '{args.id}'.")

def create_sample_data(args):
    """Create sample survey data"""
    loader = SurveyJSONLoader(args.dir)
    result = loader.create_sample_data(args.responses)
    
    if result:
        print(f"Created sample data with {args.responses} responses in {args.dir}.")
    else:
        print(f"Failed to create sample data.")

def main():
    parser = setup_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create the data directory if it doesn't exist
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
    
    # Execute the appropriate command
    if args.command == 'list-questions':
        list_questions(args)
    elif args.command == 'list-responses':
        list_responses(args)
    elif args.command == 'add-question':
        add_question(args)
    elif args.command == 'update-question':
        update_question(args)
    elif args.command == 'remove-question':
        remove_question(args)
    elif args.command == 'add-response':
        add_response(args)
    elif args.command == 'remove-response':
        remove_response(args)
    elif args.command == 'create-sample':
        create_sample_data(args)

if __name__ == "__main__":
    main()