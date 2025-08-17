#!/usr/bin/env python3

import boto3
import json

def main():
    client = boto3.client('apigateway', region_name='us-east-1')
    
    # API Gateway details
    api_id = 'gsx73a1w3d'
    
    # Get the root resource
    resources = client.get_resources(restApiId=api_id)
    root_resource_id = None
    
    for resource in resources['items']:
        if resource['path'] == '/':
            root_resource_id = resource['id']
            break
    
    if not root_resource_id:
        print("❌ Could not find root resource")
        return
    
    print(f"🔍 Found root resource ID: {root_resource_id}")
    
    # Create /rooms resource
    try:
        rooms_resource = client.create_resource(
            restApiId=api_id,
            parentId=root_resource_id,
            pathPart='rooms'
        )
        rooms_resource_id = rooms_resource['id']
        print(f"✅ Created /rooms resource: {rooms_resource_id}")
    except client.exceptions.ConflictException:
        # Resource already exists, find it
        for resource in resources['items']:
            if resource['path'] == '/rooms':
                rooms_resource_id = resource['id']
                print(f"✅ Found existing /rooms resource: {rooms_resource_id}")
                break
    
    # Create /rooms/create resource
    try:
        create_resource = client.create_resource(
            restApiId=api_id,
            parentId=rooms_resource_id,
            pathPart='create'
        )
        create_resource_id = create_resource['id']
        print(f"✅ Created /rooms/create resource: {create_resource_id}")
    except client.exceptions.ConflictException:
        # Get existing resource
        resources = client.get_resources(restApiId=api_id)
        for resource in resources['items']:
            if resource['path'] == '/rooms/create':
                create_resource_id = resource['id']
                print(f"✅ Found existing /rooms/create resource: {create_resource_id}")
                break
    
    # Create /rooms/join resource
    try:
        join_resource = client.create_resource(
            restApiId=api_id,
            parentId=rooms_resource_id,
            pathPart='join'
        )
        join_resource_id = join_resource['id']
        print(f"✅ Created /rooms/join resource: {join_resource_id}")
    except client.exceptions.ConflictException:
        resources = client.get_resources(restApiId=api_id)
        for resource in resources['items']:
            if resource['path'] == '/rooms/join':
                join_resource_id = resource['id']
                print(f"✅ Found existing /rooms/join resource: {join_resource_id}")
                break
    
    # Create /rooms/list resource
    try:
        list_resource = client.create_resource(
            restApiId=api_id,
            parentId=rooms_resource_id,
            pathPart='list'
        )
        list_resource_id = list_resource['id']
        print(f"✅ Created /rooms/list resource: {list_resource_id}")
    except client.exceptions.ConflictException:
        resources = client.get_resources(restApiId=api_id)
        for resource in resources['items']:
            if resource['path'] == '/rooms/list':
                list_resource_id = resource['id']
                print(f"✅ Found existing /rooms/list resource: {list_resource_id}")
                break
    
    # Set up methods and integrations
    endpoints = [
        {
            'resource_id': create_resource_id,
            'http_method': 'POST',
            'function_name': 'supercharged-create-room',
            'path': '/rooms/create'
        },
        {
            'resource_id': join_resource_id,
            'http_method': 'POST',
            'function_name': 'supercharged-join-room',
            'path': '/rooms/join'
        },
        {
            'resource_id': list_resource_id,
            'http_method': 'GET',
            'function_name': 'supercharged-list-user-rooms',
            'path': '/rooms/list'
        }
    ]
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    for endpoint in endpoints:
        print(f"\n🔧 Setting up {endpoint['http_method']} {endpoint['path']}")
        
        # Create method
        try:
            client.put_method(
                restApiId=api_id,
                resourceId=endpoint['resource_id'],
                httpMethod=endpoint['http_method'],
                authorizationType='NONE'
            )
            print(f"✅ Created {endpoint['http_method']} method")
        except client.exceptions.ConflictException:
            print(f"✅ {endpoint['http_method']} method already exists")
        
        # Create method response
        try:
            client.put_method_response(
                restApiId=api_id,
                resourceId=endpoint['resource_id'],
                httpMethod=endpoint['http_method'],
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': False,
                    'method.response.header.Access-Control-Allow-Headers': False,
                    'method.response.header.Access-Control-Allow-Methods': False
                }
            )
            print(f"✅ Created {endpoint['http_method']} method response")
        except client.exceptions.ConflictException:
            print(f"✅ {endpoint['http_method']} method response already exists")
        
        # Create integration
        lambda_arn = f"arn:aws:lambda:us-east-1:696944065143:function:{endpoint['function_name']}"
        
        try:
            client.put_integration(
                restApiId=api_id,
                resourceId=endpoint['resource_id'],
                httpMethod=endpoint['http_method'],
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=f"arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
            )
            print(f"✅ Created {endpoint['http_method']} integration")
        except client.exceptions.ConflictException:
            print(f"✅ {endpoint['http_method']} integration already exists")
        
        # Create integration response
        try:
            client.put_integration_response(
                restApiId=api_id,
                resourceId=endpoint['resource_id'],
                httpMethod=endpoint['http_method'],
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,POST,OPTIONS'"
                }
            )
            print(f"✅ Created {endpoint['http_method']} integration response")
        except client.exceptions.ConflictException:
            print(f"✅ {endpoint['http_method']} integration response already exists")
        
        # Add Lambda permission
        try:
            lambda_client.add_permission(
                FunctionName=endpoint['function_name'],
                StatementId=f"apigateway-invoke-{endpoint['function_name']}-{endpoint['http_method'].lower()}",
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f"arn:aws:execute-api:us-east-1:696944065143:{api_id}/*/*"
            )
            print(f"✅ Added Lambda permission for {endpoint['function_name']}")
        except lambda_client.exceptions.ResourceConflictException:
            print(f"✅ Lambda permission already exists for {endpoint['function_name']}")
        
        # Add CORS OPTIONS method
        try:
            client.put_method(
                restApiId=api_id,
                resourceId=endpoint['resource_id'],
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            client.put_method_response(
                restApiId=api_id,
                resourceId=endpoint['resource_id'],
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': False,
                    'method.response.header.Access-Control-Allow-Headers': False,
                    'method.response.header.Access-Control-Allow-Methods': False
                }
            )
            
            client.put_integration(
                restApiId=api_id,
                resourceId=endpoint['resource_id'],
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={'application/json': '{"statusCode": 200}'}
            )
            
            client.put_integration_response(
                restApiId=api_id,
                resourceId=endpoint['resource_id'],
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,POST,OPTIONS'"
                }
            )
            print(f"✅ Added CORS OPTIONS method")
        except client.exceptions.ConflictException:
            print(f"✅ CORS OPTIONS method already exists")
    
    # Deploy API
    print(f"\n🚀 Deploying API to 'prod' stage...")
    client.create_deployment(
        restApiId=api_id,
        stageName='prod',
        description='Room management endpoints deployment'
    )
    print(f"✅ API deployed successfully!")
    
    print(f"\n🎉 Room API setup complete!")
    print(f"API endpoints:")
    print(f"  POST https://{api_id}.execute-api.us-east-1.amazonaws.com/prod/rooms/create")
    print(f"  POST https://{api_id}.execute-api.us-east-1.amazonaws.com/prod/rooms/join")
    print(f"  GET  https://{api_id}.execute-api.us-east-1.amazonaws.com/prod/rooms/list")

if __name__ == "__main__":
    main()