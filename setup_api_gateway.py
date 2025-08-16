#!/usr/bin/env python3

import boto3
import json
import time

# API Gateway and Lambda configuration
API_ID = "gsx73a1w3d"
ROOT_RESOURCE_ID = "xkr2voy6ak"
REGION = "us-east-1"
ACCOUNT_ID = "696944065143"

# Initialize AWS clients
apigateway = boto3.client('apigateway', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)

def create_resource(parent_id, path_part):
    """Create a resource in API Gateway"""
    response = apigateway.create_resource(
        restApiId=API_ID,
        parentId=parent_id,
        pathPart=path_part
    )
    return response['id']

def create_method(resource_id, http_method):
    """Create a method for a resource"""
    apigateway.put_method(
        restApiId=API_ID,
        resourceId=resource_id,
        httpMethod=http_method,
        authorizationType='NONE'
    )

def create_integration(resource_id, http_method, lambda_function_name):
    """Create Lambda integration for a method"""
    lambda_uri = f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:{lambda_function_name}/invocations"
    
    apigateway.put_integration(
        restApiId=API_ID,
        resourceId=resource_id,
        httpMethod=http_method,
        type='AWS_PROXY',
        integrationHttpMethod='POST',
        uri=lambda_uri
    )
    
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

def main():
    """Setup the complete API Gateway structure"""
    print("Setting up API Gateway resources and methods...")
    
    # Create resources
    print("Creating resources...")
    superpower_resource = create_resource(ROOT_RESOURCE_ID, 'superpower')
    submit_resource = create_resource(ROOT_RESOURCE_ID, 'submit')
    rating_resource = create_resource(ROOT_RESOURCE_ID, 'rating')
    leaderboard_resource = create_resource(ROOT_RESOURCE_ID, 'leaderboard')
    admin_resource = create_resource(ROOT_RESOURCE_ID, 'admin')
    
    # Create rating sub-resources
    rating_pairs_resource = create_resource(rating_resource, 'pairs')
    
    # Setup endpoints
    endpoints = [
        (superpower_resource, 'GET', 'supercharged-get-daily-superpower'),
        (submit_resource, 'POST', 'supercharged-submit-ideas'),
        (rating_pairs_resource, 'GET', 'supercharged-get-rating-pairs'),
        (rating_resource, 'POST', 'supercharged-submit-rating'),
        (leaderboard_resource, 'GET', 'supercharged-get-leaderboard'),
        (admin_resource, 'POST', 'supercharged-admin-add-superpower'),
    ]
    
    print("Creating methods and integrations...")
    for resource_id, method, function_name in endpoints:
        print(f"Setting up {method} for {function_name}...")
        create_method(resource_id, method)
        create_integration(resource_id, method, function_name)
        setup_cors(resource_id)
        time.sleep(1)  # Small delay to avoid rate limits
    
    # Deploy the API
    print("Deploying API...")
    apigateway.create_deployment(
        restApiId=API_ID,
        stageName='prod',
        description='Production deployment of SuperCharged API'
    )
    
    print(f"""
API Gateway setup complete!
Base URL: https://{API_ID}.execute-api.{REGION}.amazonaws.com/prod

Endpoints:
- GET  /superpower        - Get daily superpower
- POST /submit            - Submit user ideas
- GET  /rating/pairs      - Get pairs for rating
- POST /rating            - Submit rating
- GET  /leaderboard       - Get leaderboard
- POST /admin             - Add superpower (admin only)
""")

if __name__ == '__main__':
    main()