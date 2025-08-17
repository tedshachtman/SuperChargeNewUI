#!/usr/bin/env python3

import json
import boto3
import time
from decimal import Decimal

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    try:
        # Get userId from query parameters
        user_id = event.get('queryStringParameters', {})
        if user_id:
            user_id = user_id.get('userId')
        
        if not user_id:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'userId query parameter is required'})
            }
        
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        room_users_table = dynamodb.Table('supercharged_room_users')
        rooms_table = dynamodb.Table('supercharged_rooms')
        
        # Get all rooms user is a member of
        response = room_users_table.query(
            IndexName='user-index',
            KeyConditionExpression='userId = :uid',
            ExpressionAttributeValues={':uid': user_id}
        )
        
        user_rooms = response.get('Items', [])
        room_details = []
        current_time = int(time.time())
        
        for user_room in user_rooms:
            room_id = user_room['roomId']
            
            # Get room details
            room_response = rooms_table.get_item(Key={'roomId': room_id})
            room = room_response.get('Item')
            
            if room:
                # Get member count
                members_response = room_users_table.query(
                    IndexName='room-index',
                    KeyConditionExpression='roomId = :rid',
                    ExpressionAttributeValues={':rid': room_id}
                )
                member_count = len(members_response.get('Items', []))
                
                # Determine room status
                status = room.get('status', 'waiting')
                if current_time > room.get('expiresAt', 0):
                    status = 'expired'
                elif current_time > room.get('submissionDeadline', 0):
                    if current_time > room.get('ratingDeadline', 0):
                        status = 'completed'
                    else:
                        status = 'rating'
                elif member_count > 1:  # At least 2 people for game to be active
                    status = 'active'
                
                room_info = {
                    'roomId': room_id,
                    'gameCode': room.get('gameCode'),
                    'roomName': room.get('roomName'),
                    'superpower': room.get('superpower'),
                    'status': status,
                    'memberCount': member_count,
                    'maxPlayers': room.get('maxPlayers', 20),
                    'createdBy': room.get('createdBy'),
                    'userRole': user_room.get('role'),
                    'submissionDeadline': room.get('submissionDeadline'),
                    'ratingDeadline': room.get('ratingDeadline'),
                    'createdAt': room.get('createdAt'),
                    'timeRemaining': max(0, room.get('submissionDeadline', 0) - current_time)
                }
                
                room_details.append(room_info)
        
        # Sort by creation time (newest first)
        room_details.sort(key=lambda x: x.get('createdAt', 0), reverse=True)
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'rooms': room_details,
                'totalRooms': len(room_details)
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': f'Failed to list user rooms: {str(e)}'})
        }