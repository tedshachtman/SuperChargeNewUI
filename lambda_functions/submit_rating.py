import json
import boto3
from datetime import datetime
import uuid

dynamodb = boto3.resource('dynamodb')
ratings_table = dynamodb.Table('supercharged_ratings')
progress_table = dynamodb.Table('supercharged_user_progress')

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        user_id = body['userId']
        submission_id1 = body['submissionId1']
        submission_id2 = body['submissionId2']
        rating = body['rating']  # 1-5 scale
        
        # Validate rating
        if rating not in [1, 2, 3, 4, 5]:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Rating must be between 1 and 5'
                })
            }
        
        today = datetime.now().strftime('%Y-%m-%d')
        now = datetime.now()
        timestamp = int(now.timestamp())
        
        # Check if this pair was already rated by this user
        existing_ratings = ratings_table.query(
            IndexName='user-date-index',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('userId').eq(user_id) & 
                                 boto3.dynamodb.conditions.Key('date').eq(today)
        )
        
        for existing_rating in existing_ratings['Items']:
            existing_pair = set([existing_rating['submissionId1'], existing_rating['submissionId2']])
            current_pair = set([submission_id1, submission_id2])
            if existing_pair == current_pair:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'This pair has already been rated'
                    })
                }
        
        # Create rating
        rating_id = str(uuid.uuid4())
        
        rating_item = {
            'ratingId': rating_id,
            'userId': user_id,
            'date': today,
            'submissionId1': submission_id1,
            'submissionId2': submission_id2,
            'rating': rating,
            'timestamp': timestamp
        }
        
        ratings_table.put_item(Item=rating_item)
        
        # Update user progress - increment ratings completed
        try:
            progress_table.update_item(
                Key={'userId': user_id, 'date': today},
                UpdateExpression='ADD ratingsCompleted :inc',
                ExpressionAttributeValues={':inc': 1}
            )
        except:
            # Create progress record if doesn't exist
            progress_table.put_item(Item={
                'userId': user_id,
                'date': today,
                'hasSubmitted': False,  # This will be updated when they submit
                'ratingsCompleted': 1,
                'ratingsTarget': 0,
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
                'ratingId': rating_id,
                'message': 'Rating submitted successfully'
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