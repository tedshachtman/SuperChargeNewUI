#!/usr/bin/env python3

import boto3
import json
import numpy as np
import requests
import time
from decimal import Decimal
from typing import List, Dict, Tuple
from collections import defaultdict
import uuid

# Configuration
K = 100  # neighbors cached per idea
KEEP_FRACTION = 0.50  # keep top 50% of ideas by novelty
EMBEDDING_MODEL = "text-embedding-3-large"

class CloudCodeOfflineJobs:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.submissions_table = self.dynamodb.Table('supercharged_submissions')
        self.ideas_table = self.dynamodb.Table('cloudcode_ideas')
        self.neighbors_table = self.dynamodb.Table('cloudcode_idea_neighbors')
        self.gemini_api_key = os.environ.get('GEMINI_API_KEY')
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding using a simple method for demo purposes"""
        # For the demo, we'll create a simple hash-based embedding
        # In production, you'd use a proper embedding model
        import hashlib
        
        # Create a simple 768-dimensional vector based on text
        hash_obj = hashlib.sha256(text.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Convert hash to vector
        vector = []
        for i in range(0, len(hash_hex), 4):
            chunk = hash_hex[i:i+4]
            val = int(chunk, 16) / 65535.0 - 0.5  # Normalize to [-0.5, 0.5]
            vector.append(val)
        
        # Pad or truncate to 768 dimensions
        while len(vector) < 768:
            vector.append(0.0)
        vector = vector[:768]
        
        return vector
    
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors"""
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def extract_ideas_from_submissions(self):
        """Step 1: Extract individual ideas from submissions and compute embeddings"""
        print("🔍 Extracting ideas from submissions...")
        
        # Scan all submissions
        response = self.submissions_table.scan()
        submissions = response.get('Items', [])
        
        # Continue scanning if there are more items
        while 'LastEvaluatedKey' in response:
            response = self.submissions_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            submissions.extend(response.get('Items', []))
        
        print(f"Found {len(submissions)} submissions")
        
        idea_count = 0
        batch_write_items = []
        
        for submission in submissions:
            user_id = submission.get('userId', 'unknown')
            is_ai = submission.get('isAI', False)
            
            # Skip AI submissions for human rating
            if is_ai:
                continue
                
            ideas = submission.get('ideas', [])
            
            for idea_text in ideas:
                if not idea_text or len(idea_text.strip()) < 10:
                    continue  # Skip very short ideas
                
                idea_id = str(uuid.uuid4())
                
                # Get embedding
                print(f"Getting embedding for idea {idea_count + 1}: {idea_text[:50]}...")
                embedding = self.get_embedding(idea_text)
                
                if embedding:
                    item = {
                        'idea_id': idea_id,
                        'author_user_id': user_id,
                        'text': idea_text,
                        'embed_version': EMBEDDING_MODEL,
                        'vector': [Decimal(str(v)) for v in embedding],  # Convert to Decimal
                        'novelty_score': Decimal('0.0'),  # Will compute later
                        'novelty_rank': 0,     # Will compute later
                        'status': 'pending',   # Will set to kept/filtered later
                        'exposure': 0,
                        'last_shown_at': None
                    }
                    
                    batch_write_items.append({'PutRequest': {'Item': item}})
                    idea_count += 1
                    
                    # Batch write every 25 items
                    if len(batch_write_items) >= 25:
                        self.ideas_table.batch_writer().write_batch(batch_write_items)
                        batch_write_items = []
                        
                # Small delay for demo
                time.sleep(0.1)
        
        # Write remaining items
        if batch_write_items:
            with self.ideas_table.batch_writer() as batch:
                for item in batch_write_items:
                    batch.put_item(Item=item['PutRequest']['Item'])
        
        print(f"✅ Extracted and embedded {idea_count} ideas")
        return idea_count
    
    def compute_novelty_scores(self):
        """Step 2: Compute novelty scores for all ideas"""
        print("🧮 Computing novelty scores...")
        
        # Load all ideas
        response = self.ideas_table.scan()
        ideas = response.get('Items', [])
        
        while 'LastEvaluatedKey' in response:
            response = self.ideas_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            ideas.extend(response.get('Items', []))
        
        print(f"Computing novelty for {len(ideas)} ideas")
        
        # Convert embeddings to numpy arrays
        embeddings = {}
        for idea in ideas:
            idea_id = idea['idea_id']
            vector = idea['vector']
            # Convert Decimal to float
            vector_floats = [float(v) for v in vector]
            embeddings[idea_id] = np.array(vector_floats)
        
        idea_ids = list(embeddings.keys())
        novelty_scores = {}
        
        # For each idea, sample M other ideas and compute novelty
        M = min(200, len(ideas) - 1)  # Sample size
        
        for i, idea_id in enumerate(idea_ids):
            if i % 50 == 0:
                print(f"Processing idea {i+1}/{len(idea_ids)}")
            
            current_embedding = embeddings[idea_id]
            
            # Sample M other ideas
            other_ids = [id for id in idea_ids if id != idea_id]
            if len(other_ids) > M:
                sample_ids = np.random.choice(other_ids, M, replace=False)
            else:
                sample_ids = other_ids
            
            # Compute similarities
            similarities = []
            for other_id in sample_ids:
                other_embedding = embeddings[other_id]
                sim = self.cosine_similarity(current_embedding, other_embedding)
                similarities.append(sim)
            
            # Take top-10 similarities and compute novelty
            similarities.sort(reverse=True)
            top_p = similarities[:min(10, len(similarities))]
            novelty_score = 1.0 - (sum(top_p) / len(top_p))
            
            novelty_scores[idea_id] = novelty_score
        
        # Rank by novelty score
        sorted_ideas = sorted(novelty_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Update ideas with novelty scores and status
        keep_count = int(len(sorted_ideas) * KEEP_FRACTION)
        
        batch_updates = []
        for rank, (idea_id, score) in enumerate(sorted_ideas):
            status = 'kept' if rank < keep_count else 'filtered'
            
            # Update the idea
            self.ideas_table.update_item(
                Key={'idea_id': idea_id},
                UpdateExpression='SET novelty_score = :score, novelty_rank = :rank, #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':score': Decimal(str(score)),
                    ':rank': rank,
                    ':status': status
                }
            )
            
            if rank % 50 == 0:
                print(f"Updated {rank+1}/{len(sorted_ideas)} ideas")
        
        print(f"✅ Computed novelty scores. Kept {keep_count}/{len(sorted_ideas)} ideas")
        return keep_count
    
    def precompute_neighbors(self):
        """Step 3: Precompute top-K neighbors for each kept idea"""
        print("🔗 Precomputing neighbors...")
        
        # Load all kept ideas
        response = self.ideas_table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('status').eq('kept')
        )
        kept_ideas = response.get('Items', [])
        
        while 'LastEvaluatedKey' in response:
            response = self.ideas_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('status').eq('kept'),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            kept_ideas.extend(response.get('Items', []))
        
        print(f"Computing neighbors for {len(kept_ideas)} kept ideas")
        
        # Convert to embeddings dict
        embeddings = {}
        for idea in kept_ideas:
            idea_id = idea['idea_id']
            vector = idea['vector']
            # Convert Decimal to float
            vector_floats = [float(v) for v in vector]
            embeddings[idea_id] = np.array(vector_floats)
        
        idea_ids = list(embeddings.keys())
        
        # Clear existing neighbors
        print("Clearing existing neighbors...")
        with self.neighbors_table.batch_writer() as batch:
            response = self.neighbors_table.scan()
            for item in response.get('Items', []):
                batch.delete_item(Key={
                    'idea_id': item['idea_id'],
                    'neighbor_id': item['neighbor_id']
                })
        
        # For each idea, compute similarities to all others
        neighbor_batch = []
        
        for i, idea_id in enumerate(idea_ids):
            if i % 10 == 0:
                print(f"Computing neighbors for idea {i+1}/{len(idea_ids)}")
            
            current_embedding = embeddings[idea_id]
            similarities = []
            
            for other_id in idea_ids:
                if other_id == idea_id:
                    continue
                
                other_embedding = embeddings[other_id]
                sim = self.cosine_similarity(current_embedding, other_embedding)
                similarities.append((other_id, sim))
            
            # Sort by similarity and take top K
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_k = similarities[:K]
            
            # Store neighbors
            for rank, (neighbor_id, cosine_sim) in enumerate(top_k):
                neighbor_item = {
                    'idea_id': idea_id,
                    'neighbor_id': neighbor_id,
                    'cosine_sim': Decimal(str(cosine_sim)),
                    'rank': rank + 1
                }
                
                neighbor_batch.append({'PutRequest': {'Item': neighbor_item}})
                
                # Batch write every 25 items
                if len(neighbor_batch) >= 25:
                    with self.neighbors_table.batch_writer() as batch:
                        for item in neighbor_batch:
                            batch.put_item(Item=item['PutRequest']['Item'])
                    neighbor_batch = []
        
        # Write remaining neighbors
        if neighbor_batch:
            with self.neighbors_table.batch_writer() as batch:
                for item in neighbor_batch:
                    batch.put_item(Item=item['PutRequest']['Item'])
        
        print(f"✅ Precomputed neighbors for {len(idea_ids)} ideas")
    
    def run_all_jobs(self):
        """Run all offline jobs in sequence"""
        print("🚀 Starting Cloud Code offline jobs...")
        
        # Step 1: Extract ideas and compute embeddings
        idea_count = self.extract_ideas_from_submissions()
        
        if idea_count == 0:
            print("No ideas found. Exiting.")
            return
        
        # Step 2: Compute novelty scores
        kept_count = self.compute_novelty_scores()
        
        # Step 3: Precompute neighbors
        self.precompute_neighbors()
        
        print("✅ All offline jobs completed!")
        print(f"Total ideas processed: {idea_count}")
        print(f"Ideas kept for rating: {kept_count}")

def main():
    jobs = CloudCodeOfflineJobs()
    jobs.run_all_jobs()

if __name__ == "__main__":
    main()