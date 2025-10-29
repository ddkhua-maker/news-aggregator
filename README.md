# iGaming News Aggregator

A comprehensive web application that aggregates iGaming industry news from 11 RSS feeds, provides AI-powered summaries using Claude, and presents them in a clean, modern interface with daily digest generation.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

- 📰 **Multi-Source Aggregation**: Automatically fetches news from 11 iGaming RSS feeds
- 🤖 **AI-Powered Summaries**: Claude AI generates concise summaries for each article
- 📊 **Daily Digest**: Automated daily digest with topic grouping and highlights
- 🎨 **Modern UI**: Clean, responsive interface built with Tailwind CSS and Alpine.js
- 🔍 **Smart Filtering**: Filter articles by source
- 📱 **Mobile-Friendly**: Fully responsive design
- 💾 **SQLite Database**: Easy setup with PostgreSQL migration path

## Tech Stack

### Backend
- **Framework**: FastAPI 0.115.0
- **Database**: SQLite / SQLAlchemy 2.0.36
- **RSS Parsing**: feedparser 6.0.11
- **AI**: Anthropic Claude API (claude-sonnet-4-20250514)
- **Language**: Python 3.9+

### Frontend
- **Framework**: Alpine.js 3.x
- **Styling**: Tailwind CSS (CDN)
- **Architecture**: Single-page application (SPA)

### RSS News Sources (11 feeds)
- Yogonet (Europe, US, Latin America, Asia, Online Gaming)
- European Gaming
- iGaming Business
- CDC Gaming Reports
- Casino Beats
- SBC News
- Slot Beats

## Project Structure

```
news-aggregator/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI application & API endpoints
│   ├── config.py            # Configuration (11 RSS feeds, API keys)
│   ├── database.py          # SQLAlchemy database setup
│   ├── models.py            # Article & DigestEntry models
│   ├── rss_parser.py        # RSS feed parser & article extraction
│   ├── claude_summarizer.py # Claude API integration
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # Main SPA page
│   └── static/
│       ├── styles.css       # Custom CSS & responsive design
│       └── app.js           # Alpine.js application logic
├── .env                     # Environment variables (not in git)
├── .env.example             # Environment variables template
├── .gitignore
├── run.sh                   # Startup script
└── README.md
```

## Quick Start

### Prerequisites
- **Python 3.9+** ([Download](https://www.python.org/downloads/))
- **Claude API Key** ([Get one here](https://console.anthropic.com/))

### Installation

1. **Clone or download this project**
   ```bash
   cd news-aggregator
   ```

2. **Set up environment variables**

   Edit the `.env` file and add your Claude API key:
   ```bash
   CLAUDE_API_KEY=sk-ant-your-actual-api-key-here
   ```

   **Important**: Replace `sk-ant-xxxxx` with your real API key from Anthropic.

3. **Run the application**

   **Option A - Using the startup script (recommended):**
   ```bash
   # Linux/Mac
   chmod +x run.sh
   ./run.sh

   # Windows (Git Bash)
   bash run.sh

   # Windows (PowerShell/CMD) - run commands manually:
   cd backend
   python -m pip install -r requirements.txt
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   **Option B - Manual setup:**
   ```bash
   # Create virtual environment (optional but recommended)
   python -m venv venv

   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate

   # Install dependencies
   cd backend
   pip install -r requirements.txt

   # Run the server
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access the application**
   - **Main App**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs
   - **Alternative API Docs**: http://localhost:8000/redoc

## How to Use

### Frontend Interface

1. **Fetch Latest News**
   - Click "Fetch Latest News" button
   - System fetches articles from all 11 RSS feeds
   - New articles are saved to database (duplicates automatically skipped)

2. **Generate Summaries**
   - Click "Generate Summaries" button
   - Claude AI creates concise summaries for articles without summaries
   - Summaries appear in article cards with a green "✓ Summarized" badge

3. **Create Daily Digest**
   - Click "Create Daily Digest" button
   - Claude AI analyzes all recent articles
   - Generates organized digest grouped by topics (regulations, mergers, product launches, etc.)
   - Digest appears in the sidebar

4. **Browse Articles**
   - Filter by source using the dropdown
   - View article titles, sources, publish dates, and summaries
   - Click "Read Full Article" to open original source

### API Endpoints

#### Articles
- `GET /api/articles?limit=20&offset=0&source=` - List articles with pagination
- `POST /api/fetch-news` - Trigger RSS feed fetch
- `POST /api/generate-summaries?limit=50` - Generate summaries for articles
- `GET /api/sources` - List all RSS feed sources

#### Digest
- `POST /api/create-digest` - Create daily digest for today
- `GET /api/digest/{date}` - Get digest for specific date (YYYY-MM-DD)

#### Example API Calls

```bash
# Fetch latest news
curl -X POST http://localhost:8000/api/fetch-news

# Generate summaries
curl -X POST http://localhost:8000/api/generate-summaries

# Get articles
curl http://localhost:8000/api/articles?limit=10

# Create daily digest
curl -X POST http://localhost:8000/api/create-digest

# Get digest for specific date
curl http://localhost:8000/api/digest/2025-01-15
```

## Configuration

### Environment Variables (.env)

```bash
# Required: Your Claude API key
CLAUDE_API_KEY=sk-ant-your-key-here

# Optional: Database configuration
DATABASE_URL=sqlite:///./news_aggregator.db

# Optional: Application settings
FETCH_INTERVAL_MINUTES=30
MAX_ARTICLES_PER_FEED=10
SUMMARY_MAX_TOKENS=500
```

### RSS Feeds

All 11 RSS feeds are pre-configured in `backend/config.py`:
- Yogonet (5 regional feeds)
- European Gaming
- iGaming Business
- CDC Gaming Reports
- Casino Beats
- SBC News
- Slot Beats

To modify feeds, edit the `RSS_FEEDS` list in `backend/config.py`.

## Database Schema

### Article Model
- `id` - Primary key
- `title` - Article title
- `link` - Unique URL
- `source` - RSS feed source name
- `published_date` - Publication date
- `content` - Original article content/description
- `summary` - Claude-generated summary
- `created_at`, `updated_at` - Timestamps

### DigestEntry Model
- `id` - Primary key
- `digest_date` - Date (unique)
- `content` - Full daily digest from Claude
- `article_count` - Number of articles in digest
- `created_at` - Timestamp

## Development

### Dependencies

The application requires these Python packages (in `requirements.txt`):
```
fastapi==0.115.0
uvicorn==0.32.0
feedparser==6.0.11
sqlalchemy==2.0.36
anthropic==0.39.0
python-dotenv==1.0.1
requests==2.32.3
```

### Database Migration to PostgreSQL

To switch from SQLite to PostgreSQL:

1. Install PostgreSQL driver:
   ```bash
   pip install psycopg2-binary
   ```

2. Update `.env`:
   ```bash
   DATABASE_URL=postgresql://username:password@localhost:5432/news_aggregator
   ```

3. Restart the application (tables will be created automatically)

### Project Architecture

- **Backend**: FastAPI handles all API endpoints and business logic
- **RSS Parser**: Fetches and parses 11 RSS feeds in parallel
- **Claude Integration**: Generates summaries and daily digests
- **Frontend**: Alpine.js SPA with reactive state management
- **Database**: SQLAlchemy ORM with automatic schema creation

## Troubleshooting

### Common Issues

1. **"Claude API client not initialized"**
   - Make sure `.env` file exists with `CLAUDE_API_KEY`
   - Verify API key is valid

2. **"No module named 'fastapi'"**
   - Run: `pip install -r backend/requirements.txt`

3. **"Address already in use"**
   - Port 8000 is occupied. Stop other servers or change port:
   - `uvicorn main:app --port 8001`

4. **Database locked error**
   - Close any other connections to the database
   - Delete `news_aggregator.db` to start fresh

## API Rate Limits

- Claude API has rate limits based on your plan
- The app includes 0.5s delays between requests
- Rate limit errors are caught and logged

## Future Enhancements

- [ ] Background scheduler for automatic feed updates
- [ ] Search functionality across articles
- [ ] User authentication and saved preferences
- [ ] Email digest subscriptions
- [ ] Article categorization and tagging
- [ ] Sentiment analysis
- [ ] Export digest as PDF
- [ ] Multi-language support

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues or questions:
- Open an issue on GitHub
- Check API documentation at `/docs`

---

**Built with ❤️ using FastAPI, Claude AI, and Alpine.js**
