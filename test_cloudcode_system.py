#!/usr/bin/env python3

import requests
import json

API_BASE = 'https://gsx73a1w3d.execute-api.us-east-1.amazonaws.com/prod'

def test_next_pair():
    """Test getting next pair for rating"""
    print("🧠 Testing CloudCode next pair API...")
    
    user_id = 'TestCloudUser'
    response = requests.get(f'{API_BASE}/cloudcode/next-pair?userId={user_id}')
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Got next pair successfully!")
        print(f"Idea A: {result['a_text'][:100]}...")
        print(f"Idea B: {result['b_text'][:100]}...")
        print(f"Prior probabilities: {result['prior']}")
        print(f"Ratings remaining: {result['ratings_remaining']}")
        return result
    else:
        print(f"❌ Failed to get next pair: {response.text}")
        return None

def test_submit_rating(pair_data, rating=3):
    """Test submitting a rating"""
    print(f"\n🎯 Testing CloudCode rating submission (rating: {rating})...")
    
    submit_data = {
        'userId': 'TestCloudUser',
        'a_id': pair_data['a_id'],
        'b_id': pair_data['b_id'],
        'rating': rating
    }
    
    response = requests.post(f'{API_BASE}/cloudcode/rate', json=submit_data)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Rating submitted successfully!")
        print(f"Points earned: {result['points']}")
        print(f"Agreement: {result['agreement_pct']}%")
        print(f"Ratings done: {result['ratings_done']}")
        print(f"Ratings remaining: {result['ratings_remaining']}")
        
        if 'next' in result:
            print(f"Next pair ready:")
            print(f"  Idea A: {result['next']['a_text'][:80]}...")
            print(f"  Idea B: {result['next']['b_text'][:80]}...")
        
        return result
    else:
        print(f"❌ Failed to submit rating: {response.text}")
        return None

def test_full_session():
    """Test a complete rating session"""
    print("🚀 Testing complete CloudCode session...")
    
    ratings_completed = 0
    total_points = 0
    
    while ratings_completed < 5:
        # Get next pair
        pair_data = test_next_pair()
        
        if not pair_data:
            break
        
        if pair_data.get('status') == 'limit':
            print("Daily limit reached")
            break
        
        # Submit a rating (random between 2 and 4 for realistic distribution)
        import random
        rating = random.choice([2, 3, 3, 4, 4])  # Weighted toward middle ratings
        
        result = test_submit_rating(pair_data, rating)
        
        if result:
            ratings_completed += 1
            total_points += result['points']
            print(f"Session progress: {ratings_completed}/5 ratings")
        else:
            break
        
        if result.get('status') == 'complete':
            print("Session completed!")
            break
    
    if ratings_completed > 0:
        avg_points = total_points / ratings_completed
        print(f"\n🎉 Session Summary:")
        print(f"Ratings completed: {ratings_completed}")
        print(f"Total points: {total_points}")
        print(f"Average points: {avg_points:.1f}")
        print(f"Estimated accuracy: {avg_points * 0.8:.1f}%")

def main():
    print("🧪 Testing CloudCode System")
    print("=" * 50)
    
    # Test full session
    test_full_session()
    
    print(f"\n✅ CloudCode system testing complete!")
    print(f"Frontend URL: http://localhost:8000/cloudcode.html")

if __name__ == "__main__":
    main()