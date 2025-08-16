#!/usr/bin/env python3

import os
import json
import numpy as np
from openai import OpenAI
from pinecone import Pinecone
from sklearn.metrics.pairwise import cosine_similarity
import itertools

# API Keys - Load from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# Check if API keys are set
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY environment variable is not set")

# Initialize clients
client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)

# 30 Bag of Holding Ideas (extracted from the website)
IDEAS = [
    "Anchor the bag at the bottom of a deep mineshaft. Place a multi-ton block of tungsten inside. When you retrieve the block at the top of the shaft, gravity immediately acts on its full mass, causing it to plummet downwards attached to a pulley and lever system. Just before impact, place it back in the bag, rendering it weightless. You can then effortlessly hoist the bag back to the top to repeat the process. This creates a trebuchet that can be re-cocked with almost no energy, powered entirely by repeatedly resetting the object's gravitational potential energy to launch massive projectiles.",
    "Fill the bag almost completely with a dense non-Newtonian fluid, like a cornstarch and water slurry (oobleck). When you get inside, you're suspended within this fluid. During sudden, high-G events like a fall or crash, your body's inertia would normally cause catastrophic injury. However, the shear stress from any rapid movement causes the non-Newtonian fluid to instantly become rigid, distributing the force evenly across your entire body. This effectively functions as a passive inertial dampener, allowing you to survive impacts that would otherwise be fatal by preventing your organs from moving relative to your skeleton.",
    "Procure a large, well-insulated Dewar flask that fits inside the bag and fill it with liquid nitrogen. Since objects inside the bag maintain their state indefinitely, the liquid nitrogen will remain at its cryogenic temperature of −196°C (−321°F) without boiling off or requiring external power. This creates a perfect, portable stasis chamber for preserving biological samples, organs, or even a person in a suitable containment suit for extended periods. The weightlessness makes handling the otherwise heavy and dangerous flask completely trivial.",
    "Place a massive, perfectly cast bell inside the bag. Strike it with a heavy mallet to set it vibrating intensely at its resonant frequency, then quickly seal the bag. The kinetic energy of the vibration is preserved perfectly within the extradimensional space, as there is no air to create drag or transmit the sound away. To deploy this stored energy, simply open the bag and aim the aperture at a target. The bell's surface instantly interacts with the outside air, releasing all its accumulated sonic energy in a single, devastating blast of sound pressure capable of shattering fortifications.",
    "Take the open bag to the highest attainable altitude or into outer space, allowing the air inside to evacuate into the near-vacuum of the surroundings. Once evacuated, seal the bag. You now possess a portable, perfect vacuum chamber. The integrity of the extradimensional space ensures no atoms can leak back in over time. This can be used for advanced scientific applications like cold welding, creating flawless crystals, or instantly extinguishing any fire or combustion-based process by placing it inside and depriving it of all oxygen.",
    "Securely attach a long, rigid pole to the exterior of the bag. After getting inside, have an external motor or partner spin the pole at high speed. Because the combined mass of you and the bag is negligible, it requires very little energy to achieve an extremely high angular velocity. Inside the bag, you will be pressed against the side of the extradimensional space by a powerful simulated gravitational force, the magnitude of which is determined by the speed of rotation. This can be used for high-G training, separating materials of different densities, or conducting experiments in variable gravity.",
    "Seal the bag at sea level, trapping normal atmospheric pressure (14.7 psi) inside. Travel to a location with significantly lower ambient pressure, such as a high mountain peak. When you rapidly unseal the bag, the higher-pressure air inside expands outwards explosively, creating a powerful concussive blast. The reverse is also possible: seal the bag at high altitude (low pressure) and open it at sea level. The higher-pressure outside air will rush in with violent force, creating a localized implosion capable of crushing objects placed directly at the opening.",
    "Tie one end of an extremely long spool of rope to an anchor point and feed the entire spool into the bag. You can now rappel down a cliff or into a chasm of virtually unlimited depth. The only weight you have to manage is the weight of the deployed section of rope; the immense weight of the thousands of feet of rope remaining in the bag is completely negated. This allows a single person to carry and deploy miles of rope that would normally weigh tons, making previously inaccessible locations reachable.",
    "Get inside the bag and seal it, leaving a small opening for a reinforced hose connected to a water pump. Submerge the bag. Since the bag and its contents are nearly weightless, the system is incredibly buoyant. To function as a submarine, simply pump external water into the bag, increasing its total mass until its density becomes greater than the surrounding water, causing it to sink. To surface, pump the water back out. This allows for controlled vertical movement through a water column with minimal energy expenditure.",
    "Fill the bag with a massive volume of a dielectric, fuzzy material like wool. Use a Van de Graaff generator to build up an enormous static electric charge on the wool inside the bag. The perfect isolation of the extradimensional space prevents the charge from dissipating into the atmosphere. To deploy, open the bag and touch a grounded conductor to the wool. The entire stored charge of millions of volts will discharge at once, creating a powerful, man-made lightning bolt.",
    "Place a large, perfectly balanced gyroscope inside the bag. Use an external motor to spin it up to an extremely high RPM before sealing it inside. The gyroscope will now spin indefinitely in a frictionless vacuum, preserving its angular momentum perfectly. This momentum battery can be used as a powerful stabilization system for a vehicle or structure. Alternatively, the rotational energy can be mechanically tapped by a clutch mechanism to power machinery, releasing the stored kinetic energy on demand.",
    "Prepare two reactive chemicals separated by a membrane that dissolves at a known rate (e.g., a specific thickness of sugar in water). Place this device inside the bag. The state preservation property halts all molecular processes, including the dissolution of the membrane. When you retrieve the device from the bag, the timer starts. This allows you to create a perfectly silent and reliable timer for initiating a chemical reaction (for demolitions, traps, or automated experiments) with a precise, pre-determined delay.",
    "Use a parabolic solar furnace to heat a large block of graphite to several thousand degrees until it is white-hot. Carefully place this block inside the bag. The bag will preserve its immense thermal energy indefinitely, preventing it from cooling via radiation or convection. Later, you can retrieve the block and use it as a long-lasting, portable heat source for forging, generating steam to power a turbine, or as a devastating incendiary weapon. The weightlessness makes transporting the incredibly heavy and dangerous object trivial.",
    "Completely fill a hardened steel container with water, ensuring there are no air bubbles, and seal it. Place the container inside the bag. In a sub-zero environment, retrieve the container and place it inside a crevice or piece of machinery. As the water inside begins to freeze, it expands by about 9%, exerting an immense and slow hydrostatic pressure—up to 30,000 psi—on the inner walls of the container. This force is sufficient to silently split solid rock or rupture metal casings without any explosive force.",
    "Place two large tanks inside the bag, one positioned above the other. Connect them with a pipe that has a small turbine in the middle. Fill the top tank with water and retrieve the apparatus. The water will flow down, spinning the turbine and generating electricity. Once the top tank is empty, place the entire setup back in the bag. Because it's weightless, you can effortlessly flip it upside down. When retrieved again, the now-full tank is on top, ready to generate power once more, creating a closed-loop, rechargeable gravity battery.",
    "Construct a sail of enormous surface area from an ultralight material and attach its rigging directly to the bag itself. Get inside. Normally, a boat's speed is limited by the drag of its hull pushing through water. Here, the wind acts upon a massive sail, but the mass it needs to accelerate is only that of the nearly weightless bag and its occupant. This creates a phenomenal thrust-to-mass ratio, allowing the craft to skim across the water surface at speeds impossible for a conventional vessel, pushed by even the slightest breeze.",
    "Create a large pouch from a strong, semi-permeable membrane and fill it with a highly concentrated brine solution. Seal it and place it in the Bag of Holding. To deploy, retrieve this inner pouch and throw it into a body of fresh water, such as a water tower or a small lake. Water from the outside will be driven by osmosis to rush into the pouch to equalize the solute concentration. This rapid influx creates immense internal pressure, causing the pouch to swell and rupture with explosive force, creating a powerful non-combustible shockwave.",
    "Construct a large, insulated box and paint its interior with a near-perfect black-body material like Vantablack. Place this box inside the bag. In a hot environment, you can aim the open box at a heat source (like a fire or an engine). The matte black surface will absorb nearly 100% of the incoming thermal radiation. Because the box is in the extradimensional space, its temperature doesn't rise conventionally, and it cannot radiate the heat back out. It functions as a perfect heat sink, passively drawing thermal energy out of an area to cause localized cooling without any exhaust.",
    "Place a massive Archimedes' screw inside the bag, leaving only the hand crank exposed. Lower the bag's opening into a body of water. Because the long, heavy screw inside is rendered weightless, a single person can turn the crank with minimal effort. The rotating screw will function normally, lifting huge volumes of water up and out of the bag's opening. This allows one person to single-handedly perform large-scale irrigation or drainage tasks that would typically require a powerful, heavy mechanical pump."
]

def generate_embeddings():
    """Generate embeddings for all ideas using OpenAI's text-embedding-3-large model"""
    print("Generating embeddings for 30 bag of holding ideas...")
    
    embeddings = []
    for i, idea in enumerate(IDEAS):
        print(f"Processing idea {i+1}/30...")
        
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=idea,
            encoding_format="float"
        )
        
        embedding = response.data[0].embedding
        embeddings.append({
            'id': f'idea_{i}',
            'text': idea,
            'embedding': embedding
        })
    
    return embeddings

def setup_pinecone():
    """Create or connect to Pinecone index"""
    index_name = "supercharge-ideas"
    
    # Check if index exists
    try:
        index = pc.Index(index_name)
        print(f"Connected to existing index: {index_name}")
        return index
    except:
        # Create new index if it doesn't exist
        print(f"Creating new index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=3072,  # text-embedding-3-large dimension
            metric="cosine",
            spec={
                "serverless": {
                    "cloud": "aws",
                    "region": "us-east-1"
                }
            }
        )
        return pc.Index(index_name)

def store_embeddings(index, embeddings):
    """Store embeddings in Pinecone"""
    print("Storing embeddings in Pinecone...")
    
    vectors = []
    for emb in embeddings:
        vectors.append({
            'id': emb['id'],
            'values': emb['embedding'],
            'metadata': {
                'text': emb['text'][:1000]  # Pinecone metadata limit
            }
        })
    
    # Upsert in batches
    batch_size = 10
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        index.upsert(vectors=batch)
        print(f"Uploaded batch {i//batch_size + 1}")

def calculate_similarities(embeddings):
    """Calculate pairwise similarities and rank them"""
    print("Calculating pairwise similarities...")
    
    # Extract just the embedding vectors
    vectors = np.array([emb['embedding'] for emb in embeddings])
    
    # Calculate cosine similarity matrix
    similarity_matrix = cosine_similarity(vectors)
    
    # Get all pairwise similarities
    similarities = []
    for i in range(len(IDEAS)):
        for j in range(i+1, len(IDEAS)):
            similarity_score = similarity_matrix[i][j]
            similarities.append({
                'idea1_index': i,
                'idea2_index': j,
                'idea1_text': IDEAS[i][:100] + "...",
                'idea2_text': IDEAS[j][:100] + "...",
                'similarity_score': float(similarity_score),
                'cosine_distance': 1 - float(similarity_score)
            })
    
    # Sort by similarity (highest first)
    similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
    
    return similarities

def main():
    print("SuperCharge Similarity Backend")
    print("=" * 40)
    
    # Generate embeddings
    embeddings = generate_embeddings()
    
    # Setup Pinecone
    index = setup_pinecone()
    
    # Store embeddings
    store_embeddings(index, embeddings)
    
    # Calculate similarities
    similarities = calculate_similarities(embeddings)
    
    # Save results
    with open('/Users/ted/SuperChargeNewUI/similarity_results.json', 'w') as f:
        json.dump(similarities, f, indent=2)
    
    print(f"\nTop 10 Most Similar Pairs:")
    print("=" * 50)
    for i, sim in enumerate(similarities[:10]):
        print(f"{i+1}. Similarity: {sim['similarity_score']:.4f}")
        print(f"   Idea {sim['idea1_index']+1}: {sim['idea1_text']}")
        print(f"   Idea {sim['idea2_index']+1}: {sim['idea2_text']}")
        print()
    
    print(f"\nTop 10 Most Dissimilar Pairs:")
    print("=" * 50)
    for i, sim in enumerate(similarities[-10:]):
        print(f"{i+1}. Similarity: {sim['similarity_score']:.4f}")
        print(f"   Idea {sim['idea1_index']+1}: {sim['idea1_text']}")
        print(f"   Idea {sim['idea2_index']+1}: {sim['idea2_text']}")
        print()
    
    print(f"Results saved to similarity_results.json")
    print(f"Total pairs analyzed: {len(similarities)}")

if __name__ == "__main__":
    main()