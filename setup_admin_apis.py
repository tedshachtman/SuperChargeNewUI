#!/usr/bin/env python3

import boto3
import time

# API Gateway configuration
API_ID = "gsx73a1w3d"
ROOT_RESOURCE_ID = "xkr2voy6ak"
REGION = "us-east-1"
ACCOUNT_ID = "696944065143"

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
        pass

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
        pass
    
    # Add permission for API Gateway to invoke Lambda
    try:
        lambda_client.add_permission(
            FunctionName=lambda_function_name,
            StatementId=f'apigateway-invoke-{lambda_function_name}',
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=f'arn:aws:execute-api:{REGION}:{ACCOUNT_ID}:{API_ID}/*/*'
        )
    except Exception:
        pass

def setup_cors(resource_id):
    """Setup CORS for a resource"""
    try:
        apigateway.put_method(
            restApiId=API_ID,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            authorizationType='NONE'
        )
        
        apigateway.put_integration(
            restApiId=API_ID,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            type='MOCK',
            requestTemplates={'application/json': '{"statusCode": 200}'}
        )
        
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
        pass

def main():
    """Setup admin API endpoints"""
    print("Setting up admin API endpoints...")
    
    # Find admin resource
    response = apigateway.get_resources(restApiId=API_ID)
    admin_resource_id = None
    
    for resource in response['items']:
        if resource.get('pathPart') == 'admin':
            admin_resource_id = resource['id']
            break
    
    if not admin_resource_id:
        admin_resource_id = create_resource(ROOT_RESOURCE_ID, 'admin')
    
    # Create sub-resources
    superpowers_resource = create_resource(admin_resource_id, 'superpowers')
    submissions_resource = create_resource(admin_resource_id, 'submissions')
    
    # Setup endpoints
    print("Creating admin endpoints...")
    create_method(superpowers_resource, 'GET')
    create_integration(superpowers_resource, 'GET', 'supercharged-admin-list-superpowers')
    
    create_method(superpowers_resource, 'DELETE')
    create_integration(superpowers_resource, 'DELETE', 'supercharged-admin-delete-superpower')
    setup_cors(superpowers_resource)
    
    create_method(submissions_resource, 'GET')
    create_integration(submissions_resource, 'GET', 'supercharged-admin-list-submissions')
    setup_cors(submissions_resource)
    
    # Deploy
    apigateway.create_deployment(
        restApiId=API_ID,
        stageName='prod',
        description='Added admin list endpoints'
    )
    
    print(f"""
Admin API endpoints added!

New endpoints:
- GET /admin/superpowers   - List all superpowers
- DELETE /admin/superpowers - Delete superpower and related submissions
- GET /admin/submissions   - List all submissions

URLs:
- https://{API_ID}.execute-api.{REGION}.amazonaws.com/prod/admin/superpowers
- https://{API_ID}.execute-api.{REGION}.amazonaws.com/prod/admin/submissions
""")

if __name__ == '__main__':
    main()