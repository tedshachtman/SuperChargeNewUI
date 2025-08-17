#!/usr/bin/env python3

import boto3
import uuid
import time

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('supercharged_superpower_library')

# Comprehensive superpower library with different difficulties
superpowers = [
    # EASY DIFFICULTY - Simple, straightforward powers
    {
        "difficulty": "easy",
        "title": "Super Strength",
        "description": "You have the ability to lift and move objects with 100 times normal human strength. This includes being able to lift cars, break through walls, and move heavy machinery with ease."
    },
    {
        "difficulty": "easy", 
        "title": "Invisibility",
        "description": "You can become completely invisible at will, including your clothes and anything you're holding. The invisibility lasts as long as you concentrate on it."
    },
    {
        "difficulty": "easy",
        "title": "Super Speed",
        "description": "You can run, move, and think at superhuman speeds - up to 100 mph on foot. Your reaction time is enhanced proportionally."
    },
    {
        "difficulty": "easy",
        "title": "Flight",
        "description": "You have the ability to fly through the air at will, reaching speeds up to 60 mph and altitudes up to 10,000 feet."
    },
    {
        "difficulty": "easy",
        "title": "X-Ray Vision",
        "description": "You can see through solid objects and materials, except for lead. You can control this ability and see normal vision when desired."
    },
    {
        "difficulty": "easy",
        "title": "Super Hearing",
        "description": "You can hear sounds from miles away and pick up conversations, footsteps, and other noises that would normally be inaudible."
    },
    {
        "difficulty": "easy",
        "title": "Telepathy",
        "description": "You can read the thoughts of anyone within 100 feet of you. You can choose whose thoughts to read and can turn this ability on and off."
    },
    {
        "difficulty": "easy",
        "title": "Heat Vision",
        "description": "You can emit focused beams of heat from your eyes, capable of melting metal, starting fires, or providing precise heating."
    },
    {
        "difficulty": "easy",
        "title": "Perfect Memory",
        "description": "You have the ability to remember everything you've ever seen, heard, read, or experienced with perfect clarity and instant recall."
    },
    {
        "difficulty": "easy",
        "title": "Super Healing",
        "description": "Any injury you sustain heals completely within minutes. This includes cuts, broken bones, burns, and even more serious injuries."
    },
    
    # MEDIUM DIFFICULTY - More complex powers requiring strategy
    {
        "difficulty": "medium",
        "title": "Telekinesis",
        "description": "You can move objects with your mind up to 1000 pounds in weight. You must be able to see the object and concentrate to maintain control."
    },
    {
        "difficulty": "medium",
        "title": "Shapeshifting",
        "description": "You can transform your body into any animal form for up to 2 hours at a time. You retain human intelligence but gain the animal's physical abilities."
    },
    {
        "difficulty": "medium",
        "title": "Time Dilation",
        "description": "You can slow down time around you by a factor of 10 for up to 5 minutes. From your perspective, everything else moves in slow motion."
    },
    {
        "difficulty": "medium",
        "title": "Elemental Control",
        "description": "You can control one element at a time (fire, water, earth, or air) within a 50-foot radius. You can switch elements but only control one at a time."
    },
    {
        "difficulty": "medium",
        "title": "Probability Manipulation",
        "description": "You can slightly influence the probability of events within your immediate vicinity. Small chances become more likely, unlikely events become possible."
    },
    {
        "difficulty": "medium",
        "title": "Phase Shifting",
        "description": "You can make your body intangible, allowing you to pass through solid objects. You can maintain this state for up to 10 minutes at a time."
    },
    {
        "difficulty": "medium",
        "title": "Energy Absorption",
        "description": "You can absorb and redirect various forms of energy (heat, electricity, kinetic energy) within a 20-foot radius and release it as needed."
    },
    {
        "difficulty": "medium",
        "title": "Duplication",
        "description": "You can create up to 3 physical copies of yourself that last for 1 hour. Each copy shares your memories and abilities but acts independently."
    },
    {
        "difficulty": "medium",
        "title": "Matter Transmutation",
        "description": "You can change the molecular structure of any material you touch, transforming it into another material of similar mass and density."
    },
    {
        "difficulty": "medium",
        "title": "Astral Projection",
        "description": "You can separate your consciousness from your body and travel as an invisible, intangible spirit within a 10-mile radius."
    },
    
    # HARD DIFFICULTY - Complex powers with limitations and strategic depth
    {
        "difficulty": "hard",
        "title": "Quantum Tunneling",
        "description": "You can shift your molecules to exist in quantum superposition, allowing instantaneous travel to any location you can visualize within 1000 miles, but only once per day."
    },
    {
        "difficulty": "hard",
        "title": "Reality Anchoring",
        "description": "You can create small zones (10-foot radius) where the laws of physics work differently. You can establish up to 3 zones at a time, each lasting 30 minutes."
    },
    {
        "difficulty": "hard",
        "title": "Temporal Echoes",
        "description": "You can see and interact with events that happened in any location up to 7 days in the past, but cannot change them. Each use drains you for 2 hours."
    },
    {
        "difficulty": "hard",
        "title": "Dimensional Storage",
        "description": "You can access a pocket dimension the size of a warehouse. Objects stored there are in temporal stasis and can be retrieved instantly, but living things cannot survive inside."
    },
    {
        "difficulty": "hard",
        "title": "Molecular Reconstruction",
        "description": "You can completely rebuild any non-living object you touch, changing its form while conserving mass. The process takes time proportional to the object's complexity."
    },
    {
        "difficulty": "hard",
        "title": "Consciousness Transfer",
        "description": "You can temporarily transfer your consciousness into any electronic device or AI system for up to 1 hour, gaining full control over its functions."
    },
    {
        "difficulty": "hard",
        "title": "Gravitational Manipulation",
        "description": "You can alter gravitational fields within a 100-foot radius, creating zones of increased, decreased, or directionally-changed gravity lasting up to 15 minutes."
    },
    {
        "difficulty": "hard",
        "title": "Information Synthesis",
        "description": "By touching any written or digital information, you can instantly understand it and synthesize connections with all other information you've ever encountered."
    },
    {
        "difficulty": "hard",
        "title": "Quantum Entanglement",
        "description": "You can create quantum links between any two objects you touch. Changes to one object are instantly reflected in the other, regardless of distance."
    },
    {
        "difficulty": "hard",
        "title": "Causal Loop Creation",
        "description": "You can create small temporal loops where a 5-minute period repeats up to 10 times. Only you retain memory between loops, and changes accumulate."
    }
]

def populate_library():
    """Populate the superpower library with predefined powers"""
    for power in superpowers:
        power_id = str(uuid.uuid4())
        item = {
            'powerId': power_id,
            'difficulty': power['difficulty'],
            'title': power['title'],
            'description': power['description'],
            'timestamp': int(time.time())
        }
        
        try:
            table.put_item(Item=item)
            print(f"Added {power['difficulty']} power: {power['title']}")
        except Exception as e:
            print(f"Error adding {power['title']}: {str(e)}")

if __name__ == "__main__":
    print("Populating superpower library...")
    populate_library()
    print("Library population complete!")