#!/usr/bin/env python3

import json
import boto3
import sys
import os
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
        
        # Parse request
        user_id = event.get('queryStringParameters', {}).get('userId')
        if not user_id:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'userId parameter required'})
            }
        
        core = CloudCodeCore()
        today = date.today().isoformat()
        
        # Load or initialize session
        session = core.load_or_init_session(user_id, today)
        
        # Check daily limit
        if session.get('ratings_done', 0) >= MAX_RATINGS_PER_DAY:
            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'status': 'limit', 'message': f'Daily limit of {MAX_RATINGS_PER_DAY} ratings reached'})
            }
        
        # Determine anchor A
        anchor_a = session.get('last_anchor_id')
        if not anchor_a:
            anchor_a = core.pick_start(exclude_user_id=user_id)
        
        if not anchor_a:
            return {
                'statusCode': 404,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'No suitable ideas available'})
            }
        
        # Pick neighbor B
        recent_ids = session.get('recent_ids', [])
        neighbor_b = core.pick_neighbor(anchor_a, recent_ids)
        
        if not neighbor_b:
            # Chain hit dead end, pick new start
            anchor_a = core.pick_start(exclude_user_id=user_id)
            if anchor_a:
                neighbor_b = core.pick_neighbor(anchor_a, recent_ids)
        
        if not neighbor_b:
            return {
                'statusCode': 404,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'No suitable neighbors found'})
            }
        
        # Update session
        session['last_anchor_id'] = neighbor_b
        session['recent_ids'] = core.push_fifo(recent_ids, [anchor_a, neighbor_b], NO_REPEAT_WINDOW)
        core.save_session(session)
        
        # Increment exposure
        core.increment_exposure(anchor_a)
        core.increment_exposure(neighbor_b)
        
        # Get predictive prior
        prior_probs = core.predictive_prior(anchor_a, neighbor_b)
        prior_dict = {
            'p1': prior_probs[0],
            'p2': prior_probs[1],
            'p3': prior_probs[2],
            'p4': prior_probs[3],
            'p5': prior_probs[4]
        }
        
        # Get idea texts
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
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'a_id': anchor_a,
                'b_id': neighbor_b,
                'a_text': idea_a_text,
                'b_text': idea_b_text,
                'prior': prior_dict,
                'ratings_done': session.get('ratings_done', 0),
                'ratings_remaining': MAX_RATINGS_PER_DAY - session.get('ratings_done', 0)
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': f'Internal error: {str(e)}'})
        }