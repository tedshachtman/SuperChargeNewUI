#!/usr/bin/env python3

import boto3
import zipfile
import os
import json
import time
import tempfile
import subprocess
import shutil

def create_lambda_package_with_dependencies(function_file, requirements_file=None):
    """Create a Lambda deployment package with dependencies"""
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = os.path.join(temp_dir, 'package')
        os.makedirs(package_dir)
        
        # Install dependencies if requirements file exists
        if requirements_file and os.path.exists(requirements_file):
            print(f"Installing dependencies from {requirements_file}...")
            subprocess.run([
                'pip', 'install', '-r', requirements_file, 
                '--target', package_dir
            ], check=True)
        
        # Copy function file as lambda_function.py
        shutil.copy(function_file, os.path.join(package_dir, 'lambda_function.py'))
        
        # Create zip file
        zip_path = os.path.join(temp_dir, 'deployment-package.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, package_dir)
                    zip_file.write(file_path, arcname)
        
        # Read the zip content
        with open(zip_path, 'rb') as zip_file:
            return zip_file.read()

def deploy_gemini_lambda():
    """Deploy the Gemini AI idea generation Lambda function"""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    function_name = 'supercharged-generate-ai-ideas'
    
    print("Creating deployment package for Gemini Lambda function...")
    
    # Create deployment package with dependencies
    zip_content = create_lambda_package_with_dependencies(
        'lambda_functions/generate_ai_ideas_simple.py',
        'requirements_simple.txt'
    )
    
    print(f"Package size: {len(zip_content) / 1024 / 1024:.2f} MB")
    
    try:
        # Try to update existing function
        print(f"Updating existing function: {function_name}")
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        # Skip configuration update if there's a conflict
        try:
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Timeout=300,  # 5 minutes for Gemini API calls
                MemorySize=512  # More memory for processing
            )
        except Exception as e:
            print(f"Configuration update skipped: {e}")
            pass
        
        print(f"Updated existing function: {function_name}")
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Function doesn't exist, create it
        print(f"Creating new function: {function_name}")
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.9',
            Role='arn:aws:iam::696944065143:role/lambda-execution-role',
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_content},
            Description='Generate AI ideas using Gemini 2.5 Pro for SuperCharge superpowers',
            Timeout=300,  # 5 minutes
            MemorySize=512,
            Environment={
                'Variables': {
                    'GEMINI_API_KEY': 'AIzaSyBhCFFPFv_qhhnkKp1GfM2MJ_bM1ZeISpg'
                }
            }
        )
        print(f"Created new function: {function_name}")
    
    return response

if __name__ == '__main__':
    try:
        result = deploy_gemini_lambda()
        print("Gemini Lambda deployment completed successfully!")
        print(f"Function ARN: {result['FunctionArn']}")
    except Exception as e:
        print(f"Error deploying Gemini Lambda: {str(e)}")
        exit(1)