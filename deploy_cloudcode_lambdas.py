#!/usr/bin/env python3

import boto3
import zipfile
import os
import json

def create_cloudcode_lambda_zip(function_name, source_file):
    """Create a zip file for CloudCode Lambda function with core module"""
    zip_filename = f"{function_name}.zip"
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add the main Lambda function
        zipf.write(source_file, os.path.basename(source_file))
        
        # Add the core module (place it in the root for easy import)
        zipf.write('cloudcode_core_lambda.py', 'cloudcode_core_lambda.py')
    
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
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.9',
            Role='arn:aws:iam::696944065143:role/lambda-execution-role',
            Handler=handler,
            Code={'ZipFile': zip_content},
            Description=description,
            Timeout=timeout,
            MemorySize=256  # More memory for embedding computations
        )
        print(f"✅ Created new function: {function_name}")
    
    return response

def main():
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # CloudCode Lambda functions to deploy
    functions = [
        {
            'name': 'cloudcode-next-pair',
            'source': 'lambda_functions/cloudcode_next_pair.py',
            'handler': 'cloudcode_next_pair.lambda_handler',
            'description': 'Get next idea pair for rating (Cloud Code)',
            'timeout': 30
        },
        {
            'name': 'cloudcode-submit-rating',
            'source': 'lambda_functions/cloudcode_submit_rating.py',
            'handler': 'cloudcode_submit_rating.lambda_handler',
            'description': 'Submit rating and get next pair (Cloud Code)',
            'timeout': 30
        }
    ]
    
    print("🚀 Deploying CloudCode Lambda functions...")
    
    for func in functions:
        print(f"\n📦 Processing {func['name']}...")
        
        # Create zip file with core module
        zip_file = create_cloudcode_lambda_zip(func['name'], func['source'])
        
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
    
    print(f"\n✅ CloudCode Lambda deployment complete!")

if __name__ == "__main__":
    main()