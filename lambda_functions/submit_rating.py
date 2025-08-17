import json
import boto3
from datetime import datetime
import uuid
import math
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
ratings_table = dynamodb.Table('supercharged_ratings')
progress_table = dynamodb.Table('supercharged_user_progress')
submissions_table = dynamodb.Table('supercharged_submissions')

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    try:
        # Convert Decimal to float for calculations
        vec1_float = [float(x) for x in vec1]
        vec2_float = [float(x) for x in vec2]
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1_float, vec2_float))
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vec1_float))
        magnitude2 = math.sqrt(sum(a * a for a in vec2_float))
        
        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        
        return dot_product / (magnitude1 * magnitude2)
    except:
        return 0

def calculate_rating_accuracy(user_rating, embedding_similarity):
    """
    Calculate accuracy score based on how well user rating matches embedding similarity
    
    Args:
        user_rating: 1-5 scale rating from user
        embedding_similarity: 0-1 cosine similarity from embeddings
    
    Returns:
        accuracy_score: 0-100 score based on how close the ratings match
    """
    try:
        # Convert embedding similarity (0-1) to 1-5 scale
        # 0.0-0.2 -> 1, 0.2-0.4 -> 2, 0.4-0.6 -> 3, 0.6-0.8 -> 4, 0.8-1.0 -> 5
        expected_rating = min(5, max(1, int(embedding_similarity * 5) + 1))
        
        # Calculate how far off the user was (0-4 scale)
        rating_difference = abs(user_rating - expected_rating)
        
        # Convert to accuracy score (100 = perfect, 0 = completely wrong)
        accuracy_score = max(0, 100 - (rating_difference * 25))
        
        return accuracy_score, expected_rating
    except:
        return 50, 3  # Default middle score if calculation fails

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        user_id = body['userId']
        submission_id1 = body['submissionId1']
        submission_id2 = body['submissionId2']
        rating = body['rating']  # 1-5 scale
        room_id = body.get('roomId')  # Optional for room-based games
        
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
        if room_id:
            # Room-based: check ratings for this room
            existing_ratings = ratings_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('userId').eq(user_id) & 
                               boto3.dynamodb.conditions.Attr('roomId').eq(room_id)
            )
        else:
            # Global: check ratings for today
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
        
        # Get submissions to calculate embedding similarity
        try:
            sub1_response = submissions_table.get_item(Key={'submissionId': submission_id1})
            sub2_response = submissions_table.get_item(Key={'submissionId': submission_id2})
            
            embedding_similarity = 0.5  # Default middle similarity
            expected_rating = 3
            accuracy_score = 50
            
            if (sub1_response.get('Item') and sub2_response.get('Item') and 
                'embeddings' in sub1_response['Item'] and 'embeddings' in sub2_response['Item']):
                
                # Calculate cosine similarity between embeddings
                emb1 = sub1_response['Item']['embeddings']
                emb2 = sub2_response['Item']['embeddings']
                embedding_similarity = cosine_similarity(emb1, emb2)
                
                # Calculate accuracy score
                accuracy_score, expected_rating = calculate_rating_accuracy(rating, embedding_similarity)
                
        except Exception as e:
            print(f"Error calculating embedding similarity: {str(e)}")
            # Use defaults if calculation fails
        
        # Create rating
        rating_id = str(uuid.uuid4())
        
        rating_item = {
            'ratingId': rating_id,
            'userId': user_id,
            'date': today,
            'submissionId1': submission_id1,
            'submissionId2': submission_id2,
            'rating': rating,
            'timestamp': timestamp,
            'embeddingSimilarity': Decimal(str(embedding_similarity)),
            'expectedRating': expected_rating,
            'accuracyScore': accuracy_score
        }
        
        # Add roomId if this is a room-based rating
        if room_id:
            rating_item['roomId'] = room_id
        
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
                'message': 'Rating submitted successfully',
                'feedback': {
                    'userRating': rating,
                    'expectedRating': expected_rating,
                    'embeddingSimilarity': float(embedding_similarity),
                    'accuracyScore': accuracy_score
                }
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