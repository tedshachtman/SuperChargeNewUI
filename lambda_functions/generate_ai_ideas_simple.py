import json
import boto3
import requests
from datetime import datetime
import uuid
import re

dynamodb = boto3.resource('dynamodb')
submissions_table = dynamodb.Table('supercharged_submissions')

GEMINI_API_KEY = "AIzaSyBhCFFPFv_qhhnkKp1GfM2MJ_bM1ZeISpg"

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        superpower_id = body['superpowerId']
        superpower_title = body['superpowerTitle']
        superpower_description = body['superpowerDescription']
        date = body['date']
        
        # Create dynamic prompt
        prompt = f"""Generate 70 creative use cases for the superpower "{superpower_title}" for a competitive creativity game. Each idea should be exactly one paragraph in length.

Superpower Description: {superpower_description}

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

Example of a GOOD idea structure:
"[Mechanism explanation]: [Specific real-world application]: [Why it works]: [Practical benefits or interesting consequences]."

Avoid these BAD approaches:
- Generic or obvious uses
- Impossible sci-fi concepts without realistic basis
- Just using big technical words without real mechanics  
- Ideas that don't cleverly exploit this specific superpower's properties
- Repetitive concepts

Generate 70 mechanistically clever and practically useful ideas for "{superpower_title}" that demonstrate creative problem-solving and real-world application."""

        # Call Gemini API directly via REST
        ideas = call_gemini_api(prompt)
        
        if len(ideas) < 60:  # Allow some tolerance
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                },
                'body': json.dumps({
                    'success': False,
                    'error': f'Only generated {len(ideas)} ideas, expected around 70'
                })
            }
        
        # Store AI ideas in database (in batches of 4 to match user submission format)
        submission_ids = []
        now = datetime.now()
        timestamp = int(now.timestamp())
        
        # Take first 70 ideas and create submissions with 4 ideas each
        ideas = ideas[:70]
        
        for i in range(0, len(ideas), 4):
            batch_ideas = ideas[i:i+4]
            
            # Pad the last batch if necessary
            while len(batch_ideas) < 4:
                batch_ideas.append("AI-generated placeholder idea for this superpower application.")
            
            submission_id = str(uuid.uuid4())
            ai_user_id = f"AI_Generator_{i//4 + 1}"
            
            submission_item = {
                'submissionId': submission_id,
                'userId': ai_user_id,
                'date': date,
                'superpowerId': superpower_id,
                'ideas': batch_ideas,
                'timestamp': timestamp,
                'submittedAt': now.isoformat(),
                'isAI': True,
                'aiModel': 'gemini-2.0-flash-exp',
                'aiPromptVersion': '1.0'
            }
            
            submissions_table.put_item(Item=submission_item)
            submission_ids.append(submission_id)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'ideasGenerated': len(ideas),
                'submissionsCreated': len(submission_ids),
                'submissionIds': submission_ids,
                'message': f'Generated {len(ideas)} AI ideas for {superpower_title}'
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
                'error': str(e),
                'errorType': 'LambdaError'
            })
        }

def call_gemini_api(prompt):
    """Call Gemini API directly via REST"""
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
    
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    
    if response.status_code != 200:
        raise Exception(f"Gemini API error: {response.status_code} - {response.text}")
    
    result = response.json()
    
    if 'candidates' not in result or not result['candidates']:
        raise Exception("No candidates returned from Gemini API")
    
    content = result['candidates'][0]['content']['parts'][0]['text']
    
    # Parse the response to extract ideas
    ideas = parse_gemini_response(content)
    
    return ideas

def parse_gemini_response(response_text):
    """Parse Gemini response to extract numbered ideas"""
    ideas = []
    
    # Split by numbered patterns (1., 2., 3., etc.)
    pattern = r'(\d+)\.\s*(.+?)(?=\n\d+\.|$)'
    matches = re.findall(pattern, response_text, re.DOTALL)
    
    for number, idea_text in matches:
        # Clean up the idea text
        idea = idea_text.strip()
        # Remove any extra whitespace and newlines
        idea = ' '.join(idea.split())
        
        if idea and len(idea) > 20:  # Basic validation
            ideas.append(idea)
    
    # Fallback: if regex doesn't work well, try line-by-line parsing
    if len(ideas) < 50:  # If we didn't get enough ideas
        lines = response_text.split('\n')
        ideas = []
        current_idea = ""
        
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\.', line):  # Start of new numbered idea
                if current_idea:
                    ideas.append(' '.join(current_idea.split()))
                current_idea = re.sub(r'^\d+\.\s*', '', line)
            elif line and current_idea:  # Continuation of current idea
                current_idea += " " + line
        
        # Add the last idea
        if current_idea:
            ideas.append(' '.join(current_idea.split()))
    
    return ideas[:70]  # Return exactly 70 ideas