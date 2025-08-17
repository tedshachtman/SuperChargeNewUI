#!/usr/bin/env python3

import requests
import json
import time

# Test the new embedding-based scoring system
API_BASE = 'https://gsx73a1w3d.execute-api.us-east-1.amazonaws.com/prod'

def test_embedding_scoring():
    print("🧪 Testing Embedding-Based Rating Accuracy System")
    print("=" * 60)
    
    # Test user
    user_id = "TestEmbeddingUser"
    
    # Test ideas with different similarity levels
    test_cases = [
        {
            "name": "High Similarity Test",
            "ideas1": [
                "Use perfect memory to become the world's best detective by remembering every clue",
                "Memorize all medical knowledge to become an expert doctor",
                "Remember every law and legal precedent to become a top lawyer", 
                "Store all historical facts to become the ultimate history teacher"
            ],
            "ideas2": [
                "Solve crimes by perfectly recalling every piece of evidence",
                "Practice medicine with complete recall of all medical literature",
                "Win court cases by remembering every legal case ever tried",
                "Teach students by recalling every historical event in detail"
            ]
        },
        {
            "name": "Medium Similarity Test", 
            "ideas1": [
                "Use perfect memory to learn every language instantly",
                "Memorize stock market patterns to predict trends",
                "Remember everyone's names and details for perfect networking",
                "Store musical compositions to become a master composer"
            ],
            "ideas2": [
                "Recall every conversation to improve relationships",
                "Remember investment patterns for financial success",
                "Never forget important dates and appointments",
                "Memorize recipes to become a world-class chef"
            ]
        },
        {
            "name": "Low Similarity Test",
            "ideas1": [
                "Use perfect memory to remember passwords and never get locked out",
                "Memorize everyone's birthday to always send cards on time",
                "Remember where you put your keys so you never lose them",
                "Store phone numbers so you don't need to look them up"
            ],
            "ideas2": [
                "Become a time traveler by somehow using memory powers",
                "Use memory to fly like Superman across the sky",
                "Transform into animals using perfect recall abilities",
                "Shoot laser beams from eyes powered by memory"
            ]
        }
    ]
    
    print(f"🚀 Testing with user: {user_id}")
    print(f"📊 Will test {len(test_cases)} similarity scenarios\n")
    
    # Submit all test cases
    submission_ids = []
    for i, test_case in enumerate(test_cases):
        print(f"📝 Submitting {test_case['name']} - Set 1...")
        
        # Submit first set of ideas
        response1 = requests.post(f"{API_BASE}/submit", json={
            "userId": f"{user_id}_Set1_{i}",
            "superpowerId": "embedding-test",
            "ideas": test_case["ideas1"]
        })
        
        if response1.status_code == 200:
            result1 = response1.json()
            submission_ids.append((result1["submissionId"], test_case["name"] + " Set 1"))
            print(f"✅ Submitted Set 1: {result1['submissionId']}")
        else:
            print(f"❌ Failed to submit Set 1: {response1.text}")
            continue
            
        # Wait a moment for embeddings to process
        time.sleep(2)
        
        print(f"📝 Submitting {test_case['name']} - Set 2...")
        
        # Submit second set of ideas
        response2 = requests.post(f"{API_BASE}/submit", json={
            "userId": f"{user_id}_Set2_{i}",
            "superpowerId": "embedding-test", 
            "ideas": test_case["ideas2"]
        })
        
        if response2.status_code == 200:
            result2 = response2.json()
            submission_ids.append((result2["submissionId"], test_case["name"] + " Set 2"))
            print(f"✅ Submitted Set 2: {result2['submissionId']}")
            print()
        else:
            print(f"❌ Failed to submit Set 2: {response2.text}")
    
    print(f"📊 Created {len(submission_ids)} test submissions")
    print("\n⏳ Waiting for embeddings to be generated...")
    time.sleep(5)
    
    # Now test ratings between different similarity pairs
    print("\n🎯 Testing Rating Accuracy Scoring:")
    print("-" * 40)
    
    test_ratings = [
        {"rating": 5, "description": "Rating very similar ideas as 5 (should be accurate)"},
        {"rating": 3, "description": "Rating medium similar ideas as 3 (should be accurate)"},
        {"rating": 1, "description": "Rating very different ideas as 1 (should be accurate)"},
        {"rating": 5, "description": "Rating very different ideas as 5 (should be inaccurate)"},
        {"rating": 1, "description": "Rating very similar ideas as 1 (should be inaccurate)"}
    ]
    
    # Test each rating scenario if we have enough submissions
    if len(submission_ids) >= 6:
        for i, test_rating in enumerate(test_ratings):
            print(f"\n{i+1}. {test_rating['description']}")
            
            # Pick appropriate pair based on test case
            if i < 3:  # Accurate ratings
                if i == 0:  # High similarity, rate 5
                    sub1, sub2 = submission_ids[0][0], submission_ids[1][0]  # High similarity pair
                elif i == 1:  # Medium similarity, rate 3  
                    sub1, sub2 = submission_ids[2][0], submission_ids[3][0]  # Medium similarity pair
                else:  # Low similarity, rate 1
                    sub1, sub2 = submission_ids[4][0], submission_ids[5][0]  # Low similarity pair
            else:  # Inaccurate ratings
                if i == 3:  # Low similarity, rate 5 (wrong)
                    sub1, sub2 = submission_ids[4][0], submission_ids[5][0]  # Low similarity pair
                else:  # High similarity, rate 1 (wrong)
                    sub1, sub2 = submission_ids[0][0], submission_ids[1][0]  # High similarity pair
            
            response = requests.post(f"{API_BASE}/rating", json={
                "userId": f"{user_id}_Rater_{i}",
                "submissionId1": sub1,
                "submissionId2": sub2,
                "rating": test_rating["rating"]
            })
            
            if response.status_code == 200:
                result = response.json()
                if "feedback" in result:
                    feedback = result["feedback"]
                    print(f"   User rated: {feedback['userRating']}/5")
                    print(f"   AI expected: {feedback['expectedRating']}/5") 
                    print(f"   Embedding similarity: {feedback['embeddingSimilarity']:.3f}")
                    print(f"   Accuracy score: {feedback['accuracyScore']}%")
                    
                    # Evaluate if this makes sense
                    if feedback["accuracyScore"] >= 75:
                        print(f"   ✅ Good accuracy score!")
                    elif feedback["accuracyScore"] >= 50:
                        print(f"   ⚠️  Moderate accuracy score")
                    else:
                        print(f"   ❌ Low accuracy score")
                else:
                    print(f"   ⚠️  No feedback received (embeddings may not be ready)")
            else:
                print(f"   ❌ Rating failed: {response.text}")
    
    print(f"\n🎉 Embedding scoring system test complete!")
    print(f"\n📖 Test Summary:")
    print(f"   • Users should get high accuracy scores (75-100%) when their ratings match AI expectations")
    print(f"   • Users should get low accuracy scores (0-50%) when their ratings differ significantly")
    print(f"   • The system provides immediate feedback after each rating")
    print(f"   • This scales much better than consensus-based scoring!")

if __name__ == "__main__":
    test_embedding_scoring()