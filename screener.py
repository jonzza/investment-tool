"""Stage 1: Cheap screening with Haiku. Classifies and scores each article."""
import asyncio
import json
from dataclasses import dataclass, field
from typing import Optional

from anthropic import AsyncAnthropic
from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from config import MODEL_SCREENING, CONCURRENT_SCREENINGS
from fetcher import Article


class ScreeningResult(BaseModel):
    """Structured output from Haiku screening."""
    relevant: bool
    significance: int = Field(ge=1, le=10)
    region: str  # FI/EU/US/ASIA/GLOBAL
    sectors: list[str] = Field(default_factory=list)
    tickers: list[str] = Field(default_factory=list)
    reasoning: str


@dataclass
class ScreenedArticle:
    """Article paired with screening result."""
    article: Article
    screening: ScreeningResult


SCREENING_SYSTEM_PROMPT = """You are an investment research assistant screening news articles.

You receive a news article (which may be in Finnish, English, or another language).
Evaluate its significance for investors and return a JSON object.

Rules:
- "relevant": true only if the article may affect markets, a sector, a company, or
  macroeconomic conditions. Sports, lifestyle, crime, politics-without-economic-angle
  should be marked false.
- "significance": 1-10 scale
    1-3 = minor, local or niche sector
    4-6 = moderate, may move individual stocks
    7-8 = significant, may move a sector or index
    9-10 = exceptional, may move global markets (rare)
- "region": one of "FI", "EU", "US", "ASIA", "GLOBAL"
- "sectors": list from {technology, energy, finance, healthcare, industrials,
  consumer, real_estate, materials, utilities, telecom, crypto, macro}
- "tickers": stock symbols explicitly mentioned (e.g. "NVDA", "NOKIA.HE")
- "reasoning": one sentence in English explaining the score

Be conservative with high scores. Most articles are 3-6. A 9-10 is reserved for
major central bank decisions, crisis events, or massive M&A.

Return ONLY a JSON object, no markdown, no other text."""


def _build_user_message(article: Article) -> str:
    return f"""Title: {article.title}
Source: {article.source}
Region hint: {article.region}
Published: {article.published_at}

Content:
{article.summary}"""


async def screen_article(
    client: AsyncAnthropic,
    article: Article,
    semaphore: asyncio.Semaphore,
) -> Optional[ScreenedArticle]:
    """Screen one article with Haiku."""
    async with semaphore:
        try:
            response = await client.messages.create(
                model=MODEL_SCREENING,
                max_tokens=400,
                system=SCREENING_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": _build_user_message(article)}],
            )
            raw_text = response.content[0].text.strip()

            # Strip code fences if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:].strip()

            data = json.loads(raw_text)
            screening = ScreeningResult(**data)
            return ScreenedArticle(article=article, screening=screening)

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed for '{article.title[:50]}': {e}")
            return None
        except ValidationError as e:
            logger.warning(f"Validation failed for '{article.title[:50]}': {e}")
            return None
        except Exception as e:
            logger.error(f"Screening failed for '{article.title[:50]}': {e}")
            return None


async def screen_all(articles: list[Article]) -> list[ScreenedArticle]:
    """Screen all articles concurrently."""
    client = AsyncAnthropic()
    semaphore = asyncio.Semaphore(CONCURRENT_SCREENINGS)

    logger.info(f"Screening {len(articles)} articles with {MODEL_SCREENING}...")
    tasks = [screen_article(client, a, semaphore) for a in articles]
    results = await asyncio.gather(*tasks)

    successful = [r for r in results if r is not None]
    logger.info(
        f"Screening done: {len(successful)}/{len(articles)} successful. "
        f"Relevant: {sum(1 for r in successful if r.screening.relevant)}"
    )
    return successful


if __name__ == "__main__":
    # Standalone test
    from fetcher import fetch_all
    articles = fetch_all()
    results = asyncio.run(screen_all(articles[:10]))
    for r in results:
        s = r.screening
        print(f"[sig={s.significance} {s.region} relevant={s.relevant}] {r.article.title[:80]}")
        print(f"  sectors={s.sectors} tickers={s.tickers}")
        print(f"  -> {s.reasoning}")
        print()
