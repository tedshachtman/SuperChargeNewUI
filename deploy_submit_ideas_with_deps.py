#!/usr/bin/env python3

import boto3
import zipfile
import os
import subprocess
import tempfile
import shutil

def deploy_submit_ideas_with_requests():
    """Deploy submit_ideas Lambda with requests dependency"""
    
    # Create temporary directory for package
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📦 Creating package in {temp_dir}")
        
        # Copy the Lambda function
        source_file = 'lambda_functions/submit_ideas.py'
        dest_file = os.path.join(temp_dir, 'lambda_function.py')  # Lambda expects this name
        shutil.copy2(source_file, dest_file)
        
        # Install requests to the temp directory
        print("📥 Installing requests library...")
        subprocess.run([
            'pip', 'install', 'requests', 
            '--target', temp_dir,
            '--quiet'
        ], check=True)
        
        # Create zip file
        zip_path = 'submit_ideas_with_deps.zip'
        print(f"🗜️ Creating zip file: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arc_name)
        
        # Deploy to Lambda
        print("🚀 Deploying to Lambda...")
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        with open(zip_path, 'rb') as zip_file:
            zip_content = zip_file.read()
        
        try:
            # Update the function code
            response = lambda_client.update_function_code(
                FunctionName='supercharged-submit-ideas',
                ZipFile=zip_content
            )
            print("✅ Successfully updated supercharged-submit-ideas with requests library")
            
            # Also update environment variables to make sure API key is set
            lambda_client.update_function_configuration(
                FunctionName='supercharged-submit-ideas',
                Environment={
                    'Variables': {
                        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY', 'your-openai-api-key-here')
                    }
                }
            )
            print("✅ Updated environment variables")
            
        except Exception as e:
            print(f"❌ Error deploying: {str(e)}")
        
        finally:
            # Cleanup
            if os.path.exists(zip_path):
                os.remove(zip_path)

if __name__ == "__main__":
    deploy_submit_ideas_with_requests()