# News Investor MVP

Fetches news from RSS feeds, screens them with Claude Haiku, analyzes the most important ones
with Sonnet, and writes a daily market digest in Finnish.

## Setup

1. **Clone the project into your own folder** (or create it manually).

2. **Create a virtual environment and install dependencies:**

   ```bash
   cd news-investor-mvp
   python -m venv venv
   source venv/bin/activate      # macOS/Linux
   # venv\Scripts\activate       # Windows
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** (copy `.env.example` as a template):

   ```bash
   cp .env.example .env
   ```

   Get an API key from https://console.anthropic.com/ and
   paste it into the `.env` file:

   ```
   ANTHROPIC_API_KEY=sk-ant-api03-...
   ```

   Also set a monthly spending limit (Spending limits) in the console -
   e.g. $30/month - as a safety net.

## Running

```bash
python main.py
```

A single run typically takes 2-5 minutes. The result is saved to
`reports/YYYY-MM-DD.md` and also printed to the console.

## Testing components separately

Each stage can be run on its own during development:

```bash
python fetcher.py        # Fetch RSS, print the first 5
python screener.py       # Fetch + screen 10 articles
python analyzer.py       # Fetch + screen + analyze
```

## Configuration

Adjust in `config.py`:
- `RSS_FEEDS` - which news sources are used
- `SIGNIFICANCE_THRESHOLD` - how high a score is required for deep analysis (default 7)
- `MAX_ANALYSES` - maximum number of deep analyses per run (cost cap, default 20)
- `MODEL_SCREENING` / `MODEL_ANALYSIS` - the Claude models used

## Cost estimate

Rough estimate per run:
- Stage 1 (Haiku screening of ~100 articles): ~$0.05-0.15
- Stage 2 (Sonnet deep analysis of 10-20 articles): ~$0.20-0.50
- Stage 3 (Sonnet synthesis): ~$0.05-0.15

**Total ~$0.30-0.80/run, i.e. €10-25/month** with one daily run.

## Known limitations (MVP)

- No database - it doesn't remember what it showed yesterday, so it may show the same article again
- No email - the report goes to a file only
- Uses only the short intro text provided by the RSS feeds, does not fetch the full article
- No stock prices or earnings reports
- No prompt caching

These will come in later stages.

## Security

- `.env` is not committed to Git (`.gitignore` takes care of this)
- API keys are personal - do not share them
- Set a spending limit in the Anthropic console
