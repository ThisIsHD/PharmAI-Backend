"""
Quick script to fix MongoDB indexes.
Run this if you get index conflicts.
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    print("❌ MONGO_URI not found in .env")
    exit(1)

try:
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db = client["pharmai"]
    collection = db["sessions"]
    
    print("Current indexes:")
    for name, info in collection.index_information().items():
        print(f"  - {name}: {info}")
    
    print("\nDropping old indexes...")
    
    # Drop the conflicting index
    try:
        collection.drop_index("updated_at_1")
        print("✅ Dropped updated_at_1")
    except Exception as e:
        print(f"⚠️  Could not drop updated_at_1: {e}")
    
    # Recreate with TTL
    ttl_seconds = int(os.getenv("SESSION_TTL_SECONDS", "604800"))
    collection.create_index(
        [("updated_at", 1)],
        expireAfterSeconds=ttl_seconds,
        name="session_ttl"
    )
    print(f"✅ Created session_ttl index (expires after {ttl_seconds}s)")
    
    print("\nNew indexes:")
    for name, info in collection.index_information().items():
        print(f"  - {name}: {info}")
    
    print("\n✅ Indexes fixed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    client.close()
