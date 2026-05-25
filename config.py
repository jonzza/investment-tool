"""Configuration for news investor MVP."""
from pathlib import Path

# RSS feeds - small but diverse initial set
RSS_FEEDS = [
    # Finland
    {"name": "Kauppalehti", "url": "https://www.kauppalehti.fi/rss/main.xml", "region": "FI"},
    {"name": "Yle Talous", "url": "https://yle.fi/uutiset/rss/uutiset.rss?osasto=talous", "region": "FI"},
    {"name": "Talouselämä", "url": "https://www.talouselama.fi/rss.xml", "region": "FI"},

    # USA / Global
    {"name": "Reuters Business", "url": "https://feeds.reuters.com/reuters/businessNews", "region": "GLOBAL"},
    {"name": "CNBC Top News", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html", "region": "US"},
    {"name": "MarketWatch", "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories", "region": "US"},

    # Europe
    {"name": "FT Europe", "url": "https://www.ft.com/world/europe?format=rss", "region": "EU"},
]

# Claude models (update if newer ones are released)
MODEL_SCREENING = "claude-haiku-4-5-20251001"   # Cheap, fast, for screening
MODEL_ANALYSIS = "claude-sonnet-4-6"            # Deep analysis and synthesis

# Thresholds
MAX_ARTICLES_PER_FEED = 15        # How many latest articles to fetch per feed
SIGNIFICANCE_THRESHOLD = 7         # Only articles scoring >= this go to deep analysis
MAX_ANALYSES = 20                  # Max deep analyses per run (cost cap)

# Request concurrency
CONCURRENT_SCREENINGS = 5          # How many Haiku calls to run in parallel

# Paths
PROJECT_ROOT = Path(__file__).parent
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"
