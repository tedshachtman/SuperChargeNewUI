#!/usr/bin/env python3

import boto3
import time

# API Gateway configuration
API_ID = "gsx73a1w3d"
ROOT_RESOURCE_ID = "xkr2voy6ak"
REGION = "us-east-1"
ACCOUNT_ID = "696944065143"

# Initialize AWS clients
apigateway = boto3.client('apigateway', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)

def create_resource(parent_id, path_part):
    """Create a resource in API Gateway"""
    try:
        response = apigateway.create_resource(
            restApiId=API_ID,
            parentId=parent_id,
            pathPart=path_part
        )
        return response['id']
    except apigateway.exceptions.ConflictException:
        # Resource already exists, get its ID
        response = apigateway.get_resources(restApiId=API_ID)
        for resource in response['items']:
            if resource.get('pathPart') == path_part and resource['parentId'] == parent_id:
                return resource['id']
        raise

def create_method(resource_id, http_method):
    """Create a method for a resource"""
    try:
        apigateway.put_method(
            restApiId=API_ID,
            resourceId=resource_id,
            httpMethod=http_method,
            authorizationType='NONE'
        )
    except apigateway.exceptions.ConflictException:
        print(f"Method {http_method} already exists for resource {resource_id}")

def create_integration(resource_id, http_method, lambda_function_name):
    """Create Lambda integration for a method"""
    lambda_uri = f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:{lambda_function_name}/invocations"
    
    try:
        apigateway.put_integration(
            restApiId=API_ID,
            resourceId=resource_id,
            httpMethod=http_method,
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=lambda_uri
        )
    except apigateway.exceptions.ConflictException:
        print(f"Integration already exists for {http_method} on resource {resource_id}")
    
    # Add permission for API Gateway to invoke Lambda
    try:
        lambda_client.add_permission(
            FunctionName=lambda_function_name,
            StatementId=f'apigateway-invoke-{lambda_function_name}',
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=f'arn:aws:execute-api:{REGION}:{ACCOUNT_ID}:{API_ID}/*/*'
        )
    except Exception as e:
        print(f"Permission might already exist for {lambda_function_name}: {e}")

def setup_cors(resource_id):
    """Setup CORS for a resource"""
    try:
        # Create OPTIONS method for CORS
        apigateway.put_method(
            restApiId=API_ID,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            authorizationType='NONE'
        )
        
        # Create mock integration for OPTIONS
        apigateway.put_integration(
            restApiId=API_ID,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            type='MOCK',
            requestTemplates={
                'application/json': '{"statusCode": 200}'
            }
        )
        
        # Create method response for OPTIONS
        apigateway.put_method_response(
            restApiId=API_ID,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': False,
                'method.response.header.Access-Control-Allow-Methods': False,
                'method.response.header.Access-Control-Allow-Origin': False
            }
        )
        
        # Create integration response for OPTIONS
        apigateway.put_integration_response(
            restApiId=API_ID,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                'method.response.header.Access-Control-Allow-Methods': "'GET,POST,OPTIONS'",
                'method.response.header.Access-Control-Allow-Origin': "'*'"
            }
        )
    except apigateway.exceptions.ConflictException:
        print(f"CORS already configured for resource {resource_id}")

def main():
    """Setup the Gemini AI endpoint"""
    print("Setting up Gemini AI endpoint...")
    
    try:
        # Find the admin resource
        response = apigateway.get_resources(restApiId=API_ID)
        admin_resource_id = None
        
        for resource in response['items']:
            if resource.get('pathPart') == 'admin':
                admin_resource_id = resource['id']
                break
        
        if not admin_resource_id:
            print("Admin resource not found, creating it...")
            admin_resource_id = create_resource(ROOT_RESOURCE_ID, 'admin')
        
        # Create generate-ideas sub-resource
        generate_ideas_resource = create_resource(admin_resource_id, 'generate-ideas')
        
        # Setup the endpoint
        print("Creating method and integration for generate-ideas endpoint...")
        create_method(generate_ideas_resource, 'POST')
        create_integration(generate_ideas_resource, 'POST', 'supercharged-generate-ai-ideas')
        setup_cors(generate_ideas_resource)
        
        # Deploy the API
        print("Deploying API...")
        apigateway.create_deployment(
            restApiId=API_ID,
            stageName='prod',
            description='Added Gemini AI idea generation endpoint'
        )
        
        print(f"""
Gemini AI endpoint setup complete!

New endpoint:
POST /admin/generate-ideas - Generate AI ideas for a superpower

Full URL: https://{API_ID}.execute-api.{REGION}.amazonaws.com/prod/admin/generate-ideas

Example usage:
POST https://{API_ID}.execute-api.{REGION}.amazonaws.com/prod/admin/generate-ideas
{{
    "superpowerId": "uuid-string",
    "superpowerTitle": "Perfect Memory", 
    "superpowerDescription": "You have the ability to...",
    "date": "2025-08-16"
}}
""")
        
    except Exception as e:
        print(f"Error setting up Gemini API: {str(e)}")
        raise

if __name__ == '__main__':
    main()