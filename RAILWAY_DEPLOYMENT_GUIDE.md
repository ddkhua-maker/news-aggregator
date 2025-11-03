# Railway Deployment Guide - iGaming News Aggregator

## Prerequisites
- GitHub account with repository: `ddkhua-maker/news-aggregator`
- Railway account (sign up at https://railway.app)
- OpenAI API key (from https://platform.openai.com)

---

## Step 1: Create Railway Project

### 1.1 Go to Railway Dashboard
- Navigate to https://railway.app
- Click **"New Project"**

### 1.2 Deploy from GitHub
- Select **"Deploy from GitHub repo"**
- Choose repository: `ddkhua-maker/news-aggregator`
- Railway will automatically detect the Dockerfile

---

## Step 2: Add PostgreSQL Database

### 2.1 Add Database Service
- In your Railway project, click **"+ New"**
- Select **"Database"**
- Choose **"Add PostgreSQL"**
- Railway will provision the database automatically

### 2.2 Verify Database Connection
- The `DATABASE_URL` environment variable is automatically created
- Your web service will automatically use this for database connection

---

## Step 3: Configure Environment Variables

### 3.1 Navigate to Variables Tab
- Click on your **web service** (not the database)
- Go to **"Variables"** tab

### 3.2 Add Required Variables

**REQUIRED:**
```
OPENAI_API_KEY=sk-your-openai-api-key-here
```

**RECOMMENDED:**
```
ENVIRONMENT=production
```

**OPTIONAL (with defaults):**
```
MAX_ARTICLES_PER_FEED=10
FETCH_INTERVAL_MINUTES=30
SUMMARY_MAX_TOKENS=150
```

**FOR CORS (if you have a frontend):**
```
CORS_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com
```

### 3.3 Verify Variables
- Ensure `DATABASE_URL` is present (auto-created by Railway)
- Ensure `PORT` is NOT set manually (Railway handles this automatically)

---

## Step 4: Deploy

### 4.1 Automatic Deployment
- Railway will automatically deploy after you add environment variables
- Watch the **"Deployments"** tab for build progress

### 4.2 Build Process (Expected: 30-60 seconds)
```
[1/4] FROM python:3.11-slim
[2/4] Installing system dependencies (gcc, postgresql-client)
[3/4] Installing Python dependencies
[4/4] Copying application code
```

### 4.3 Check Build Logs
Look for:
```
✓ Building image
✓ Pushing image
✓ Starting deployment
✓ Deployment successful
```

---

## Step 5: Verify Deployment

### 5.1 Generate Domain
- In Railway project, click **"Settings"**
- Under **"Domains"**, click **"Generate Domain"**
- Railway will provide a URL like: `your-app-name.up.railway.app`

### 5.2 Test Health Endpoints

**Test 1: Root Health Check**
```bash
curl https://your-app-name.up.railway.app/
```
Expected response:
```json
{"status": "healthy", "service": "iGaming News Aggregator"}
```

**Test 2: Simple Health Check**
```bash
curl https://your-app-name.up.railway.app/health
```
Expected response:
```json
{"status": "ok"}
```

**Test 3: API Documentation**
Open in browser:
```
https://your-app-name.up.railway.app/docs
```
Should see interactive Swagger UI documentation.

---

## Step 6: Check Deployment Logs

### 6.1 View Logs
- Go to **"Deployments"** tab
- Click on the latest deployment
- View logs for startup messages

### 6.2 Expected Log Messages
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Database initialized successfully
INFO:     Application started in production mode
INFO:     CORS origins: [...]
INFO:     Uvicorn running on http://0.0.0.0:XXXX
```

### 6.3 Check for Errors
❌ **Common issues:**
- `OPENAI_API_KEY environment variable must be set` → Add OPENAI_API_KEY to variables
- Database connection errors → Verify DATABASE_URL exists
- Import errors → Should be fixed (we use absolute imports now)

---

## Step 7: Initialize Application Data

### 7.1 Fetch Initial News Articles
```bash
curl -X POST https://your-app-name.up.railway.app/api/fetch-news
```

Expected response:
```json
{
  "status": "success",
  "message": "Successfully fetched and saved X new articles",
  "new_articles": X,
  "total_parsed": Y
}
```

### 7.2 Generate AI Summaries
```bash
curl -X POST https://your-app-name.up.railway.app/api/generate-summaries
```

Expected response:
```json
{
  "status": "success",
  "message": "Successfully generated X summaries",
  "summaries_generated": X
}
```

### 7.3 View Articles
```bash
curl https://your-app-name.up.railway.app/api/articles?limit=5
```

---

## Step 8: Test All Endpoints

### 8.1 Test API Endpoints

**Get Sources:**
```bash
curl https://your-app-name.up.railway.app/api/sources
```

**Search Articles:**
```bash
curl -X POST https://your-app-name.up.railway.app/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "casino regulation", "limit": 5}'
```

**Create Daily Digest:**
```bash
curl -X POST https://your-app-name.up.railway.app/api/create-digest
```

---

## Step 9: Monitor and Maintain

### 9.1 Set Up Monitoring
- Use Railway's built-in metrics (CPU, Memory, Network)
- Check logs regularly for errors

### 9.2 Monitor Costs
- **PostgreSQL database:** Free tier includes limited storage
- **OpenAI API:** Monitor usage at https://platform.openai.com/usage
- **Railway:** Monitor usage in project settings

### 9.3 Scale if Needed
- Railway auto-scales based on demand
- Upgrade plan if you hit free tier limits

---

## Troubleshooting

### Issue: Build Fails

**Check:**
- Dockerfile syntax is correct
- requirements.txt has all dependencies
- No syntax errors in Python files

**Solution:**
- Review build logs in Railway
- Check recent commits for breaking changes

### Issue: Container Crashes on Startup

**Check:**
- OPENAI_API_KEY is set
- DATABASE_URL exists
- No import errors

**Solution:**
```bash
# Check logs in Railway dashboard
# Look for Python tracebacks
# Verify environment variables
```

### Issue: Database Connection Failed

**Check:**
- PostgreSQL service is running
- DATABASE_URL is present
- URL format is correct (postgresql:// not postgres://)

**Solution:**
- Our code auto-converts postgres:// to postgresql://
- Restart deployment if DATABASE_URL was just added

### Issue: CORS Errors (from frontend)

**Check:**
- CORS_ORIGINS environment variable is set
- Frontend domain is included in CORS_ORIGINS
- ENVIRONMENT is set to "production"

**Solution:**
```bash
# Add CORS_ORIGINS variable:
CORS_ORIGINS=https://your-frontend.com,https://www.your-frontend.com
```

---

## Post-Deployment Tasks

### ✅ Required
1. Test all API endpoints
2. Fetch initial news articles
3. Generate summaries for articles
4. Create first daily digest

### ✅ Recommended
1. Set up custom domain (optional)
2. Configure scheduled jobs for:
   - Fetching news every 30 minutes
   - Generating summaries daily
   - Creating daily digests
3. Monitor OpenAI API costs
4. Set up error alerting

### ✅ Optional
1. Add frontend application
2. Configure SSL/TLS (Railway handles this automatically)
3. Set up CI/CD for automatic deployments
4. Add monitoring tools (Sentry, etc.)

---

## Railway Auto-Deployment

### How It Works
- Railway watches your GitHub repository
- On push to `main` branch, Railway automatically:
  1. Pulls latest code
  2. Builds new Docker image
  3. Deploys updated container
  4. Routes traffic to new deployment

### Disable Auto-Deploy (if needed)
- Go to project **Settings** → **Deployments**
- Toggle **"Auto Deploy"** off

---

## Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | None | OpenAI API key for summaries |
| `DATABASE_URL` | ✅ Yes | Auto-set | PostgreSQL connection URL |
| `PORT` | ❌ No | Auto-set | Railway sets this automatically |
| `ENVIRONMENT` | ❌ No | `development` | Set to `production` |
| `MAX_ARTICLES_PER_FEED` | ❌ No | `10` | Articles to fetch per RSS feed |
| `FETCH_INTERVAL_MINUTES` | ❌ No | `30` | How often to fetch news |
| `SUMMARY_MAX_TOKENS` | ❌ No | `150` | Max tokens for AI summaries (2-3 sentences) |
| `CORS_ORIGINS` | ❌ No | `localhost` | Comma-separated frontend URLs |

---

## Success Criteria

Your deployment is successful when:

✅ Build completes without errors (30-60 seconds)
✅ Container starts successfully
✅ Health check at `/` returns `{"status": "healthy"}`
✅ Database connection works
✅ Can fetch news articles via API
✅ Can generate AI summaries
✅ API documentation loads at `/docs`
✅ No errors in deployment logs

---

## Support

- **Railway Docs:** https://docs.railway.app
- **Project Issues:** https://github.com/ddkhua-maker/news-aggregator/issues
- **Railway Status:** https://railway.statuspage.io

---

## Security Notes

🔒 **Do NOT commit:**
- `.env` file (contains OPENAI_API_KEY)
- Database credentials
- Any API keys

✅ **All secrets managed via Railway environment variables**

---

## Next Steps After Deployment

1. **Test the API** using the examples above
2. **Fetch initial data** (articles and summaries)
3. **Set up scheduled jobs** for automatic news fetching
4. **Monitor costs** (OpenAI API usage)
5. **Deploy a frontend** to consume the API

---

🎉 **Your iGaming News Aggregator is now live!**

API URL: `https://your-app-name.up.railway.app`
API Docs: `https://your-app-name.up.railway.app/docs`
