# Deploy to HuggingFace Spaces

## Prerequisites

1. HuggingFace account
2. Anthropic API key
3. MongoDB Atlas account (free tier works)
4. (Optional) Tavily API key
5. (Optional) LangSmith API key

## Deployment Steps

### 1. Create New Space

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Name: `PharmAI_Navigator`
4. License: MIT
5. SDK: **Docker**
6. Click "Create Space"

### 2. Configure Secrets

In your Space settings, add these secrets:

**Required:**
```
ANTHROPIC_API_KEY=sk-ant-api03-...
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/?appName=Cluster0
```

**Optional:**
```
TAVILY_API_KEY=tvly-...
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=pharmai-navigator
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
MAX_OUTPUT_TOKENS=1200
MAX_TOOL_LOOPS=4
SESSION_TTL_SECONDS=604800
```

### 3. Upload Files

Upload these files to your Space:

```
app/
├── Dockerfile
├── requirements.txt
├── README.md
├── app.py
├── graph.py
├── memory_mongo.py
├── memory.py
├── schemas.py
├── tools.py
└── .env (optional, use Secrets instead)
```

**Important:** Do NOT upload `.env` file with secrets. Use HF Secrets instead.

### 4. Git Method (Recommended)

```bash
# Clone your space
git clone https://huggingface.co/spaces/YOUR_USERNAME/PharmAI_Navigator
cd PharmAI_Navigator

# Copy app files
cp -r ../app/* .

# Remove test files
rm -f test_*.py test_*.ps1 fix_indexes.py

# Commit and push
git add .
git commit -m "Initial deployment"
git push
```

### 5. Wait for Build

- HuggingFace will automatically build your Docker image
- Check the "Logs" tab for build progress
- Build takes ~5-10 minutes

### 6. Test Your Space

Once deployed, test with:

```bash
# Health check
curl https://YOUR_USERNAME-pharmai-navigator.hf.space/health

# Test query
curl -X POST https://YOUR_USERNAME-pharmai-navigator.hf.space/run \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","query":"What is pembrolizumab?"}'
```

## MongoDB Setup

### 1. Create MongoDB Atlas Cluster

1. Go to https://www.mongodb.com/cloud/atlas
2. Create free cluster
3. Create database user
4. Whitelist IP: `0.0.0.0/0` (allow all)
5. Get connection string

### 2. Configure Database

Your app will automatically:
- Create database: `pharmai`
- Create collection: `sessions`
- Create TTL index for auto-cleanup

## Troubleshooting

### Build Fails

Check Dockerfile and requirements.txt syntax:
```bash
docker build -t pharmai-test .
```

### MongoDB Connection Error

- Verify `MONGO_URI` in Secrets
- Check IP whitelist (0.0.0.0/0)
- Test connection locally first

### API Key Issues

- Verify `ANTHROPIC_API_KEY` in Secrets
- Check API key has credits
- Test locally first

### Memory Issues

If Space runs out of memory:
- Reduce `MAX_OUTPUT_TOKENS`
- Reduce `MAX_TOOL_LOOPS`
- Upgrade to larger Space tier

## Local Testing

Test Docker build locally before deploying:

```bash
cd app

# Build
docker build -t pharmai-navigator .

# Run
docker run -p 7860:7860 \
  -e ANTHROPIC_API_KEY=your-key \
  -e MONGO_URI=your-mongo-uri \
  pharmai-navigator

# Test
curl http://localhost:7860/health
```

## Monitoring

### LangSmith (Optional)

If you added LangSmith keys, monitor at:
https://smith.langchain.com

### MongoDB Atlas

Monitor sessions at:
https://cloud.mongodb.com
- Database: pharmai
- Collection: sessions

## Updating Your Space

```bash
# Make changes locally
# Test locally
# Then push

git add .
git commit -m "Update: description"
git push
```

HuggingFace will automatically rebuild and redeploy.

## Cost Considerations

**Free Tier:**
- HuggingFace Spaces: Free (with limits)
- MongoDB Atlas: Free (512MB)
- Anthropic API: Pay per use
- Tavily API: Free tier available

**Estimated Costs:**
- Simple query: ~$0.01
- Complex query with tools: ~$0.05-0.10
- 1000 queries/month: ~$20-50

## Security Notes

1. **Never commit API keys** - Use HF Secrets
2. **Use environment variables** - Not hardcoded values
3. **Whitelist IPs** - If possible (MongoDB)
4. **Monitor usage** - Set up billing alerts
5. **Rate limiting** - Consider adding rate limits

## Support

- HuggingFace Docs: https://huggingface.co/docs/hub/spaces
- MongoDB Docs: https://docs.mongodb.com
- LangChain Docs: https://python.langchain.com
