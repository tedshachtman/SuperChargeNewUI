import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
superpowers_table = dynamodb.Table('supercharged_superpowers')
submissions_table = dynamodb.Table('supercharged_submissions')

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        superpower_id = body['superpowerId']
        
        # Check if superpower exists
        response = superpowers_table.get_item(
            Key={'superpowerID': superpower_id}
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Superpower not found'
                })
            }
        
        superpower = response['Item']
        
        # Delete all related submissions (both AI and human)
        submissions_response = submissions_table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('superpowerId').eq(superpower_id)
        )
        
        deleted_submissions = 0
        for submission in submissions_response['Items']:
            submissions_table.delete_item(
                Key={'submissionId': submission['submissionId']}
            )
            deleted_submissions += 1
        
        # Delete the superpower itself
        superpowers_table.delete_item(
            Key={'superpowerID': superpower_id}
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'message': f'Deleted superpower "{superpower["title"]}" and {deleted_submissions} related submissions',
                'deletedSubmissions': deleted_submissions
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }