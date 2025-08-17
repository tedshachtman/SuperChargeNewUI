import json
import boto3
from datetime import datetime
import uuid
import requests
import os
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
submissions_table = dynamodb.Table('supercharged_submissions')
progress_table = dynamodb.Table('supercharged_user_progress')

def generate_embeddings(ideas):
    """Generate embeddings for ideas using OpenAI API"""
    try:
        # Use OpenAI API key from environment
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Combine all 4 ideas into one text for submission-level embedding
        combined_text = " ".join(ideas)
        
        data = {
            "input": combined_text,
            "model": "text-embedding-3-large"
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if 'data' in result and len(result['data']) > 0:
            # Convert float list to Decimal list for DynamoDB
            embedding = result['data'][0]['embedding']
            return [Decimal(str(float(x))) for x in embedding]
        
        return None
        
    except Exception as e:
        print(f"Error generating embeddings: {str(e)}")
        return None

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        user_id = body['userId']
        superpower_id = body['superpowerId']
        room_id = body.get('roomId')  # Optional - for room-based games
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
        current_timestamp = int(now.timestamp())
        
        # Handle room-based vs global submissions differently
        if room_id:
            # Room-based submission - check room deadline
            rooms_table = dynamodb.Table('supercharged_rooms')
            room_response = rooms_table.get_item(Key={'roomId': room_id})
            if not room_response.get('Item'):
                return {
                    'statusCode': 404,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Room not found'
                    })
                }
            
            room = room_response['Item']
            submission_deadline = room.get('submissionDeadline', 0)
            
            if current_timestamp > submission_deadline:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Submission deadline has passed for this room'
                    })
                }
            
            # Check if user already submitted for this room
            existing_submissions = submissions_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('userId').eq(user_id) & 
                               boto3.dynamodb.conditions.Attr('roomId').eq(room_id)
            )
        else:
            # Global submission - check daily deadline
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
        
        # Generate embeddings for the ideas
        embeddings = generate_embeddings(ideas)
        
        submission_item = {
            'submissionId': submission_id,
            'userId': user_id,
            'date': today,
            'superpowerId': superpower_id,
            'ideas': ideas,
            'timestamp': timestamp,
            'submittedAt': now.isoformat()
        }
        
        # Add embeddings if successfully generated
        if embeddings:
            submission_item['embeddings'] = embeddings
        
        # Add roomId if this is a room-based submission
        if room_id:
            submission_item['roomId'] = room_id
        
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