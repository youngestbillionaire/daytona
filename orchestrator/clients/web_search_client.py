import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx
from orchestrator.config import settings

logger = logging.getLogger("founder0.webscraper")


class WebSearchClient:
    """
    Lightweight web research client for FOUNDER-0's market recon stage.

    HONEST NOTE ON WHAT THIS ACTUALLY DOES:
    This client does NOT call any paid scraping/search API (Oxylabs or otherwise).
    It does two things:
      1. Best-effort live search via Google's HTML results page (no API key required,
         no auth, subject to their rate limits and markup changes breaking parsing —
         and to occasional CAPTCHA challenges, which are treated as a failed request).
      2. Falls back to curated local fixture data (fixtures/market_recon/*.json) when
         live search fails, times out, or returns nothing useful.

    If you want real paid-API search/scraping (Oxylabs, SerpAPI, Bright Data, etc.),
    swap the implementation of `search_query` / `scrape_page` below for a real client
    call using that provider's SDK and credentials. As shipped, this class has no
    external API dependency and no API key requirement at all.
    """

    def __init__(self):
        self.mock_mode = settings.MOCK_MODE
        self.fixtures_dir = Path(__file__).resolve().parent.parent.parent / "fixtures" / "market_recon"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }

    def _match_category(self, query: str) -> str:
        """Infer industry category from user prompt via keyword matching."""
        q = query.lower().strip()
        if q in ["productivity", "fintech", "social", "health", "devtools", "trading"]:
            return q
        tokens = set(re.findall(r'[a-zA-Z0-9]+', q))
        if tokens & {"stock", "stocks", "market", "markets", "invest", "investing", "investor", "trading", "trade", "trader", "predict", "prediction", "predicts", "predictor", "portfolio", "equities", "equity", "shares", "ticker", "forecast", "forecasting", "backtest", "algo", "algorithmic"}:
            return "trading"
        elif tokens & {"sleep", "health", "diet", "fitness", "workout", "caffeine", "recovery", "wellness", "chronobiology", "circadian"}:
            return "health"
        elif tokens & {"freelance", "accounting", "tax", "invoice", "finance", "bank", "crypto", "pay", "fintech", "money", "deduction", "deductions", "cfo", "cpa"}:
            return "fintech"
        elif tokens & {"schema", "database", "migration", "postgres", "sql", "code", "dev", "api", "devtools", "docker", "deploy", "linter", "contention", "firewall"}:
            return "devtools"
        elif tokens & {"split", "roommate", "chore", "debt", "task", "habit", "todo", "productivity", "escrow", "house", "household", "bills", "rent"}:
            return "productivity"
        elif tokens & {"dating", "tinder", "match", "meetup", "hobby", "friend", "community", "social", "event", "club", "group", "ghosting", "attendance", "bonds", "pet", "dog", "cat", "puppy", "animal", "game", "gaming", "pokemon", "ar", "vr"}:
            return "social"
        # Neutral default for anything unmatched: generic productivity/SaaS fixtures,
        # NOT dating apps. An unmatched idea (e.g. a niche B2B tool) has nothing to do
        # with social/dating competitors, so defaulting there was actively misleading.
        return "productivity"

    def get_fixture_data(self, idea_or_query: str, seed: Optional[int] = None) -> Dict[str, Any]:
        """Load fixture file based on query topic with dynamic randomized sampling."""
        category = self._match_category(idea_or_query)
        fixture_file = self.fixtures_dir / f"{category}.json"
        rng = __import__("random").Random(seed) if seed is not None else __import__("random").Random()

        if fixture_file.exists():
            with open(fixture_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            raw_keywords = data.get("keywords", [idea_or_query])
            keyword_variations = data.get("keyword_variations", [])
            if keyword_variations:
                selected_var = rng.choice(keyword_variations)
                combined_kw = list(dict.fromkeys(raw_keywords[:3] + selected_var))
            else:
                combined_kw = raw_keywords

            base_comps = data.get("competitors", [])
            variants = data.get("competitor_variants", [])
            selected_comps = list(base_comps)
            if variants:
                num_to_add = rng.randint(1, min(2, len(variants)))
                added_variants = rng.sample(variants, num_to_add)
                selected_comps.extend(added_variants)

            base_complaints = data.get("raw_complaint_pool", [])
            extended = data.get("complaint_pool_extended", [])
            all_complaints = list(dict.fromkeys(base_complaints + extended))
            sample_size = min(len(all_complaints), rng.randint(8, 12)) if len(all_complaints) >= 8 else len(all_complaints)
            sampled_complaints = rng.sample(all_complaints, sample_size) if len(all_complaints) >= sample_size else all_complaints

            size_range = data.get("market_size_range")
            if size_range:
                min_b = size_range.get("min_billions", 3.0)
                max_b = size_range.get("max_billions", 10.0)
                template = size_range.get("label_template", "${value}B market")
                val = round(rng.uniform(min_b, max_b), 1)
                market_size_str = template.replace("${value}", str(val))
            else:
                market_size_str = data.get("market_size", "$4.0B market")

            trend_signals = data.get("trend_signals", [])
            sampled_signals = rng.sample(trend_signals, min(len(trend_signals), 2)) if trend_signals else []

            return {
                "category": category,
                "keywords": combined_kw,
                "market_size": market_size_str,
                "competitors": selected_comps,
                "raw_complaint_pool": sampled_complaints,
                "trend_signals": sampled_signals,
            }

        # Generic fallback for a category with no fixture file on disk at all.
        return {
            "category": category,
            "keywords": [f"{idea_or_query} platform", "competitor analysis", "market research"],
            "market_size": "$5.8B global market (unverified estimate, no fixture data for this category)",
            "competitors": [],
            "raw_complaint_pool": [],
            "trend_signals": [],
        }

    async def search_query(self, query: str) -> Dict[str, Any]:
        """Best-effort live web search. No API key, no auth, Google HTML results page."""
        try:
            params = {
                "q": query,
                "num": "10",
                "hl": "en",
                "gl": "us",
            }
            # "CONSENT=YES+" skips the EU cookie-consent interstitial page that
            # would otherwise replace the actual results HTML.
            cookies = {"CONSENT": "YES+"}
            async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
                res = await client.get(
                    "https://www.google.com/search",
                    params=params,
                    headers=self.headers,
                    cookies=cookies,
                )
                if res.status_code == 200:
                    # Google's markup/class names shift often and aren't part of any
                    # stable public API, so parsing here is deliberately loose:
                    # <h3 ...>Title</h3> blocks are the organic-result headings, and
                    # the snippet text sits in the nearby data-sncf/VwiC3b-style spans.
                    titles = re.findall(r'<h3[^>]*>(.*?)</h3>', res.text, re.DOTALL)
                    snippets = re.findall(
                        r'<div class="VwiC3b[^"]*"[^>]*>(.*?)</div>', res.text, re.DOTALL
                    )

                    def _strip_tags(html_fragment: str) -> str:
                        return re.sub(r'<[^>]+>', '', html_fragment).strip()

                    clean_titles = [_strip_tags(t) for t in titles if _strip_tags(t)]
                    clean_snippets = [_strip_tags(s) for s in snippets if _strip_tags(s)]

                    if clean_titles or clean_snippets:
                        pairs = list(zip(clean_titles[:5], clean_snippets[:5])) if clean_snippets else \
                            [(t, "") for t in clean_titles[:5]]
                        return {
                            "query": query,
                            "status": "success",
                            "source": "live_google",
                            "organic": [
                                {"title": t, "snippet": s}
                                for t, s in pairs
                            ]
                        }
                elif res.status_code in (429, 503):
                    logger.info(f"Google search rate-limited/blocked ({res.status_code}) for '{query}'.")
        except Exception as e:
            logger.info(f"Live search failed for '{query}' ({e}), falling back to no-result.")

        return {"query": query, "status": "no_results", "source": "none", "organic": []}

    async def scrape_page(self, target_url: str) -> Dict[str, Any]:
        """Best-effort single-page fetch for title/meta content. No API key, no auth."""
        try:
            if not target_url.startswith("http"):
                target_url = f"https://{target_url}"
            async with httpx.AsyncClient(timeout=3.0, follow_redirects=True) as client:
                res = await client.get(target_url, headers=self.headers)
                if res.status_code == 200:
                    title_match = re.search(r'<title>([^<]+)</title>', res.text, re.IGNORECASE)
                    title = title_match.group(1).strip() if title_match else target_url
                    desc_match = re.search(
                        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
                        res.text, re.IGNORECASE
                    )
                    description = desc_match.group(1).strip() if desc_match else None
                    return {
                        "url": target_url,
                        "status": "success",
                        "source": "live_fetch",
                        "title": title,
                        "meta_description": description,
                    }
        except Exception as e:
            logger.info(f"Live page fetch failed for '{target_url}' ({e}).")

        return {"url": target_url, "status": "unreachable", "source": "none", "title": None, "meta_description": None}


web_search_client = WebSearchClient()
