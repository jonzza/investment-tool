"""Main pipeline: fetch -> screen -> analyze -> synthesize -> save report."""
import asyncio
import sys
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

from config import REPORTS_DIR, LOGS_DIR
from fetcher import fetch_all
from screener import screen_all
from analyzer import analyze_top
from synthesizer import synthesize


def setup_logging():
    LOGS_DIR.mkdir(exist_ok=True)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(LOGS_DIR / "run_{time:YYYY-MM-DD}.log", level="DEBUG", rotation="1 day")


async def run_pipeline() -> str:
    """Run the full pipeline and return the report Markdown."""
    logger.info("=== Starting pipeline ===")

    # Stage 0: fetch
    articles = fetch_all()
    if not articles:
        logger.error("No articles fetched. Check feed configuration.")
        return "# Virhe\n\nUutisia ei voitu hakea."

    # Stage 1: screen
    screened = await screen_all(articles)

    # Stage 2: analyze top
    analyzed = await analyze_top(screened)

    # Stage 3: synthesize
    report_md = synthesize(analyzed)

    logger.info("=== Pipeline complete ===")
    return report_md


def save_report(content: str) -> str:
    """Save report to reports/YYYY-MM-DD.md, return file path."""
    REPORTS_DIR.mkdir(exist_ok=True)
    filename = REPORTS_DIR / f"{datetime.now():%Y-%m-%d}.md"
    filename.write_text(content, encoding="utf-8")
    logger.info(f"Report saved to {filename}")
    return str(filename)


def main():
    load_dotenv()
    setup_logging()
    report = asyncio.run(run_pipeline())
    path = save_report(report)
    print(f"\n✅ Report saved: {path}\n")
    print("=" * 70)
    print(report[:2000])
    if len(report) > 2000:
        print("\n... (truncated, see full report in file)")


if __name__ == "__main__":
    main()
