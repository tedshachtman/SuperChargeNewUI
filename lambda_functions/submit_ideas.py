import json
import boto3
from datetime import datetime
import uuid

dynamodb = boto3.resource('dynamodb')
submissions_table = dynamodb.Table('supercharged_submissions')
progress_table = dynamodb.Table('supercharged_user_progress')

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        user_id = body['userId']
        superpower_id = body['superpowerId']
        ideas = body['ideas']  # Array of 4 ideas
        
        # Validate ideas
        if len(ideas) != 4:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Exactly 4 ideas required'
                })
            }
        
        # Validate word count (max 100 words per idea)
        for i, idea in enumerate(ideas):
            word_count = len(idea.split())
            if word_count > 100:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': f'Idea {i+1} exceeds 100 words ({word_count} words)'
                    })
                }
        
        today = datetime.now().strftime('%Y-%m-%d')
        now = datetime.now()
        
        # Check if it's past 11:59 PM
        if now.hour == 23 and now.minute >= 59:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Submission deadline has passed for today'
                })
            }
        
        # Check if user already submitted for today
        existing_submissions = submissions_table.query(
            IndexName='user-date-index',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('userId').eq(user_id) & 
                                 boto3.dynamodb.conditions.Key('date').eq(today)
        )
        
        if existing_submissions['Items']:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'You have already submitted ideas for today'
                })
            }
        
        # Create submission
        submission_id = str(uuid.uuid4())
        timestamp = int(now.timestamp())
        
        submission_item = {
            'submissionId': submission_id,
            'userId': user_id,
            'date': today,
            'superpowerId': superpower_id,
            'ideas': ideas,
            'timestamp': timestamp,
            'submittedAt': now.isoformat()
        }
        
        submissions_table.put_item(Item=submission_item)
        
        # Update user progress
        progress_table.put_item(Item={
            'userId': user_id,
            'date': today,
            'hasSubmitted': True,
            'ratingsCompleted': 0,
            'ratingsTarget': 0,  # Will be calculated when rating starts
            'percentileRank': 0,
            'totalScore': 0
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
                'submissionId': submission_id,
                'message': 'Ideas submitted successfully'
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