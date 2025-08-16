import json
import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
submissions_table = dynamodb.Table('supercharged_submissions')
superpowers_table = dynamodb.Table('supercharged_superpowers')

def lambda_handler(event, context):
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        date_filter = query_params.get('date')
        limit = int(query_params.get('limit', 50))
        
        # Scan submissions
        if date_filter:
            response = submissions_table.query(
                IndexName='date-index',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('date').eq(date_filter)
            )
        else:
            response = submissions_table.scan()
        
        submissions = response['Items']
        
        # Get superpower titles for context
        superpowers_response = superpowers_table.scan()
        superpower_titles = {sp['superpowerID']: sp['title'] for sp in superpowers_response['Items']}
        
        # Format submissions and add superpower titles
        formatted_submissions = []
        for submission in submissions:
            # Convert Decimal to appropriate types
            timestamp = int(submission['timestamp']) if isinstance(submission['timestamp'], Decimal) else submission['timestamp']
            
            formatted_submission = {
                'submissionId': submission['submissionId'],
                'userId': submission['userId'],
                'date': submission['date'],
                'superpowerId': submission['superpowerId'],
                'superpowerTitle': superpower_titles.get(submission['superpowerId'], 'Unknown Superpower'),
                'ideas': submission['ideas'],
                'timestamp': timestamp,
                'submittedAt': submission['submittedAt'],
                'isAI': submission.get('isAI', False),
                'aiModel': submission.get('aiModel', '')
            }
            
            formatted_submissions.append(formatted_submission)
        
        # Sort by timestamp (newest first)
        formatted_submissions.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Apply limit
        if len(formatted_submissions) > limit:
            formatted_submissions = formatted_submissions[:limit]
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'submissions': formatted_submissions,
                'total': len(submissions),
                'returned': len(formatted_submissions)
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