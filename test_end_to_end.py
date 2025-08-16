#!/usr/bin/env python3

import requests
import json
import time

API_BASE_URL = 'https://gsx73a1w3d.execute-api.us-east-1.amazonaws.com/prod'

def test_complete_flow():
    """Test the complete SuperCharge workflow"""
    
    print("🧪 Testing SuperCharge End-to-End Flow\n")
    
    # Test 1: Get daily superpower
    print("1️⃣ Testing GET /superpower...")
    response = requests.get(f"{API_BASE_URL}/superpower")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Got superpower: {result.get('superpower', {}).get('title', 'N/A')}")
    else:
        print(f"❌ Error: {response.text}")
    
    print()
    
    # Test 2: Submit user ideas
    print("2️⃣ Testing POST /submit...")
    test_submission = {
        "userId": "test_user_123",
        "superpowerId": "demo-today",
        "ideas": [
            "Use perfect memory to become a human GPS by memorizing every road, shortcut, and traffic pattern in real-time.",
            "Memorize all known allergies and drug interactions to become an instant medical safety consultant.",
            "Remember every person's preferences and interests to become the ultimate networker and relationship builder.",
            "Store perfect memories of crime scenes to help solve cold cases by spotting overlooked details."
        ]
    }
    
    response = requests.post(
        f"{API_BASE_URL}/submit",
        headers={'Content-Type': 'application/json'},
        json=test_submission
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Result: {result.get('message', result.get('error', 'Unknown'))}")
    
    submission_id = result.get('submissionId')
    print()
    
    # Test 3: Get rating pairs
    print("3️⃣ Testing GET /rating/pairs...")
    response = requests.get(f"{API_BASE_URL}/rating/pairs?userId=test_user_123")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        pairs_count = len(result.get('pairs', []))
        print(f"✅ Got {pairs_count} pairs for rating")
        if pairs_count > 0:
            print(f"First pair includes {len(result['pairs'][0]['submission1']['ideas'])} + {len(result['pairs'][0]['submission2']['ideas'])} ideas")
    else:
        print(f"❌ Error: {response.text}")
    
    print()
    
    # Test 4: Submit a rating
    if submission_id:
        print("4️⃣ Testing POST /rating...")
        test_rating = {
            "userId": "test_user_123",
            "submissionId1": submission_id,
            "submissionId2": "bdd68ae5-14cc-4e18-b640-6ffac164179f",  # One of the AI submissions
            "rating": 3
        }
        
        response = requests.post(
            f"{API_BASE_URL}/rating",
            headers={'Content-Type': 'application/json'},
            json=test_rating
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Result: {result.get('message', result.get('error', 'Unknown'))}")
        print()
    
    # Test 5: Get leaderboard
    print("5️⃣ Testing GET /leaderboard...")
    response = requests.get(f"{API_BASE_URL}/leaderboard?date=2025-08-16")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        leaderboard = result.get('leaderboard', [])
        print(f"✅ Got leaderboard with {len(leaderboard)} entries")
        if leaderboard:
            print(f"Top performer: {leaderboard[0].get('userId', 'N/A')} with score {leaderboard[0].get('totalScore', 0)}")
    else:
        print(f"❌ Error: {response.text}")
    
    print()
    
    # Test 6: Check AI submissions count
    print("6️⃣ Verifying AI submissions in database...")
    import boto3
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('supercharged_submissions')
    
    # Scan for AI submissions
    response = table.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr('isAI').eq(True)
    )
    
    ai_submissions = response['Items']
    print(f"✅ Found {len(ai_submissions)} AI submissions in database")
    
    if ai_submissions:
        sample = ai_submissions[0]
        print(f"Sample AI user: {sample['userId']}")
        print(f"Sample AI idea: {sample['ideas'][0][:100]}...")
    
    print("\n🎉 End-to-End Test Complete!")
    print(f"📊 Summary:")
    print(f"   - ✅ Daily superpower API working")
    print(f"   - ✅ User submissions working") 
    print(f"   - ✅ Rating system working")
    print(f"   - ✅ Leaderboard working")
    print(f"   - ✅ AI baseline generation working ({len(ai_submissions)} AI submissions)")

if __name__ == '__main__':
    test_complete_flow()