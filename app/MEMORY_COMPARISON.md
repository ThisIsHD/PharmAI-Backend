# Memory Storage Comparison

## In-Memory vs MongoDB

### In-Memory Storage (`memory.py`)

**Pros:**
- ✅ Fast (no network latency)
- ✅ Simple implementation
- ✅ No external dependencies
- ✅ Good for development/testing

**Cons:**
- ❌ Data lost on server restart
- ❌ Can't scale horizontally (multiple servers)
- ❌ Limited by server RAM
- ❌ No persistence across deployments

**Use Cases:**
- Local development
- Testing
- Demos
- Single-server deployments with acceptable data loss

---

### MongoDB Storage (`memory_mongo.py`)

**Pros:**
- ✅ Persistent across restarts
- ✅ Scales horizontally (multiple servers share data)
- ✅ Automatic TTL cleanup
- ✅ Production-ready
- ✅ Can handle millions of sessions
- ✅ Backup/restore capabilities

**Cons:**
- ❌ Slightly slower (network latency)
- ❌ Requires MongoDB setup
- ❌ More complex

**Use Cases:**
- Production deployments
- Multi-server setups
- When data persistence is critical
- Scalable applications

---

## Configuration

### Current Setup (MongoDB with Fallback)

`memory_mongo.py` automatically falls back to in-memory if MongoDB is unavailable:

```python
try:
    # Try MongoDB first
    return MongoMemoryStore(...)
except (ValueError, ConnectionError):
    # Fallback to in-memory
    return MemoryStore(...)
```

### Environment Variables

```env
# MongoDB Connection
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/

# Session Settings
MAX_SESSION_MESSAGES=30        # Keep last 30 messages per session
SESSION_TTL_SECONDS=604800     # Auto-delete after 7 days (0 = never)
```

---

## MongoDB Schema

```javascript
{
  "_id": "session-abc-123",           // session_id
  "messages": [
    {
      "role": "user",
      "content": "What is semaglutide?"
    },
    {
      "role": "assistant",
      "content": "Semaglutide is a GLP-1..."
    }
  ],
  "created_at": ISODate("2024-01-15T10:00:00Z"),
  "updated_at": ISODate("2024-01-15T10:05:00Z")
}
```

### Indexes

1. **updated_at** - For efficient queries
2. **TTL Index** - Automatic cleanup of old sessions

---

## Testing

### Test MongoDB Persistence
```powershell
cd app
python -c "from memory_mongo import memory_store; print(memory_store.get_session_count())"
```

### Test via API
```powershell
.\test_mongo_memory.ps1
```

### Verify in MongoDB Atlas
1. Go to MongoDB Atlas dashboard
2. Browse Collections
3. Database: `pharmai`
4. Collection: `sessions`
5. See your session data!

---

## Migration Path

### From In-Memory to MongoDB

1. **No code changes needed** - just update import in `app.py`:
   ```python
   from memory_mongo import memory_store  # MongoDB
   # from memory import memory_store      # In-memory
   ```

2. **Set MONGO_URI** in `app/.env`

3. **Restart server** - sessions will now persist

### From MongoDB back to In-Memory

1. Update import in `app.py`:
   ```python
   from memory import memory_store  # In-memory
   ```

2. Restart server

---

## Production Recommendations

✅ **Use MongoDB** for:
- Production deployments
- Multi-user applications
- When data persistence matters
- Scalable systems

✅ **Use In-Memory** for:
- Local development
- Quick testing
- Demos
- Prototypes

---

## Monitoring

### Check Active Sessions
```bash
curl http://localhost:7860/health
```

Response:
```json
{
  "status": "ok",
  "mongodb": "connected",
  "active_sessions": 42
}
```

### Manual Cleanup
```bash
curl -X POST http://localhost:7860/admin/cleanup-sessions?days=7
```

---

## Troubleshooting

### MongoDB Connection Failed
```
Error: Failed to connect to MongoDB
```

**Solutions:**
1. Check `MONGO_URI` in `app/.env`
2. Verify MongoDB Atlas IP whitelist (allow 0.0.0.0/0 for testing)
3. Check network connectivity
4. Verify credentials

### Fallback to In-Memory
```
⚠️  MongoDB not available: ...
⚠️  Falling back to in-memory storage
```

This is normal - system continues working with in-memory storage.
