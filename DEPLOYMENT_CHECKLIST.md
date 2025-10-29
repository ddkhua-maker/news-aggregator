# Railway Deployment Checklist

## Files Ready ✅

- [x] **Dockerfile** (clean, no cd commands)
- [x] **railway.json** (using DOCKERFILE builder)
- [x] **backend/requirements.txt** (all dependencies)
- [x] **backend/main.py** (health check endpoints)
- [x] **backend/config.py** (Railway PostgreSQL URL fix)
- [x] **.dockerignore** (optimized for clean builds)
- [x] **No Procfile, nixpacks.toml, or startup scripts**

## Railway Setup Steps

### 1. Create New Railway Project
- Go to [railway.app](https://railway.app)
- Click "New Project"
- Select "Deploy from GitHub repo"
- Choose repository: `ddkhua-maker/news-aggregator`
- Railway will detect the Dockerfile automatically

### 2. Add PostgreSQL Database
- In your Railway project, click "+ New"
- Select "Database" → "Add PostgreSQL"
- Railway will automatically provision the database
- Note: DATABASE_URL environment variable is automatically created

### 3. Connect PostgreSQL to Web Service
- Railway automatically links services in the same project
- Verify DATABASE_URL is available in your web service environment variables
- The config.py file handles postgres:// → postgresql:// conversion automatically

### 4. Add Environment Variables
Navigate to your web service → Variables tab and add:

**Required:**
```
OPENAI_API_KEY=your-openai-api-key-here
```

**Recommended:**
```
ENVIRONMENT=production
MAX_ARTICLES_PER_FEED=10
FETCH_INTERVAL_MINUTES=30
```

**For Production CORS (optional - set after you have a frontend domain):**
```
CORS_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com
```

### 5. Deploy
- Railway will automatically deploy after you add environment variables
- Watch the build logs in the Deployments tab
- Build should complete in ~30-60 seconds

### 6. Check Deployment Logs
Look for these success indicators:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Database initialized successfully
INFO:     Application started in production mode
INFO:     Uvicorn running on http://0.0.0.0:XXXX
```

### 7. Test Deployment
- Click "Generate Domain" in Railway to get your public URL
- Open the URL in your browser
- You should see: `{"status": "healthy", "service": "iGaming News Aggregator"}`
- Test health endpoint: `https://your-url.railway.app/health`
- Test API docs: `https://your-url.railway.app/docs`

## Expected Results

### Build Process
- **Build Time:** ~30-60 seconds
- **Image Size:** ~400-500 MB (Python 3.11-slim + dependencies)
- **Build Steps:**
  1. Pull python:3.11-slim base image
  2. Install system dependencies (gcc, postgresql-client)
  3. Install Python dependencies from requirements.txt
  4. Copy application code
  5. Set working directory to /app/backend
  6. Define CMD to run uvicorn

### Runtime
- **Container Startup:** ~2-5 seconds
- **Health Check at `/`:** Returns `{"status": "healthy", "service": "iGaming News Aggregator"}`
- **Health Check at `/health`:** Returns `{"status": "ok"}`
- **Database Connection:** Automatic via DATABASE_URL
- **Port:** Railway automatically assigns and uses PORT environment variable

## API Endpoints Available

Once deployed, these endpoints will be available:

- `GET /` - Health check
- `GET /health` - Simple health status
- `GET /api/articles` - Get articles with pagination
- `POST /api/fetch-news` - Manually trigger RSS feed fetch
- `POST /api/generate-summaries` - Generate AI summaries
- `POST /api/create-digest` - Create daily digest
- `GET /api/digest/{date}` - Get digest for specific date
- `GET /api/sources` - List all RSS feed sources
- `POST /api/search` - Semantic search for articles
- `GET /docs` - Interactive API documentation (Swagger UI)

## Testing the Deployment

### 1. Test Health Endpoints
```bash
curl https://your-url.railway.app/
curl https://your-url.railway.app/health
```

### 2. Fetch News Articles
```bash
curl -X POST https://your-url.railway.app/api/fetch-news
```

### 3. View Articles
```bash
curl https://your-url.railway.app/api/articles?limit=10
```

### 4. Generate Summaries
```bash
curl -X POST https://your-url.railway.app/api/generate-summaries
```

### 5. Create Daily Digest
```bash
curl -X POST https://your-url.railway.app/api/create-digest
```

## Troubleshooting

### Build Fails
- Check Railway build logs for errors
- Verify Dockerfile syntax
- Ensure requirements.txt has all dependencies

### Container Crashes on Startup
- Check deployment logs for Python errors
- Verify OPENAI_API_KEY is set
- Check DATABASE_URL is available
- Look for missing dependencies

### Database Connection Issues
- Verify PostgreSQL service is running
- Check DATABASE_URL environment variable exists
- Ensure config.py URL conversion is working (postgres:// → postgresql://)

### Health Checks Fail
- Check if PORT environment variable is set correctly
- Verify uvicorn is binding to 0.0.0.0 (not 127.0.0.1)
- Check container logs for startup errors

## Post-Deployment Tasks

1. **Test all API endpoints** via `/docs` interface
2. **Run initial RSS feed fetch** via `/api/fetch-news`
3. **Generate summaries** for fetched articles via `/api/generate-summaries`
4. **Set up scheduled jobs** (optional):
   - Use Railway cron jobs or external service
   - Fetch news every 30 minutes
   - Generate summaries daily
5. **Monitor logs** for any errors or warnings
6. **Set up custom domain** (optional) in Railway settings
7. **Configure CORS_ORIGINS** if deploying a separate frontend

## Security Notes

- ✅ Rate limiting enabled on all endpoints
- ✅ CORS configured for production (set CORS_ORIGINS)
- ✅ Security headers middleware active
- ✅ Input validation with Pydantic models
- ✅ No debug mode in production
- ✅ Environment-based configuration
- ⚠️ Keep OPENAI_API_KEY secure - never commit to git
- ⚠️ PostgreSQL credentials managed by Railway (automatic)

## Deployment Complete! 🎉

Your iGaming News Aggregator is now live on Railway!

**Next Steps:**
1. Share the API URL with your team
2. Build a frontend to consume the API
3. Set up monitoring and alerts
4. Schedule regular RSS fetches
5. Monitor OpenAI API usage and costs
