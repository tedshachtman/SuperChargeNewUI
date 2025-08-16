import json
import boto3
from datetime import datetime
import uuid

dynamodb = boto3.resource('dynamodb')
superpowers_table = dynamodb.Table('supercharged_superpowers')

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        title = body['title']
        description = body['description']
        date = body['date']  # YYYY-MM-DD format
        
        # Validate required fields
        if not title or not description or not date:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Title, description, and date are required'
                })
            }
        
        # Check if superpower already exists for this date
        existing = superpowers_table.query(
            IndexName='date-index',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('date').eq(date)
        )
        
        if existing['Items']:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': f'Superpower already exists for {date}'
                })
            }
        
        # Create superpower
        superpower_id = str(uuid.uuid4())
        now = datetime.now()
        timestamp = int(now.timestamp())
        
        superpower_item = {
            'superpowerID': superpower_id,
            'date': date,
            'title': title,
            'description': description,
            'isActive': date == now.strftime('%Y-%m-%d'),
            'timestamp': timestamp
        }
        
        superpowers_table.put_item(Item=superpower_item)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'superpowerId': superpower_id,
                'message': 'Superpower added successfully'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }