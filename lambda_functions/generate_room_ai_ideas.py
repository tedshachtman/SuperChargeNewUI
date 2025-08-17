#!/usr/bin/env python3

import json
import boto3
import uuid
import time
import requests
import os

def lambda_handler(event, context):
    try:
        # Parse input
        room_id = event.get('roomId')
        superpower = event.get('superpower')
        
        if not room_id or not superpower:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'roomId and superpower are required'})
            }
        
        # Generate AI ideas using Gemini
        ai_ideas = generate_ai_ideas(superpower)
        
        if not ai_ideas:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to generate AI ideas'})
            }
        
        # Store AI ideas as submissions
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        submissions_table = dynamodb.Table('supercharged_submissions')
        
        # Create AI submissions (18 submissions with 4 ideas each = 72 total ideas)
        ai_submissions_created = 0
        current_time = int(time.time())
        
        for i in range(18):  # 18 AI users
            ai_user_id = f"AI_Room_Generator_{i+1}"
            submission_id = str(uuid.uuid4())
            
            # Get 4 ideas for this submission
            start_idx = i * 4
            end_idx = start_idx + 4
            submission_ideas = ai_ideas[start_idx:end_idx] if end_idx <= len(ai_ideas) else ai_ideas[start_idx:]
            
            # Pad with generic ideas if needed
            while len(submission_ideas) < 4:
                submission_ideas.append(f"Creative application #{len(submission_ideas) + 1} for {superpower['title']}")
            
            submission_data = {
                'submissionId': submission_id,
                'userId': ai_user_id,
                'roomId': room_id,  # Key difference - room-specific
                'superpowerId': room_id,  # Use room ID as superpower ID for rooms
                'ideas': submission_ideas,
                'timestamp': current_time,
                'submittedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'isAI': True,
                'aiModel': 'gemini-2.0-flash-exp',
                'aiPromptVersion': '1.0'
            }
            
            submissions_table.put_item(Item=submission_data)
            ai_submissions_created += 1
        
        # Update room to mark AI ideas as generated
        rooms_table = dynamodb.Table('supercharged_rooms')
        rooms_table.update_item(
            Key={'roomId': room_id},
            UpdateExpression='SET aiIdeasGenerated = :flag',
            ExpressionAttributeValues={':flag': True}
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Generated {ai_submissions_created} AI submissions for room {room_id}',
                'totalAIIdeas': len(ai_ideas),
                'aiSubmissions': ai_submissions_created
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Failed to generate room AI ideas: {str(e)}'})
        }

def generate_ai_ideas(superpower):
    """Generate AI ideas using Gemini API"""
    try:
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Create dynamic prompt
        prompt = f"""Generate 70 creative use cases for the superpower "{superpower['title']}" for a competitive creativity game.

Superpower Description: {superpower['description']}

Quality Requirements:
- Mechanistically complex: Must exploit specific properties or clever interactions of this superpower
- Realistic: Based on real-world physics and practical applications, could actually work if this power existed
- Novel: Hard to think of, not obvious applications
- Competition-winning: Ideas that would beat other players in a creativity contest
- Practical: Focus on everyday problems and creative solutions

Format Requirements:
- Each idea should be 1-3 sentences
- Focus on the HOW and WHY it works
- Include specific details about implementation
- Avoid obvious or simple applications
- Prioritize mechanical ingenuity over raw power

Please provide exactly 70 distinct, creative applications as a numbered list."""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=300)
        response.raise_for_status()
        
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            content = result['candidates'][0]['content']['parts'][0]['text']
            
            # Parse the numbered list
            ideas = []
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('**')):
                    # Remove numbering and formatting
                    cleaned_line = line
                    if '. ' in cleaned_line:
                        cleaned_line = cleaned_line.split('. ', 1)[1]
                    cleaned_line = cleaned_line.replace('**', '').strip()
                    
                    if len(cleaned_line) > 20:  # Filter out very short lines
                        ideas.append(cleaned_line)
                        
                        if len(ideas) >= 70:
                            break
            
            print(f"Generated {len(ideas)} AI ideas for room")
            return ideas[:70]  # Return exactly 70 ideas
        
        return []
        
    except Exception as e:
        print(f"Gemini API error: {str(e)}")
        return []