#!/usr/bin/env python3

import json
import boto3
import sys
import os
import math
from decimal import Decimal
from datetime import date

# Add the parent directory to Python path for imports
sys.path.append('/opt')

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    try:
        # Import core functionality
        from cloudcode_core_lambda import CloudCodeCore, MAX_RATINGS_PER_DAY, NO_REPEAT_WINDOW
        
        # Parse request body
        if event.get('body'):
            body = json.loads(event['body'])
        else:
            body = event
        
        user_id = body.get('userId')
        a_id = body.get('a_id')
        b_id = body.get('b_id')
        rating = body.get('rating')
        
        if not all([user_id, a_id, b_id, rating]):
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'userId, a_id, b_id, and rating are required'})
            }
        
        if rating not in [1, 2, 3, 4, 5]:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Rating must be 1, 2, 3, 4, or 5'})
            }
        
        core = CloudCodeCore()
        today = date.today().isoformat()
        
        # Load session
        session = core.load_or_init_session(user_id, today)
        
        # Check daily limit
        if session.get('ratings_done', 0) >= MAX_RATINGS_PER_DAY:
            return {
                'statusCode': 403,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': f'Daily limit of {MAX_RATINGS_PER_DAY} ratings reached'})
            }
        
        # Get predictive prior (before updating)
        prior_probs = core.predictive_prior(a_id, b_id)
        
        # Calculate points and agreement
        pr = prior_probs[rating - 1]  # Convert 1-5 rating to 0-4 index
        points = max(0, 100 * (1 + math.log(pr) / math.log(5))) if pr > 0 else 0
        agreement_pct = round(100 * pr)
        
        # Update pair statistics
        core.update_pair_stats(a_id, b_id, rating)
        
        # Update session
        session['ratings_done'] = session.get('ratings_done', 0) + 1
        session['last_anchor_id'] = b_id  # Sticky chain
        recent_ids = session.get('recent_ids', [])
        session['recent_ids'] = core.push_fifo(recent_ids, [a_id, b_id], NO_REPEAT_WINDOW)
        core.save_session(session)
        
        # Get next pair
        next_pair = None
        if session['ratings_done'] < MAX_RATINGS_PER_DAY:
            # Get next pair using the same logic as next_pair endpoint
            anchor_a = session['last_anchor_id']
            neighbor_b = core.pick_neighbor(anchor_a, session['recent_ids'])
            
            if not neighbor_b:
                # Chain hit dead end, pick new start
                anchor_a = core.pick_start(exclude_user_id=user_id)
                if anchor_a:
                    neighbor_b = core.pick_neighbor(anchor_a, session['recent_ids'])
            
            if neighbor_b:
                # Update session for next pair
                session['last_anchor_id'] = neighbor_b
                session['recent_ids'] = core.push_fifo(session['recent_ids'], [anchor_a, neighbor_b], NO_REPEAT_WINDOW)
                core.save_session(session)
                
                # Increment exposure for next pair
                core.increment_exposure(anchor_a)
                core.increment_exposure(neighbor_b)
                
                # Get predictive prior for next pair
                next_prior_probs = core.predictive_prior(anchor_a, neighbor_b)
                next_prior_dict = {
                    'p1': next_prior_probs[0],
                    'p2': next_prior_probs[1],
                    'p3': next_prior_probs[2],
                    'p4': next_prior_probs[3],
                    'p5': next_prior_probs[4]
                }
                
                # Get idea texts for next pair
                idea_a_text = "Unknown idea"
                idea_b_text = "Unknown idea"
                
                try:
                    response_a = core.ideas_table.get_item(Key={'idea_id': anchor_a})
                    if 'Item' in response_a:
                        idea_a_text = response_a['Item'].get('text', 'Unknown idea')
                except:
                    pass
                
                try:
                    response_b = core.ideas_table.get_item(Key={'idea_id': neighbor_b})
                    if 'Item' in response_b:
                        idea_b_text = response_b['Item'].get('text', 'Unknown idea')
                except:
                    pass
                
                next_pair = {
                    'a_id': anchor_a,
                    'b_id': neighbor_b,
                    'a_text': idea_a_text,
                    'b_text': idea_b_text,
                    'prior': next_prior_dict
                }
        
        response_data = {
            'points': round(points),
            'agreement_pct': agreement_pct,
            'ratings_done': session['ratings_done'],
            'ratings_remaining': MAX_RATINGS_PER_DAY - session['ratings_done']
        }
        
        if next_pair:
            response_data['next'] = next_pair
        else:
            response_data['status'] = 'complete'
            response_data['message'] = f'Daily limit of {MAX_RATINGS_PER_DAY} ratings reached'
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(response_data, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': f'Internal error: {str(e)}'})
        }