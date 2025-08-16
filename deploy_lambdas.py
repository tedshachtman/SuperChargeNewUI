#!/usr/bin/env python3

import boto3
import zipfile
import os
import json
import time

# Lambda function configurations
LAMBDA_FUNCTIONS = [
    {
        'name': 'supercharged-get-daily-superpower',
        'file': 'get_daily_superpower.py',
        'description': 'Get the current day\'s superpower challenge'
    },
    {
        'name': 'supercharged-submit-ideas',
        'file': 'submit_ideas.py',
        'description': 'Submit user ideas for daily challenge'
    },
    {
        'name': 'supercharged-get-rating-pairs',
        'file': 'get_rating_pairs.py',
        'description': 'Get pairs of submissions for rating'
    },
    {
        'name': 'supercharged-submit-rating',
        'file': 'submit_rating.py',
        'description': 'Submit similarity rating for idea pairs'
    },
    {
        'name': 'supercharged-admin-add-superpower',
        'file': 'admin_add_superpower.py',
        'description': 'Admin function to add new superpowers'
    },
    {
        'name': 'supercharged-get-leaderboard',
        'file': 'get_leaderboard.py',
        'description': 'Get leaderboard and results for a specific date'
    },
    {
        'name': 'supercharged-admin-list-superpowers',
        'file': 'admin_list_superpowers.py',
        'description': 'List all superpowers for admin interface'
    },
    {
        'name': 'supercharged-admin-list-submissions',
        'file': 'admin_list_submissions.py',
        'description': 'List all submissions for admin interface'
    }
]

def create_lambda_zip(file_path, zip_path):
    """Create a zip file for Lambda deployment"""
    with zipfile.ZipFile(zip_path, 'w') as zip_file:
        zip_file.write(file_path, 'lambda_function.py')
    return zip_path

def deploy_lambda_function(lambda_client, function_config):
    """Deploy a single Lambda function"""
    function_name = function_config['name']
    file_name = function_config['file']
    description = function_config['description']
    
    # Get script directory to ensure correct paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'lambda_functions', file_name)
    zip_path = f'/tmp/{function_name}.zip'
    
    print(f"Deploying {function_name}...")
    
    # Create zip file
    create_lambda_zip(file_path, zip_path)
    
    # Read zip file
    with open(zip_path, 'rb') as zip_file:
        zip_content = zip_file.read()
    
    try:
        # Try to update existing function
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        print(f"Updated existing function: {function_name}")
    except lambda_client.exceptions.ResourceNotFoundException:
        # Function doesn't exist, create it
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.9',
            Role='arn:aws:iam::696944065143:role/lambda-execution-role',
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_content},
            Description=description,
            Timeout=30,
            MemorySize=128
        )
        print(f"Created new function: {function_name}")
    
    # Clean up zip file
    os.remove(zip_path)
    
    return response

def main():
    """Deploy all Lambda functions"""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    print("Starting Lambda deployment...")
    
    for function_config in LAMBDA_FUNCTIONS:
        try:
            deploy_lambda_function(lambda_client, function_config)
            time.sleep(1)  # Small delay between deployments
        except Exception as e:
            print(f"Error deploying {function_config['name']}: {str(e)}")
    
    print("Lambda deployment completed!")

if __name__ == '__main__':
    main()