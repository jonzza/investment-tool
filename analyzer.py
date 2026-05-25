"""Stage 2: Deep analysis with Sonnet for the most significant articles."""
import asyncio
import json
from dataclasses import dataclass
from typing import Optional, Literal

from anthropic import AsyncAnthropic
from loguru import logger
from pydantic import BaseModel, Field, ValidationError

from config import MODEL_ANALYSIS, SIGNIFICANCE_THRESHOLD, MAX_ANALYSES
from screener import ScreenedArticle


class Impact(BaseModel):
    target: str           # company / sector / region affected
    mechanism: str        # 1-2 sentences why
    confidence: Literal["low", "medium", "high"]


class DeepAnalysis(BaseModel):
    summary: str          # 2-3 sentences, English
    key_facts: list[str]  # concrete facts from the text
    positive_impact: list[Impact] = Field(default_factory=list)
    negative_impact: list[Impact] = Field(default_factory=list)
    time_horizon: Literal["immediate", "short_term", "long_term"]
    uncertainty_notes: str


@dataclass
class AnalyzedArticle:
    screened: ScreenedArticle
    analysis: DeepAnalysis


ANALYSIS_SYSTEM_PROMPT = """You analyze a single news article in depth from an investor's perspective.

Your task is to produce a structured analysis of what the article may mean for
different actors. Stay strictly with facts in the text - if something is not
stated, do not invent it.

Return ONLY a JSON object with this structure:
{
  "summary": "2-3 sentences in English on the core of the article",
  "key_facts": ["list of concrete facts from the text, including numbers"],
  "positive_impact": [
    {
      "target": "who/what benefits (company, sector, region)",
      "mechanism": "why - 1-2 sentence mechanism",
      "confidence": "low|medium|high"
    }
  ],
  "negative_impact": [{"target": "...", "mechanism": "...", "confidence": "..."}],
  "time_horizon": "immediate|short_term|long_term",
  "uncertainty_notes": "what we do not know, what could change the interpretation"
}

CRITICAL:
- Never invent numbers or facts not in the text.
- If uncertain, set "confidence": "low".
- "uncertainty_notes" is mandatory - investing always involves uncertainty.
- Empty lists are fine if no clear positive/negative impacts exist.
- Return JSON only, no markdown, no other text."""


def _build_user_message(screened: ScreenedArticle) -> str:
    a = screened.article
    s = screened.screening
    return f"""Article:
Title: {a.title}
Source: {a.source} ({a.region})
Published: {a.published_at}
URL: {a.url}

Pre-screening notes:
- Sectors: {s.sectors}
- Tickers mentioned: {s.tickers}
- Initial significance: {s.significance}/10

Content:
{a.summary}"""


async def analyze_one(
    client: AsyncAnthropic,
    screened: ScreenedArticle,
    semaphore: asyncio.Semaphore,
) -> Optional[AnalyzedArticle]:
    async with semaphore:
        try:
            response = await client.messages.create(
                model=MODEL_ANALYSIS,
                max_tokens=1500,
                system=ANALYSIS_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": _build_user_message(screened)}],
            )
            raw_text = response.content[0].text.strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:].strip()

            data = json.loads(raw_text)
            analysis = DeepAnalysis(**data)
            return AnalyzedArticle(screened=screened, analysis=analysis)

        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Analysis parse failed for '{screened.article.title[:50]}': {e}")
            return None
        except Exception as e:
            logger.error(f"Analysis failed for '{screened.article.title[:50]}': {e}")
            return None


async def analyze_top(screened_articles: list[ScreenedArticle]) -> list[AnalyzedArticle]:
    """Pick the most significant articles and analyze them in depth."""
    relevant = [
        s for s in screened_articles
        if s.screening.relevant and s.screening.significance >= SIGNIFICANCE_THRESHOLD
    ]
    relevant.sort(key=lambda s: s.screening.significance, reverse=True)
    selected = relevant[:MAX_ANALYSES]

    logger.info(
        f"Selected {len(selected)} articles for deep analysis "
        f"(threshold={SIGNIFICANCE_THRESHOLD}, max={MAX_ANALYSES})"
    )

    if not selected:
        return []

    client = AsyncAnthropic()
    semaphore = asyncio.Semaphore(3)  # lower concurrency for the more expensive model

    tasks = [analyze_one(client, s, semaphore) for s in selected]
    results = await asyncio.gather(*tasks)
    successful = [r for r in results if r is not None]
    logger.info(f"Deep analysis done: {len(successful)}/{len(selected)} successful")
    return successful


if __name__ == "__main__":
    # Standalone test
    import asyncio as _asyncio
    from fetcher import fetch_all
    from screener import screen_all

    articles = fetch_all()
    screened = _asyncio.run(screen_all(articles))
    analyzed = _asyncio.run(analyze_top(screened))
    for a in analyzed:
        print(f"=== {a.screened.article.title}")
        print(a.analysis.summary)
        print(f"  Positive: {len(a.analysis.positive_impact)}, Negative: {len(a.analysis.negative_impact)}")
