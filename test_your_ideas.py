#!/usr/bin/env python3

import os
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Your two test ideas
idea1 = """You can use the bag of holding to steal things from people's luggages. What you do is you break into someone's house, you open up their luggage, as someone who's about to travel, you open up their luggage, and you get inside the bag of holding, in their luggage. Then, after you're through airport security, and after you're on the plane in the baggage part, you get out, you rummage through everyone's luggage, and you steal all of the expensive valuables. You have more than enough time to do this because you're on the plane. Then, you put all the valuables back in your bag of holding, and you get in your bag of holding, and you get back in anyone's luggage."""

idea2 = """You find the house of somebody who's a high-up official in the government. You break into their house and you get, in the bag of holding, in their work bag, in a pocket that seems to not be opened, or not often be opened. You stay in there until they go to work at some high-level security base. You have your head peeked outside of the bag and you listen for when the bag is set down. Then you get out of the bag. You can take pictures or you can steal documents. And then, any time you need to hide or at the end of your session, when you just want to get out of the base, you get back in the bag and back in the person's backpack or whatever they're carrying and they safely escort you out of the base."""

def get_embedding(text):
    """Get embedding using the same model as the website"""
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=text,
        encoding_format="float"
    )
    return response.data[0].embedding

def calculate_similarity(emb1, emb2):
    """Calculate cosine similarity between two embeddings"""
    emb1 = np.array(emb1).reshape(1, -1)
    emb2 = np.array(emb2).reshape(1, -1)
    return cosine_similarity(emb1, emb2)[0][0]

def main():
    print("Testing similarity between your two bag of holding ideas")
    print("Using OpenAI's text-embedding-3-large (same as the website)")
    print("=" * 70)
    
    # Get embeddings
    print("Getting embeddings...")
    emb1 = get_embedding(idea1)
    emb2 = get_embedding(idea2)
    
    # Calculate similarity
    similarity = calculate_similarity(emb1, emb2)
    
    print(f"\nSimilarity Score: {similarity:.4f}")
    print(f"Similarity Percentage: {similarity * 100:.2f}%")
    
    print("\nAnalysis:")
    if similarity > 0.8:
        print("🔥 VERY HIGH SIMILARITY - These ideas are extremely similar")
    elif similarity > 0.7:
        print("🚀 HIGH SIMILARITY - These ideas share many common elements")
    elif similarity > 0.6:
        print("⭐ MODERATE-HIGH SIMILARITY - Clear shared themes with some variation")
    elif similarity > 0.5:
        print("📊 MODERATE SIMILARITY - Some shared themes but distinct approaches")
    elif similarity > 0.4:
        print("🤔 LOW-MODERATE SIMILARITY - Few common elements")
    else:
        print("❌ LOW SIMILARITY - These ideas are quite different")
    
    print(f"\nFor reference, in your game:")
    print(f"- Top similarity pairs typically score 0.65-0.75")
    print(f"- Medium similarity pairs score around 0.50-0.65") 
    print(f"- Low similarity pairs score 0.35-0.50")
    print(f"- Very different pairs score below 0.35")
    
    # Scale to 1-10 rating (like the game uses)
    scaled_rating = 1 + (similarity * 9)  # Scale 0-1 to 1-10
    print(f"\nIf this were in the game, experts would likely rate it: {scaled_rating:.1f}/10")

if __name__ == "__main__":
    main()