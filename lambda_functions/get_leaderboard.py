import json
import boto3
from datetime import datetime, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
submissions_table = dynamodb.Table('supercharged_submissions')
ratings_table = dynamodb.Table('supercharged_ratings')
progress_table = dynamodb.Table('supercharged_user_progress')

def lambda_handler(event, context):
    try:
        # Get date parameter (default to yesterday for results)
        query_params = event.get('queryStringParameters', {}) or {}
        target_date = query_params.get('date')
        
        if not target_date:
            # Default to yesterday's results
            yesterday = datetime.now() - timedelta(days=1)
            target_date = yesterday.strftime('%Y-%m-%d')
        
        # Get all submissions for the target date
        submissions_response = submissions_table.query(
            IndexName='date-index',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('date').eq(target_date)
        )
        
        all_submissions = submissions_response['Items']
        
        if not all_submissions:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': f'No submissions found for {target_date}'
                })
            }
        
        # Calculate scores for each submission
        submission_scores = {}
        
        for submission in all_submissions:
            submission_id = submission['submissionId']
            user_id = submission['userId']
            
            # Get all ratings for this submission
            ratings_for_submission = []
            
            # Query ratings where this submission is either submissionId1 or submissionId2
            all_ratings = ratings_table.query(
                IndexName='date-index',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('date').eq(target_date)
            )
            
            for rating in all_ratings['Items']:
                if rating['submissionId1'] == submission_id or rating['submissionId2'] == submission_id:
                    rating_value = rating['rating']
                    # Convert Decimal to float if necessary
                    if isinstance(rating_value, Decimal):
                        rating_value = float(rating_value)
                    ratings_for_submission.append(rating_value)
            
            # Calculate average rating (higher is better)
            avg_rating = sum(ratings_for_submission) / len(ratings_for_submission) if ratings_for_submission else 0
            
            # Get user's rating accuracy (how well they rated others)
            user_ratings = [r for r in all_ratings['Items'] if r['userId'] == user_id]
            rating_accuracy = calculate_rating_accuracy(user_ratings, all_submissions)
            
            # Combined score (50% submission quality, 50% rating accuracy)
            total_score = (float(avg_rating) * 20) + (float(rating_accuracy) * 100)  # Scale to 0-120
            
            submission_scores[submission_id] = {
                'userId': user_id,
                'submissionScore': avg_rating,
                'ratingAccuracy': rating_accuracy,
                'totalScore': total_score,
                'ideas': submission['ideas'][:2],  # Only show first 2 ideas in leaderboard
                'ratingCount': len(ratings_for_submission)
            }
        
        # Sort by total score
        sorted_submissions = sorted(
            submission_scores.items(), 
            key=lambda x: x[1]['totalScore'], 
            reverse=True
        )
        
        # Create leaderboard
        leaderboard = []
        for rank, (submission_id, data) in enumerate(sorted_submissions[:10], 1):
            leaderboard.append({
                'rank': rank,
                'userId': data['userId'],
                'submissionScore': round(data['submissionScore'], 2),
                'ratingAccuracy': round(data['ratingAccuracy'], 2),
                'totalScore': round(data['totalScore'], 2),
                'topIdeas': data['ideas'],
                'ratingCount': data['ratingCount']
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
                'date': target_date,
                'leaderboard': leaderboard,
                'totalParticipants': len(all_submissions)
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

def calculate_rating_accuracy(user_ratings, all_submissions):
    """Calculate how well user's ratings match the consensus"""
    if not user_ratings:
        return 0.0
    
    # This is a simplified accuracy calculation
    # In a real system, you'd calculate correlation with consensus ratings
    # For now, return a mock accuracy based on rating variance
    
    ratings_values = []
    for r in user_ratings:
        rating_val = r['rating']
        # Convert Decimal to float
        if isinstance(rating_val, Decimal):
            rating_val = float(rating_val)
        ratings_values.append(rating_val)
    
    if not ratings_values:
        return 0.0
    
    # Users who rate with moderate variance (not all 1s or 5s) get higher accuracy
    variance = sum((r - 3.0) ** 2 for r in ratings_values) / len(ratings_values)
    
    # Optimal variance around 1.5 (moderate spread)
    accuracy = max(0.0, 1.0 - abs(variance - 1.5) / 1.5)
    
    return accuracy