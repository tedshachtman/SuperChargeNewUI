#!/usr/bin/env python3

import json
import boto3
import uuid
import random
import string
import time
from decimal import Decimal

def lambda_handler(event, context):
    try:
        # Parse request body
        if event.get('body'):
            body = json.loads(event['body'])
        else:
            body = event
        
        creator_id = body.get('userId')
        room_name = body.get('roomName', 'Private Room')
        power_type = body.get('powerType')  # 'custom' or 'auto'
        difficulty = body.get('difficulty', 'medium')  # for auto-generated
        custom_title = body.get('customTitle')
        custom_description = body.get('customDescription')
        
        if not creator_id:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'userId is required'})
            }
        
        if not power_type:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'powerType is required (custom or auto)'})
            }
        
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Generate unique room ID and game code
        room_id = str(uuid.uuid4())
        game_code = generate_game_code()
        
        # Make sure game code is unique
        rooms_table = dynamodb.Table('supercharged_rooms')
        while check_game_code_exists(rooms_table, game_code):
            game_code = generate_game_code()
        
        # Handle superpower selection
        superpower = None
        if power_type == 'custom':
            if not custom_title or not custom_description:
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Custom title and description required for custom power'})
                }
            superpower = {
                'title': custom_title,
                'description': custom_description,
                'isCustom': True
            }
        elif power_type == 'auto':
            # Get random power from library
            library_table = dynamodb.Table('supercharged_superpower_library')
            superpower = get_random_power_from_library(library_table, difficulty)
            if not superpower:
                return {
                    'statusCode': 500,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Failed to get random power from library'})
                }
        
        # Create room record
        current_time = int(time.time())
        room_data = {
            'roomId': room_id,
            'gameCode': game_code,
            'createdBy': creator_id,
            'roomName': room_name,
            'superpower': superpower,
            'status': 'waiting',  # waiting, active, completed
            'createdAt': current_time,
            'expiresAt': current_time + (24 * 60 * 60),  # 24 hours from now
            'maxPlayers': 20,
            'aiIdeasGenerated': False,
            'submissionDeadline': current_time + (23 * 60 * 60),  # 23 hours to submit
            'ratingDeadline': current_time + (23 * 60 * 60) + (15 * 60)  # +15 min for rating
        }
        
        rooms_table.put_item(Item=room_data)
        
        # Add creator as first room member
        room_users_table = dynamodb.Table('supercharged_room_users')
        room_user_id = str(uuid.uuid4())
        
        room_user_data = {
            'roomUserId': room_user_id,
            'roomId': room_id,
            'userId': creator_id,
            'joinedAt': current_time,
            'role': 'creator'
        }
        
        room_users_table.put_item(Item=room_user_data)
        
        # Trigger AI idea generation for the room
        try:
            generate_ai_ideas_for_room(room_id, superpower)
        except Exception as e:
            print(f"AI generation failed but room created: {str(e)}")
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'roomId': room_id,
                'gameCode': game_code,
                'superpower': superpower,
                'message': 'Room created successfully'
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': f'Failed to create room: {str(e)}'})
        }

def generate_game_code():
    """Generate a 6-character alphanumeric game code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def check_game_code_exists(table, game_code):
    """Check if game code already exists"""
    try:
        response = table.query(
            IndexName='gamecode-index',
            KeyConditionExpression='gameCode = :gc',
            ExpressionAttributeValues={':gc': game_code}
        )
        return len(response.get('Items', [])) > 0
    except:
        return False

def get_random_power_from_library(table, difficulty):
    """Get a random power from the library by difficulty"""
    try:
        response = table.query(
            IndexName='difficulty-index',
            KeyConditionExpression='difficulty = :diff',
            ExpressionAttributeValues={':diff': difficulty}
        )
        
        powers = response.get('Items', [])
        if not powers:
            return None
        
        # Select random power
        selected_power = random.choice(powers)
        return {
            'title': selected_power['title'],
            'description': selected_power['description'],
            'difficulty': difficulty,
            'isCustom': False
        }
    except Exception as e:
        print(f"Error getting random power: {str(e)}")
        return None

def generate_ai_ideas_for_room(room_id, superpower):
    """Trigger AI idea generation for this room using Lambda"""
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        payload = {
            'roomId': room_id,
            'superpower': superpower
        }
        
        # Invoke the AI generation function asynchronously
        lambda_client.invoke(
            FunctionName='supercharged-generate-room-ai-ideas',
            InvocationType='Event',  # Async
            Payload=json.dumps(payload)
        )
        
        print(f"AI generation triggered for room {room_id}")
        
    except Exception as e:
        print(f"Failed to trigger AI generation: {str(e)}")
        raise