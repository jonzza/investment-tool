"""Stage 3: Synthesize all deep analyses into a single daily Finnish report."""
from datetime import datetime
from anthropic import Anthropic
from loguru import logger

from config import MODEL_ANALYSIS
from analyzer import AnalyzedArticle


SYNTHESIS_SYSTEM_PROMPT = """You synthesize a daily investment briefing in FINNISH
based on provided analyses.

You will receive a numbered list of article analyses. Your job is to produce a
concise, readable Finnish-language daily briefing (~5 minute read).

CRITICAL RULES:
1. Every claim in the report must be traceable to one of the provided analyses
   via a numbered citation like [1], [3]. If you can't cite it, leave it out.
2. Never invent numbers, names, or facts not present in the analyses.
3. Do not give investment advice (no "buy", "sell", "recommend").
4. Use conditional language for uncertain matters ("voi vaikuttaa", "saattaa hyötyä").
5. Keep company names and tickers in their original form (e.g. "Nvidia", "NVDA"),
   do not decline them awkwardly in Finnish.
6. Use established Finnish financial terms where they exist (korko, tulosjulkistus,
   ohjeistus, osakekurssi). Keep English terms only when no good Finnish equivalent.

Structure (Markdown):

# Päivän markkinakatsaus – {date}

## Tiivistelmä
[3-5 lausetta päivän tärkeimmistä asioista]

## Globaalit markkinat
[2-4 kappaletta merkittävimmistä globaaleista signaaleista, jos sellaisia on]

## Yhdysvallat
[USA-spesifit asiat; jätä pois jos ei aineistoa]

## Eurooppa
[EU-spesifit asiat; jätä pois jos ei aineistoa]

## Suomi
[Suomen markkinaa koskevat asiat; jätä pois jos ei aineistoa]

## Toimialat
[Lyhyt katsaus 3-6 toimialaan: missä positiivisia, missä negatiivisia signaaleja]

## Huomioitavaa
[Epävarmuustekijät, ristiriitaiset signaalit, mitä seurata]

Style:
- Asiallinen, ei sensaationhakuinen.
- Konkreettiset luvut kun saatavilla.
- Lyhyet kappaleet, yksi ajatus per kappale.
- Lähdeviitteet [n] heti väitteen perään, ennen pistettä."""


def _format_analyses_for_prompt(analyzed: list[AnalyzedArticle]) -> str:
    """Format analyses as a numbered list for the synthesis prompt."""
    lines = []
    for i, a in enumerate(analyzed, start=1):
        art = a.screened.article
        an = a.analysis
        lines.append(f"--- [{i}] ---")
        lines.append(f"Source: {art.source} ({art.region})")
        lines.append(f"Title: {art.title}")
        lines.append(f"URL: {art.url}")
        lines.append(f"Summary: {an.summary}")
        lines.append(f"Key facts: {an.key_facts}")
        if an.positive_impact:
            lines.append("Positive impacts:")
            for imp in an.positive_impact:
                lines.append(f"  - {imp.target}: {imp.mechanism} (confidence={imp.confidence})")
        if an.negative_impact:
            lines.append("Negative impacts:")
            for imp in an.negative_impact:
                lines.append(f"  - {imp.target}: {imp.mechanism} (confidence={imp.confidence})")
        lines.append(f"Time horizon: {an.time_horizon}")
        lines.append(f"Uncertainty: {an.uncertainty_notes}")
        lines.append("")
    return "\n".join(lines)


def _build_source_list(analyzed: list[AnalyzedArticle]) -> str:
    """Build a Markdown source list to append below the report."""
    lines = ["", "---", "", "## Lähteet", ""]
    for i, a in enumerate(analyzed, start=1):
        art = a.screened.article
        lines.append(f"[{i}] [{art.source}: {art.title}]({art.url})")
    return "\n".join(lines)


def synthesize(analyzed: list[AnalyzedArticle]) -> str:
    """Synthesize all analyses into a Finnish Markdown briefing."""
    if not analyzed:
        return "# Päivän markkinakatsaus\n\nEi merkittäviä uutisia analyysiin tänään.\n"

    date_str = datetime.now().strftime("%d.%m.%Y")
    user_message = (
        f"Today's date: {date_str}\n\n"
        f"Analyses ({len(analyzed)} articles):\n\n"
        f"{_format_analyses_for_prompt(analyzed)}\n\n"
        f"Now write the Finnish daily briefing following the structure in the system prompt."
    )

    client = Anthropic()
    logger.info(f"Synthesizing report from {len(analyzed)} analyses...")
    response = client.messages.create(
        model=MODEL_ANALYSIS,
        max_tokens=4000,
        system=SYNTHESIS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    report_body = response.content[0].text.strip()
    source_list = _build_source_list(analyzed)
    return report_body + "\n" + source_list
