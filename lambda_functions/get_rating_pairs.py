import json
import boto3
from datetime import datetime
import random

dynamodb = boto3.resource('dynamodb')
submissions_table = dynamodb.Table('supercharged_submissions')
ratings_table = dynamodb.Table('supercharged_ratings')

def lambda_handler(event, context):
    try:
        # Parse request
        user_id = event['queryStringParameters']['userId']
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Get all submissions for today (excluding user's own)
        response = submissions_table.query(
            IndexName='date-index',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('date').eq(today)
        )
        
        all_submissions = [item for item in response['Items'] if item['userId'] != user_id]
        
        if len(all_submissions) < 2:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Not enough submissions available for rating'
                })
            }
        
        # Get user's existing ratings to avoid duplicates
        user_ratings = ratings_table.query(
            IndexName='user-date-index',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('userId').eq(user_id) & 
                                 boto3.dynamodb.conditions.Key('date').eq(today)
        )
        
        rated_pairs = set()
        for rating in user_ratings['Items']:
            pair = tuple(sorted([rating['submissionId1'], rating['submissionId2']]))
            rated_pairs.add(pair)
        
        # Generate available pairs (not yet rated by this user)
        available_pairs = []
        for i, sub1 in enumerate(all_submissions):
            for j, sub2 in enumerate(all_submissions[i+1:], i+1):
                pair = tuple(sorted([sub1['submissionId'], sub2['submissionId']]))
                if pair not in rated_pairs:
                    available_pairs.append({
                        'submission1': {
                            'id': sub1['submissionId'],
                            'ideas': sub1['ideas']
                        },
                        'submission2': {
                            'id': sub2['submissionId'],
                            'ideas': sub2['ideas']
                        }
                    })
        
        if not available_pairs:
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': json.dumps({
                    'success': True,
                    'pairs': [],
                    'message': 'All available pairs have been rated'
                })
            }
        
        # Return up to 20 random pairs for 15-minute rating session
        random.shuffle(available_pairs)
        rating_pairs = available_pairs[:20]
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'pairs': rating_pairs,
                'totalAvailable': len(available_pairs)
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