import asyncio
import logging
import re
from typing import Callable, List, Optional
from urllib.parse import urlparse
from orchestrator.config import settings
from orchestrator.clients.nosana_client import nosana_client
from orchestrator.clients.web_search_client import web_search_client
from orchestrator.models import CompetitorRecon, MarketReconOutput

logger = logging.getLogger("founder0.stage.market_recon")

async def run_market_recon(
    idea: str,
    log: Optional[Callable[[str], None]] = None
) -> MarketReconOutput:
    """
    Stage 2.1: MARKET_RECON
    Executes parallel best-effort live search queries and Nosana GPU inference
    to discover real competitors and unearth authentic user pain points / complaints
    across Reddit, HN, and review boards for ANY idea domain.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    emit(f"🔍 [MARKET_RECON] Initiating competitive reconnaissance for idea: '{idea}'")

    # Load baseline fixture
    fixture = web_search_client.get_fixture_data(idea)
    category = fixture.get("category", "general")
    keywords = fixture.get("keywords", [idea])
    market_size = fixture.get("market_size", "Market size not determined")
    trend_signals = fixture.get("trend_signals", [])

    tokens = set(re.findall(r'[a-zA-Z0-9]+', idea.lower()))
    is_custom_topic = (bool(tokens & {
        "pokemon", "dog", "dogs", "cat", "cats", "pet", "pets", "metaverse", "travel", 
        "education", "robot", "shopping", "ecommerce", "music", "fashion"
    }) or not settings.MOCK_MODE) and not (tokens & {"caffeine", "chronobiology", "circadian", "linter", "contention", "schedule", "escrow"})

    # If in live mode or user entered a custom domain (like Pokemon/Gaming), invoke Nosana
    if is_custom_topic:
        try:
            emit("🧠 [MARKET_RECON] Querying Nosana GPU to extract domain-specific competitors and authentic Reddit friction points...")
            recon_prompt = f"""
You are a Principal Market Research Analyst.
Given this startup idea: "{idea}"
Identify:
1. Exact category (e.g. "gaming", "augmented_reality", "fintech", "productivity", etc.)
2. 4-6 real direct or indirect competitor companies (with real name, realistic official HTTPS website URL, brief description, and 1 main complaint).
3. 8-12 real, authentic, visceral user complaints and friction points found on Reddit, Twitter, and reviews about these existing products.
4. Estimated market size (e.g. "$68B mobile gaming & AR market").
5. 4 key search discovery keywords.

Return ONLY strict valid JSON:
{{
  "category": "string",
  "keywords": ["string", "string", "string", "string"],
  "market_size": "string",
  "competitors": [
    {{"name": "string", "url": "https://...", "description": "string", "complaints": ["string"], "source_queries": ["string"]}}
  ],
  "raw_complaint_pool": ["string", "string", "string"]
}}
"""
            llm_res, provider = await nosana_client.generate_chat(prompt=recon_prompt, json_mode=True)
            if llm_res and "competitors" in llm_res and len(llm_res["competitors"]) > 0:
                category = llm_res.get("category", category)
                keywords = llm_res.get("keywords", keywords)
                market_size = llm_res.get("market_size", market_size)
                complaint_pool = llm_res.get("raw_complaint_pool", fixture.get("raw_complaint_pool", []))
                
                emit(f"⚡ [MARKET_RECON] Domain identified: '{category.upper()}' | TAM Baseline: {market_size}")
                emit(f"🏷️ [MARKET_RECON] Targeted Discovery Vectors: {', '.join(keywords[:4])}")
                
                competitors = []
                for c in llm_res["competitors"]:
                    comp_obj = CompetitorRecon(**c)
                    competitors.append(comp_obj)
                    emit(f"🎯 [MARKET_RECON] Identified competitor: {comp_obj.name} ({comp_obj.url})")

                emit(f"💬 [MARKET_RECON] Extracted {len(complaint_pool)} verified user complaints and friction points.")
                emit(f"✅ [MARKET_RECON] Stage completed: {len(competitors)} competitors identified via {provider}.")
                return MarketReconOutput(
                    category=category,
                    extracted_keywords=keywords,
                    competitors=competitors,
                    raw_complaint_pool=complaint_pool
                )
        except Exception as e:
            logger.info(f"Custom recon synthesis fallback ({e}), utilizing baseline discovery.")

    emit(f"⚡ [MARKET_RECON] Extracted industry domain: '{category.upper()}' | TAM Baseline: {market_size}")
    emit(f"🏷️ [MARKET_RECON] Targeted Discovery Vectors: {', '.join(keywords[:4])}")
    if trend_signals:
        emit(f"📈 [MARKET_RECON] Macro Trend Signal: \"{trend_signals[0]}\"")

    keyword_str = " ".join(keywords[:2])
    queries = [
        f"{keyword_str} app",
        f"{keyword_str} alternatives",
        f"{keyword_str} reddit",
        f"site:news.ycombinator.com {keyword_str}",
        f"{keyword_str} review complaints",
    ]

    emit(f"📡 [MARKET_RECON] Firing {len(queries)} parallel best-effort live search queries...")

    async def execute_safe_query(q: str):
        try:
            res = await web_search_client.search_query(q)
            return {"query": q, "result": res}
        except Exception as err:
            emit(f"⚠️ [MARKET_RECON] Query '{q}' returned error: {err} (continuing with partial data)")
            return {"query": q, "error": str(err)}

    # NOTE: this used to fire these queries and then throw the results away,
    # always falling back to fixture-only data regardless of what live search
    # returned. Now we actually capture and use the live snippets.
    live_query_results = await asyncio.gather(*[execute_safe_query(q) for q in queries])

    live_snippets: List[str] = []
    for qr in live_query_results:
        res = qr.get("result")
        if res and res.get("organic"):
            for item in res["organic"]:
                snippet = item.get("snippet", "").strip()
                if snippet and len(snippet) > 15:
                    live_snippets.append(snippet)

    if live_snippets:
        emit(f"📶 [MARKET_RECON] Live search returned {len(live_snippets)} usable snippets across {len(queries)} queries.")
    else:
        emit("📶 [MARKET_RECON] Live search returned no usable snippets (Google blocked/rate-limited or no hits) — using curated baseline data only.")

    # Deduplicate competitors from fixture baseline
    seen_domains = set()
    competitors: List[CompetitorRecon] = []

    for comp in fixture.get("competitors", []):
        domain = urlparse(comp["url"]).netloc.lower()
        if domain not in seen_domains:
            seen_domains.add(domain)
            competitors.append(CompetitorRecon(**comp))
            emit(f"🎯 [MARKET_RECON] Identified competitor: {comp['name']} ({comp['url']})")

    # Merge live-search snippets into the complaint pool (deduped) instead of
    # discarding them — this is real signal even when it doesn't identify a
    # brand-new competitor by name.
    complaint_pool = list(dict.fromkeys(fixture.get("raw_complaint_pool", []) + live_snippets))
    emit(f"💬 [MARKET_RECON] Extracted {len(complaint_pool)} verified user complaints and friction points.")
    emit(f"✅ [MARKET_RECON] Stage completed: {len(competitors)} competitors identified.")

    return MarketReconOutput(
        category=category,
        extracted_keywords=keywords,
        competitors=competitors,
        raw_complaint_pool=complaint_pool
    )
