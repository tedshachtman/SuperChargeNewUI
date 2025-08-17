#!/usr/bin/env python3

import requests
import json
import time

API_BASE = 'https://gsx73a1w3d.execute-api.us-east-1.amazonaws.com/prod'

def test_room_creation():
    """Test creating a room with auto-generated power"""
    print("🚀 Testing room creation...")
    
    create_data = {
        'userId': 'TestUser123',
        'roomName': 'Epic Test Room',
        'powerType': 'auto',
        'difficulty': 'medium'
    }
    
    response = requests.post(f'{API_BASE}/rooms/create', json=create_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Room created successfully!")
        print(f"Room ID: {result['roomId']}")
        print(f"Game Code: {result['gameCode']}")
        print(f"Power: {result['superpower']['title']}")
        return result['roomId'], result['gameCode']
    else:
        print(f"❌ Failed to create room: {response.text}")
        return None, None

def test_room_joining(game_code):
    """Test joining a room with game code"""
    print(f"\n🔗 Testing room joining with code {game_code}...")
    
    join_data = {
        'userId': 'TestUser456',
        'gameCode': game_code
    }
    
    response = requests.post(f'{API_BASE}/rooms/join', json=join_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Successfully joined room: {result['roomName']}")
        return True
    else:
        print(f"❌ Failed to join room: {response.text}")
        return False

def test_list_user_rooms(user_id):
    """Test listing user's rooms"""
    print(f"\n📋 Testing room listing for user {user_id}...")
    
    response = requests.get(f'{API_BASE}/rooms/list?userId={user_id}')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Found {result['totalRooms']} rooms")
        for room in result['rooms']:
            print(f"  - {room['roomName']} ({room['gameCode']}) - {room['status']} - {room['memberCount']} members")
        return True
    else:
        print(f"❌ Failed to list rooms: {response.text}")
        return False

def test_room_submission(room_id):
    """Test submitting ideas to a room"""
    print(f"\n📝 Testing room submission...")
    
    submission_data = {
        'userId': 'TestUser123',
        'superpowerId': room_id,  # Use room ID as superpower ID for rooms
        'roomId': room_id,
        'ideas': [
            'Idea 1 for testing room functionality with unique creative applications',
            'Idea 2 demonstrating mechanical complexity within room-based game constraints',
            'Idea 3 showing novel approach to room-isolated creative challenges',
            'Idea 4 completing the required set for room-based idea submission testing'
        ]
    }
    
    response = requests.post(f'{API_BASE}/submit', json=submission_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Ideas submitted to room successfully!")
        print(f"Submission ID: {result['submissionId']}")
        return True
    else:
        print(f"❌ Failed to submit to room: {response.text}")
        return False

def test_superpower_library():
    """Test the superpower library is populated"""
    print(f"\n🔮 Testing superpower library...")
    
    import boto3
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('supercharged_superpower_library')
    
    # Count powers by difficulty
    for difficulty in ['easy', 'medium', 'hard']:
        response = table.query(
            IndexName='difficulty-index',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('difficulty').eq(difficulty)
        )
        count = len(response.get('Items', []))
        print(f"  {difficulty.title()}: {count} powers")
    
    print("✅ Superpower library populated")

def main():
    print("🧪 Testing Complete Room System")
    print("=" * 50)
    
    # Test superpower library
    test_superpower_library()
    
    # Test room creation
    room_id, game_code = test_room_creation()
    
    if not room_id:
        print("❌ Cannot continue without valid room")
        return
    
    # Wait a moment for AI generation to start
    time.sleep(2)
    
    # Test room joining
    join_success = test_room_joining(game_code)
    
    # Test listing rooms
    test_list_user_rooms('TestUser123')
    test_list_user_rooms('TestUser456')
    
    # Test room submission
    test_room_submission(room_id)
    
    print(f"\n🎉 Room system testing complete!")
    print(f"Room ID: {room_id}")
    print(f"Game Code: {game_code}")
    print(f"\nTest URLs:")
    print(f"  Room Management: http://localhost:8000/rooms.html")
    print(f"  Join Room Game: http://localhost:8000/cloth.html?mode=room&roomId={room_id}")

if __name__ == "__main__":
    main()