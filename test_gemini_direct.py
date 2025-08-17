#!/usr/bin/env python3

import requests
import json
import re

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

def call_gemini_api(prompt):
    """Test Gemini API directly"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.9,
            "topP": 0.9,
            "maxOutputTokens": 8000,
        }
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    print("Calling Gemini API...")
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return []
    
    result = response.json()
    print(f"Response structure: {list(result.keys())}")
    
    if 'candidates' not in result or not result['candidates']:
        print("No candidates returned")
        return []
    
    content = result['candidates'][0]['content']['parts'][0]['text']
    print(f"Generated content length: {len(content)} characters")
    print(f"First 500 characters: {content[:500]}...")
    
    # Parse the response to extract ideas
    ideas = parse_gemini_response(content)
    print(f"Parsed {len(ideas)} ideas")
    
    return ideas

def parse_gemini_response(response_text):
    """Parse Gemini response to extract numbered ideas"""
    ideas = []
    
    # Split by numbered patterns (1., 2., 3., etc.)
    pattern = r'(\d+)\.\s*(.+?)(?=\n\d+\.|$)'
    matches = re.findall(pattern, response_text, re.DOTALL)
    
    print(f"Regex found {len(matches)} numbered matches")
    
    for number, idea_text in matches:
        # Clean up the idea text
        idea = idea_text.strip()
        # Remove any extra whitespace and newlines
        idea = ' '.join(idea.split())
        
        if idea and len(idea) > 20:  # Basic validation
            ideas.append(idea)
    
    return ideas[:70]  # Return exactly 70 ideas

def main():
    # Test prompt
    prompt = """Generate 70 creative use cases for the superpower "Perfect Memory" for a competitive creativity game. Each idea should be exactly one paragraph in length.

Superpower Description: You have the ability to remember everything with perfect clarity and recall any information instantly.

Quality Requirements:
- Mechanistically complex: Must exploit specific properties or clever interactions of this superpower
- Realistic: Based on real-world physics and practical applications, could actually work if this power existed
- Novel: Hard to think of, not obvious applications
- Competition-winning: Ideas that would beat other players in a creativity contest
- Practical: Focus on everyday problems and creative solutions

Format Requirements:
- Return exactly 70 ideas
- Each idea must be one complete paragraph (50-100 words)
- Number each idea clearly (1., 2., 3., etc.)
- Focus on the practical mechanism and real-world application

Generate 70 mechanistically clever and practically useful ideas for "Perfect Memory" that demonstrate creative problem-solving and real-world application."""

    ideas = call_gemini_api(prompt)
    
    if ideas:
        print(f"\n✅ SUCCESS: Generated {len(ideas)} ideas")
        print(f"First 3 ideas:")
        for i, idea in enumerate(ideas[:3]):
            print(f"{i+1}. {idea}")
    else:
        print("❌ FAILED: No ideas generated")

if __name__ == '__main__':
    main()