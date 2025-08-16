import json
import boto3
from datetime import datetime
import uuid

dynamodb = boto3.resource('dynamodb')
superpowers_table = dynamodb.Table('supercharged_superpowers')

def lambda_handler(event, context):
    try:
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Query for today's superpower
        response = superpowers_table.query(
            IndexName='date-index',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('date').eq(today)
        )
        
        if response['Items']:
            superpower = response['Items'][0]
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': json.dumps({
                    'success': True,
                    'superpower': {
                        'id': superpower['superpowerID'],
                        'title': superpower['title'],
                        'description': superpower['description'],
                        'date': superpower['date']
                    }
                })
            }
        else:
            # No superpower for today - return default or error
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'No superpower scheduled for today'
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