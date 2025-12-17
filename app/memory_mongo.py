"""
MongoDB-backed session memory store.
Replaces in-memory storage with persistent MongoDB storage.
"""
from __future__ import annotations
from typing import List, Optional
import os
from datetime import datetime, timedelta
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from schemas import Message
from dotenv import load_dotenv

#load env vars
load_dotenv()

class MongoMemoryStore:
    """
    MongoDB-backed session memory store.
    
    Schema:
    {
        "_id": "session_id",
        "messages": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ],
        "updated_at": datetime,
        "created_at": datetime
    }
    """

    def __init__(
        self,
        mongo_uri: Optional[str] = None,
        database_name: str = "pharmai",
        collection_name: str = "sessions",
        max_messages: int = 30,
        ttl_seconds: Optional[int] = None,
    ):
        self.max_messages = max_messages
        self.ttl_seconds = ttl_seconds
        
        # Get MongoDB URI from env or parameter
        self.mongo_uri = mongo_uri or os.getenv("MONGO_URI")
        if not self.mongo_uri:
            raise ValueError("MONGO_URI not found in environment variables")
        
        # Connect to MongoDB
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            print(f"✅ MongoDB connected: {database_name}.{collection_name}")
        except ConnectionFailure as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")
        
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        
        # Create indexes
        self._create_indexes()

    def _create_indexes(self):
        """Create indexes for performance and TTL."""
        try:
            # Get existing indexes
            existing_indexes = self.collection.index_information()
            
            # TTL index - automatically delete old sessions
            if self.ttl_seconds:
                # Check if TTL index exists
                ttl_exists = any(
                    idx.get("expireAfterSeconds") is not None
                    for idx in existing_indexes.values()
                )
                
                if not ttl_exists:
                    # Drop the basic updated_at index if it exists (without TTL)
                    if "updated_at_1" in existing_indexes:
                        self.collection.drop_index("updated_at_1")
                    
                    # Create TTL index
                    self.collection.create_index(
                        [("updated_at", ASCENDING)],
                        expireAfterSeconds=self.ttl_seconds,
                        name="session_ttl"
                    )
                    print(f"✅ Created TTL index (expires after {self.ttl_seconds}s)")
            else:
                # Just a regular index on updated_at (no TTL)
                if "updated_at_1" not in existing_indexes and "session_ttl" not in existing_indexes:
                    self.collection.create_index([("updated_at", ASCENDING)])
                    print("✅ Created updated_at index")
                    
        except OperationFailure as e:
            # Index creation failed, but continue anyway
            print(f"⚠️  Index creation warning: {e}")
            pass

    def get(self, session_id: str) -> List[Message]:
        """Get messages for a session."""
        if not session_id:
            return []
        
        try:
            doc = self.collection.find_one({"_id": session_id})
            if not doc:
                return []
            
            # Convert dict messages to Message objects
            messages = []
            for msg in doc.get("messages", []):
                messages.append(Message(
                    role=msg.get("role", "user"),
                    content=msg.get("content", "")
                ))
            
            return messages
        except OperationFailure as e:
            print(f"Error getting session {session_id}: {e}")
            return []

    def append(self, session_id: str, role: str, content: str) -> None:
        """Append a message to a session."""
        if not session_id:
            return
        
        now = datetime.utcnow()
        message = {"role": role, "content": content}
        
        try:
            # Try to update existing session
            result = self.collection.update_one(
                {"_id": session_id},
                {
                    "$push": {"messages": message},
                    "$set": {"updated_at": now}
                }
            )
            
            # If session doesn't exist, create it
            if result.matched_count == 0:
                self.collection.insert_one({
                    "_id": session_id,
                    "messages": [message],
                    "created_at": now,
                    "updated_at": now
                })
            
            # Trim old messages if needed
            self._trim_messages(session_id)
            
        except OperationFailure as e:
            print(f"Error appending to session {session_id}: {e}")

    def _trim_messages(self, session_id: str) -> None:
        """Keep only the most recent max_messages."""
        try:
            doc = self.collection.find_one({"_id": session_id})
            if not doc:
                return
            
            messages = doc.get("messages", [])
            if len(messages) > self.max_messages:
                # Keep only the most recent messages
                trimmed = messages[-self.max_messages:]
                self.collection.update_one(
                    {"_id": session_id},
                    {"$set": {"messages": trimmed}}
                )
        except OperationFailure as e:
            print(f"Error trimming session {session_id}: {e}")

    def set_messages(self, session_id: str, messages: List[Message]) -> None:
        """Replace session history entirely."""
        if not session_id:
            return
        
        now = datetime.utcnow()
        message_dicts = [{"role": m.role, "content": m.content} for m in messages]
        
        # Keep only most recent messages
        if len(message_dicts) > self.max_messages:
            message_dicts = message_dicts[-self.max_messages:]
        
        try:
            self.collection.update_one(
                {"_id": session_id},
                {
                    "$set": {
                        "messages": message_dicts,
                        "updated_at": now
                    },
                    "$setOnInsert": {"created_at": now}
                },
                upsert=True
            )
        except OperationFailure as e:
            print(f"Error setting messages for session {session_id}: {e}")

    def clear(self, session_id: str) -> None:
        """Clear a single session."""
        if not session_id:
            return
        
        try:
            self.collection.delete_one({"_id": session_id})
        except OperationFailure as e:
            print(f"Error clearing session {session_id}: {e}")

    def cleanup_old_sessions(self, days: int = 7) -> int:
        """
        Manually cleanup sessions older than X days.
        (TTL index handles this automatically if configured)
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        try:
            result = self.collection.delete_many({"updated_at": {"$lt": cutoff}})
            return result.deleted_count
        except OperationFailure as e:
            print(f"Error cleaning up old sessions: {e}")
            return 0

    def get_session_count(self) -> int:
        """Get total number of active sessions."""
        try:
            return self.collection.count_documents({})
        except OperationFailure:
            return 0

    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()


# Create global singleton
def create_memory_store() -> MongoMemoryStore:
    """Factory function to create memory store based on configuration."""
    try:
        # Try MongoDB first
        return MongoMemoryStore(
            max_messages=int(os.getenv("MAX_SESSION_MESSAGES", "30")),
            ttl_seconds=int(os.getenv("SESSION_TTL_SECONDS", "0")) or None,
        )
    except (ValueError, ConnectionError) as e:
        print(f"⚠️  MongoDB not available: {e}")
        print("⚠️  Falling back to in-memory storage")
        
        # Fallback to in-memory
        from memory import MemoryStore
        return MemoryStore(
            max_messages=int(os.getenv("MAX_SESSION_MESSAGES", "30")),
            ttl_seconds=int(os.getenv("SESSION_TTL_SECONDS", "0")) or None,
        )


# Global instance
memory_store = create_memory_store()
