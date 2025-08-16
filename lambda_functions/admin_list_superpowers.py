import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
superpowers_table = dynamodb.Table('supercharged_superpowers')

def lambda_handler(event, context):
    try:
        # Scan all superpowers
        response = superpowers_table.scan()
        superpowers = response['Items']
        
        # Sort by date (newest first)
        superpowers.sort(key=lambda x: x['date'], reverse=True)
        
        # Format for frontend
        formatted_superpowers = []
        for superpower in superpowers:
            formatted_superpowers.append({
                'superpowerID': superpower['superpowerID'],
                'date': superpower['date'],
                'title': superpower['title'],
                'description': superpower['description'],
                'isActive': superpower.get('isActive', False),
                'timestamp': int(superpower['timestamp'])
            })
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'superpowers': formatted_superpowers,
                'total': len(formatted_superpowers)
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