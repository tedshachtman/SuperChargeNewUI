#!/usr/bin/env python3

import boto3
import zipfile
import os
import json

def create_lambda_zip(function_name, source_file):
    """Create a zip file for the Lambda function"""
    zip_filename = f"{function_name}.zip"
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(source_file, os.path.basename(source_file))
    
    return zip_filename

def deploy_lambda_function(lambda_client, function_name, zip_file, handler, description, timeout=30):
    """Deploy or update a Lambda function"""
    
    with open(zip_file, 'rb') as zip_data:
        zip_content = zip_data.read()
    
    try:
        # Try to update existing function
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        print(f"✅ Updated existing function: {function_name}")
        
        # Update timeout if needed
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Timeout=timeout
        )
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        # Extract the actual Python file name for handler
        source_file_name = os.path.splitext(os.path.basename(zip_file.replace('.zip', '.py')))[0]
        
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.9',
            Role='arn:aws:iam::696944065143:role/lambda-execution-role',
            Handler=handler,
            Code={'ZipFile': zip_content},
            Description=description,
            Timeout=timeout,
            Environment={
                'Variables': {
                    'GEMINI_API_KEY': os.environ.get('GEMINI_API_KEY', 'your-gemini-api-key-here')
                }
            }
        )
        print(f"✅ Created new function: {function_name}")
    
    return response

def main():
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Room management functions to deploy
    functions = [
        {
            'name': 'supercharged-create-room',
            'source': 'lambda_functions/create_room.py',
            'handler': 'create_room.lambda_handler',
            'description': 'Create new custom rooms for friends',
            'timeout': 60
        },
        {
            'name': 'supercharged-join-room',
            'source': 'lambda_functions/join_room.py',
            'handler': 'join_room.lambda_handler',
            'description': 'Join existing rooms with game code',
            'timeout': 30
        },
        {
            'name': 'supercharged-list-user-rooms',
            'source': 'lambda_functions/list_user_rooms.py',
            'handler': 'list_user_rooms.lambda_handler',
            'description': 'List rooms user is a member of',
            'timeout': 30
        },
        {
            'name': 'supercharged-generate-room-ai-ideas',
            'source': 'lambda_functions/generate_room_ai_ideas.py',
            'handler': 'generate_room_ai_ideas.lambda_handler',
            'description': 'Generate AI baseline ideas for room superpowers',
            'timeout': 300
        }
    ]
    
    print("🚀 Deploying room management Lambda functions...")
    
    for func in functions:
        print(f"\n📦 Processing {func['name']}...")
        
        # Create zip file
        zip_file = create_lambda_zip(func['name'], func['source'])
        
        try:
            # Deploy function
            response = deploy_lambda_function(
                lambda_client,
                func['name'],
                zip_file,
                func['handler'],
                func['description'],
                func['timeout']
            )
            
        except Exception as e:
            print(f"❌ Error deploying {func['name']}: {str(e)}")
        
        finally:
            # Cleanup zip file
            if os.path.exists(zip_file):
                os.remove(zip_file)
    
    print(f"\n✅ Room Lambda deployment complete!")

if __name__ == "__main__":
    main()