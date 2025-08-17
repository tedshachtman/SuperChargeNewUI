#!/usr/bin/env python3

import boto3
import json
import math
import random
from decimal import Decimal
from typing import List, Dict, Tuple, Optional
from datetime import datetime, date

# Configuration constants
K = 100  # neighbors cached per idea
AMBIG_BAND = [0.20, 0.70]  # percentile band on A's neighbor list
MAX_RATINGS_PER_DAY = 5  # per user
NO_REPEAT_WINDOW = 10  # avoid re-showing recent ideas
DIRICHLET_CONFIDENCE = 3.0  # c parameter for prior strength

class CloudCodeCore:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.ideas_table = self.dynamodb.Table('cloudcode_ideas')
        self.neighbors_table = self.dynamodb.Table('cloudcode_idea_neighbors')
        self.pair_stats_table = self.dynamodb.Table('cloudcode_pair_stats')
        self.user_session_table = self.dynamodb.Table('cloudcode_user_session')
        
        # Cold-start default distribution mapping
        self.default_q_mapping = {
            0.10: [0.40, 0.30, 0.20, 0.08, 0.02],
            0.30: [0.25, 0.25, 0.30, 0.15, 0.05],
            0.50: [0.12, 0.20, 0.36, 0.24, 0.08],
            0.70: [0.05, 0.10, 0.25, 0.35, 0.25],
            0.85: [0.02, 0.05, 0.18, 0.35, 0.40]
        }
    
    def decimal_default(self, obj):
        """JSON serializer for Decimal objects"""
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError
    
    def interpolate_q_of_s(self, cosine_sim: float) -> List[float]:
        """Interpolate 5-bucket distribution from cosine similarity"""
        s = max(0.0, min(1.0, cosine_sim))  # Clamp to [0,1]
        
        # Find the two closest points in our mapping
        sorted_points = sorted(self.default_q_mapping.keys())
        
        if s <= sorted_points[0]:
            return self.default_q_mapping[sorted_points[0]]
        if s >= sorted_points[-1]:
            return self.default_q_mapping[sorted_points[-1]]
        
        # Find surrounding points
        lower_s = None
        upper_s = None
        
        for point in sorted_points:
            if point <= s:
                lower_s = point
            elif point > s and upper_s is None:
                upper_s = point
                break
        
        if lower_s is None or upper_s is None:
            return self.default_q_mapping[sorted_points[len(sorted_points)//2]]
        
        # Linear interpolation
        alpha = (s - lower_s) / (upper_s - lower_s)
        lower_q = self.default_q_mapping[lower_s]
        upper_q = self.default_q_mapping[upper_s]
        
        result = []
        for i in range(5):
            interpolated = lower_q[i] * (1 - alpha) + upper_q[i] * alpha
            result.append(interpolated)
        
        return result
    
    def get_cosine_similarity(self, idea_a: str, idea_b: str) -> float:
        """Get cosine similarity between two ideas from cache or compute"""
        # Try to find in neighbors cache
        try:
            response = self.neighbors_table.get_item(
                Key={'idea_id': idea_a, 'neighbor_id': idea_b}
            )
            if 'Item' in response:
                return float(response['Item']['cosine_sim'])
            
            # Try reverse direction
            response = self.neighbors_table.get_item(
                Key={'idea_id': idea_b, 'neighbor_id': idea_a}
            )
            if 'Item' in response:
                return float(response['Item']['cosine_sim'])
        except Exception as e:
            print(f"Error getting cached similarity: {str(e)}")
        
        # If not found in cache, return default moderate similarity
        return 0.5
    
    def predictive_prior(self, idea_a: str, idea_b: str) -> List[float]:
        """Compute predictive prior for rating pair (A,B)"""
        # Canonicalize pair order
        lo, hi = sorted([idea_a, idea_b])
        
        # Get cosine similarity
        cosine_sim = self.get_cosine_similarity(lo, hi)
        
        # Get base distribution from cosine similarity
        q = self.interpolate_q_of_s(cosine_sim)
        
        # Apply Dirichlet prior
        alpha0 = [DIRICHLET_CONFIDENCE * x for x in q]
        
        # Load existing human ratings if any
        pair_key = f"{lo}#{hi}"
        try:
            response = self.pair_stats_table.get_item(Key={'pair_key': pair_key})
            if 'Item' in response:
                item = response['Item']
                counts = [
                    float(item.get('n1', 0)),
                    float(item.get('n2', 0)),
                    float(item.get('n3', 0)),
                    float(item.get('n4', 0)),
                    float(item.get('n5', 0))
                ]
            else:
                counts = [0.0, 0.0, 0.0, 0.0, 0.0]
        except:
            counts = [0.0, 0.0, 0.0, 0.0, 0.0]
        
        # Compute posterior
        alpha = [a0 + n for a0, n in zip(alpha0, counts)]
        total = sum(alpha)
        p = [a / total for a in alpha]
        
        return p
    
    def load_or_init_session(self, user_id: str, day: str) -> Dict:
        """Load or initialize user session for the day"""
        try:
            response = self.user_session_table.get_item(
                Key={'user_id': user_id, 'day': day}
            )
            if 'Item' in response:
                return response['Item']
        except:
            pass
        
        # Initialize new session
        session = {
            'user_id': user_id,
            'day': day,
            'ratings_done': 0,
            'last_anchor_id': None,
            'recent_ids': []
        }
        
        self.user_session_table.put_item(Item=session)
        return session
    
    def save_session(self, session: Dict):
        """Save user session"""
        self.user_session_table.put_item(Item=session)
    
    def pick_start(self, exclude_user_id: str = None) -> Optional[str]:
        """Pick starting idea with low exposure"""
        try:
            # Query ideas with low exposure
            response = self.ideas_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('status').eq('kept') &
                               boto3.dynamodb.conditions.Attr('exposure').lte(5)
            )
            
            candidates = response.get('Items', [])
            
            # Filter out user's own ideas
            if exclude_user_id:
                candidates = [item for item in candidates 
                            if item.get('author_user_id') != exclude_user_id]
            
            if not candidates:
                # Fall back to any kept ideas
                response = self.ideas_table.scan(
                    FilterExpression=boto3.dynamodb.conditions.Attr('status').eq('kept')
                )
                candidates = response.get('Items', [])
                
                if exclude_user_id:
                    candidates = [item for item in candidates 
                                if item.get('author_user_id') != exclude_user_id]
            
            if candidates:
                # Sort by exposure (ascending) and pick randomly among lowest
                candidates.sort(key=lambda x: x.get('exposure', 0))
                min_exposure = candidates[0].get('exposure', 0)
                lowest_exposure = [c for c in candidates if c.get('exposure', 0) == min_exposure]
                return random.choice(lowest_exposure)['idea_id']
            
        except Exception as e:
            print(f"Error in pick_start: {str(e)}")
        
        return None
    
    def percentile(self, values: List[float], p: float) -> float:
        """Compute percentile of values"""
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        index = (len(sorted_vals) - 1) * p / 100.0
        lower = int(index)
        upper = min(lower + 1, len(sorted_vals) - 1)
        weight = index - lower
        return sorted_vals[lower] * (1 - weight) + sorted_vals[upper] * weight
    
    def pick_neighbor(self, anchor_id: str, recent_ids: List[str]) -> Optional[str]:
        """Pick neighbor from ambiguous similarity band"""
        try:
            # Load neighbors for anchor
            response = self.neighbors_table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('idea_id').eq(anchor_id)
            )
            
            neighbors = response.get('Items', [])
            
            if not neighbors:
                return None
            
            # Extract similarities and compute percentiles
            similarities = [float(n['cosine_sim']) for n in neighbors]
            lo_percentile = self.percentile(similarities, AMBIG_BAND[0] * 100)
            hi_percentile = self.percentile(similarities, AMBIG_BAND[1] * 100)
            
            # Filter candidates
            candidates = []
            for neighbor in neighbors:
                neighbor_id = neighbor['neighbor_id']
                cosine_sim = float(neighbor['cosine_sim'])
                
                # Check similarity band
                if not (lo_percentile <= cosine_sim <= hi_percentile):
                    continue
                
                # Check not in recent
                if neighbor_id in recent_ids:
                    continue
                
                # Check if neighbor is kept
                try:
                    idea_response = self.ideas_table.get_item(Key={'idea_id': neighbor_id})
                    if 'Item' not in idea_response:
                        continue
                    if idea_response['Item'].get('status') != 'kept':
                        continue
                except:
                    continue
                
                candidates.append((neighbor_id, cosine_sim))
            
            if not candidates:
                # Widen the band
                lo_percentile = self.percentile(similarities, 10)
                hi_percentile = self.percentile(similarities, 90)
                
                for neighbor in neighbors:
                    neighbor_id = neighbor['neighbor_id']
                    cosine_sim = float(neighbor['cosine_sim'])
                    
                    if not (lo_percentile <= cosine_sim <= hi_percentile):
                        continue
                    if neighbor_id in recent_ids:
                        continue
                    
                    try:
                        idea_response = self.ideas_table.get_item(Key={'idea_id': neighbor_id})
                        if 'Item' not in idea_response:
                            continue
                        if idea_response['Item'].get('status') != 'kept':
                            continue
                    except:
                        continue
                    
                    candidates.append((neighbor_id, cosine_sim))
            
            if candidates:
                # Pick highest cosine similarity (greedy)
                best_neighbor = max(candidates, key=lambda x: x[1])
                return best_neighbor[0]
            
        except Exception as e:
            print(f"Error in pick_neighbor: {str(e)}")
        
        return None
    
    def increment_exposure(self, idea_id: str):
        """Increment exposure count for an idea"""
        try:
            self.ideas_table.update_item(
                Key={'idea_id': idea_id},
                UpdateExpression='ADD exposure :inc',
                ExpressionAttributeValues={':inc': 1}
            )
        except Exception as e:
            print(f"Error incrementing exposure for {idea_id}: {str(e)}")
    
    def update_pair_stats(self, idea_a: str, idea_b: str, rating: int):
        """Update rating statistics for a pair"""
        lo, hi = sorted([idea_a, idea_b])
        pair_key = f"{lo}#{hi}"
        
        try:
            # Get current stats or create new
            response = self.pair_stats_table.get_item(Key={'pair_key': pair_key})
            
            if 'Item' in response:
                item = response['Item']
                n1 = float(item.get('n1', 0))
                n2 = float(item.get('n2', 0))
                n3 = float(item.get('n3', 0))
                n4 = float(item.get('n4', 0))
                n5 = float(item.get('n5', 0))
            else:
                n1 = n2 = n3 = n4 = n5 = 0.0
            
            # Increment the appropriate rating bucket
            if rating == 1:
                n1 += 1.0
            elif rating == 2:
                n2 += 1.0
            elif rating == 3:
                n3 += 1.0
            elif rating == 4:
                n4 += 1.0
            elif rating == 5:
                n5 += 1.0
            
            # Calculate mean
            total_ratings = n1 + n2 + n3 + n4 + n5
            if total_ratings > 0:
                mean = (1*n1 + 2*n2 + 3*n3 + 4*n4 + 5*n5) / total_ratings
            else:
                mean = 3.0
            
            # Update the record
            self.pair_stats_table.put_item(Item={
                'pair_key': pair_key,
                'a_id': lo,
                'b_id': hi,
                'n1': Decimal(str(n1)),
                'n2': Decimal(str(n2)),
                'n3': Decimal(str(n3)),
                'n4': Decimal(str(n4)),
                'n5': Decimal(str(n5)),
                'mean': Decimal(str(mean)),
                'last_rating_at': datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"Error updating pair stats: {str(e)}")
    
    def push_fifo(self, recent_ids: List[str], new_ids: List[str], max_size: int) -> List[str]:
        """Add new IDs to FIFO list with size limit"""
        combined = recent_ids + new_ids
        return combined[-max_size:] if len(combined) > max_size else combined