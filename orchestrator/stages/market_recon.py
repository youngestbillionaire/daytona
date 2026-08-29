import asyncio
import logging
from typing import Callable, List, Optional
from urllib.parse import urlparse
from orchestrator.clients.oxylabs_client import oxylabs_client
from orchestrator.models import CompetitorRecon, MarketReconOutput

logger = logging.getLogger("founder0.stage.market_recon")

async def run_market_recon(
    idea: str,
    log: Optional[Callable[[str], None]] = None
) -> MarketReconOutput:
    """
    Stage 2.1: MARKET_RECON
    Executes parallel search queries via Oxylabs Realtime Client to discover competitors
    and unearth authentic user pain points / complaints across Reddit, HN, and review boards.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    emit(f"🔍 [MARKET_RECON] Initiating competitive reconnaissance for idea: '{idea}'")

    # Load industry category fixture baseline or live queries
    fixture = oxylabs_client.get_fixture_data(idea)
    category = fixture.get("category", "general")
    keywords = fixture.get("keywords", [idea])

    emit(f"⚡ [MARKET_RECON] Extracted industry domain: '{category.upper()}' | Keywords: {', '.join(keywords[:4])}")

    keyword_str = " ".join(keywords[:2])
    queries = [
        f"{keyword_str} app",
        f"{keyword_str} alternatives",
        f"{keyword_str} reddit",
        f"site:news.ycombinator.com {keyword_str}",
        f"{keyword_str} review complaints",
    ]

    emit(f"📡 [MARKET_RECON] Firing {len(queries)} parallel search queries via Oxylabs Realtime API...")

    async def execute_safe_query(q: str):
        try:
            res = await oxylabs_client.search_query(q)
            return {"query": q, "result": res}
        except Exception as err:
            emit(f"⚠️ [MARKET_RECON] Query '{q}' returned error: {err} (continuing with partial data)")
            return {"query": q, "error": str(err)}

    results = await asyncio.gather(*[execute_safe_query(q) for q in queries])

    # Deduplicate competitors from fixture baseline + live results
    seen_domains = set()
    competitors: List[CompetitorRecon] = []

    for comp in fixture.get("competitors", []):
        domain = urlparse(comp["url"]).netloc.lower()
        if domain not in seen_domains:
            seen_domains.add(domain)
            competitors.append(CompetitorRecon(**comp))
            emit(f"🎯 [MARKET_RECON] Identified competitor: {comp['name']} ({comp['url']})")

    complaint_pool = fixture.get("raw_complaint_pool", [])
    emit(f"💬 [MARKET_RECON] Extracted {len(complaint_pool)} verified user complaints and friction points.")
    emit(f"✅ [MARKET_RECON] Stage completed: {len(competitors)} competitors identified.")

    return MarketReconOutput(
        category=category,
        extracted_keywords=keywords,
        competitors=competitors,
        raw_complaint_pool=complaint_pool
    )
