#!/usr/bin/env python3

import json
import boto3
import uuid
import time
from decimal import Decimal

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    try:
        # Parse request body
        if event.get('body'):
            body = json.loads(event['body'])
        else:
            body = event
        
        user_id = body.get('userId')
        game_code = body.get('gameCode')
        
        if not user_id or not game_code:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'userId and gameCode are required'})
            }
        
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        rooms_table = dynamodb.Table('supercharged_rooms')
        room_users_table = dynamodb.Table('supercharged_room_users')
        
        # Find room by game code
        response = rooms_table.query(
            IndexName='gamecode-index',
            KeyConditionExpression='gameCode = :gc',
            ExpressionAttributeValues={':gc': game_code.upper()}
        )
        
        rooms = response.get('Items', [])
        if not rooms:
            return {
                'statusCode': 404,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Room not found with that game code'})
            }
        
        room = rooms[0]
        room_id = room['roomId']
        
        # Check if room is still accepting players
        current_time = int(time.time())
        if room.get('status') == 'completed':
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'This room has already completed'})
            }
        
        if current_time > room.get('expiresAt', 0):
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'This room has expired'})
            }
        
        # Check if user is already in this room
        existing_user = room_users_table.query(
            IndexName='room-index',
            KeyConditionExpression='roomId = :rid',
            FilterExpression='userId = :uid',
            ExpressionAttributeValues={
                ':rid': room_id,
                ':uid': user_id
            }
        )
        
        if existing_user.get('Items'):
            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'message': 'Already in room',
                    'roomId': room_id,
                    'superpower': room.get('superpower'),
                    'roomName': room.get('roomName')
                }, default=decimal_default)
            }
        
        # Check room capacity
        current_members = room_users_table.query(
            IndexName='room-index',
            KeyConditionExpression='roomId = :rid',
            ExpressionAttributeValues={':rid': room_id}
        )
        
        if len(current_members.get('Items', [])) >= room.get('maxPlayers', 20):
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Room is full'})
            }
        
        # Add user to room
        room_user_id = str(uuid.uuid4())
        room_user_data = {
            'roomUserId': room_user_id,
            'roomId': room_id,
            'userId': user_id,
            'joinedAt': current_time,
            'role': 'member'
        }
        
        room_users_table.put_item(Item=room_user_data)
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'message': 'Successfully joined room',
                'roomId': room_id,
                'superpower': room.get('superpower'),
                'roomName': room.get('roomName'),
                'submissionDeadline': room.get('submissionDeadline'),
                'ratingDeadline': room.get('ratingDeadline')
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': f'Failed to join room: {str(e)}'})
        }