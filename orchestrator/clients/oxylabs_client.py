import asyncio
import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx
from orchestrator.config import settings

logger = logging.getLogger("founder0.oxylabs")

class OxylabsClient:
    """
    Client for Oxylabs Realtime Search & Web Scraper APIs.
    Gracefully falls back to industry-specific fixtures when in MOCK_MODE
    or when credentials are unconfigured. Supports flexible, randomized
    sampling across extended complaint pools and competitor variants.
    """

    def __init__(self):
        self.username = settings.OXYLABS_USERNAME
        self.password = settings.OXYLABS_PASSWORD
        self.mock_mode = settings.MOCK_MODE or not (self.username and self.password)
        self.fixtures_dir = Path(__file__).resolve().parent.parent.parent / "fixtures" / "market_recon"

    def _match_category(self, query: str) -> str:
        """Infer industry category from user prompt to choose realistic fixture."""
        q = query.lower().strip()
        if q in ["productivity", "fintech", "social", "health", "devtools"]:
            return q
        if any(w in q for w in ["split", "roommate", "chore", "debt", "task", "habit", "todo", "productivity"]):
            return "productivity"
        elif any(w in q for w in ["freelance", "accounting", "tax", "invoice", "finance", "bank", "crypto", "pay", "fintech"]):
            return "fintech"
        elif any(w in q for w in ["meetup", "hobby", "friend", "community", "social", "event", "club", "group"]):
            return "social"
        elif any(w in q for w in ["sleep", "health", "diet", "fitness", "workout", "caffeine", "recovery"]):
            return "health"
        elif any(w in q for w in ["schema", "database", "migration", "postgres", "sql", "code", "dev", "api", "devtools"]):
            return "devtools"
        return "productivity"

    def get_fixture_data(self, idea_or_query: str, seed: Optional[int] = None) -> Dict[str, Any]:
        """Load fixture file based on query topic with dynamic randomized sampling."""
        category = self._match_category(idea_or_query)
        fixture_file = self.fixtures_dir / f"{category}.json"
        rng = random.Random(seed) if seed is not None else random.Random()

        if fixture_file.exists():
            with open(fixture_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 1. Keywords & Variations
            raw_keywords = data.get("keywords", [idea_or_query])
            keyword_variations = data.get("keyword_variations", [])
            if keyword_variations:
                selected_var = rng.choice(keyword_variations)
                combined_kw = list(dict.fromkeys(raw_keywords[:3] + selected_var))
            else:
                combined_kw = raw_keywords

            # 2. Competitors + Variants
            base_comps = data.get("competitors", [])
            variants = data.get("competitor_variants", [])
            selected_comps = list(base_comps)
            if variants:
                num_to_add = rng.randint(1, min(2, len(variants)))
                added_variants = rng.sample(variants, num_to_add)
                selected_comps.extend(added_variants)

            # 3. Complaints (Core + Extended)
            base_complaints = data.get("raw_complaint_pool", [])
            extended = data.get("complaint_pool_extended", [])
            all_complaints = list(dict.fromkeys(base_complaints + extended))
            sample_size = min(len(all_complaints), rng.randint(8, 12)) if len(all_complaints) >= 8 else len(all_complaints)
            sampled_complaints = rng.sample(all_complaints, sample_size) if len(all_complaints) >= sample_size else all_complaints

            # 4. Market Size Range
            size_range = data.get("market_size_range")
            if size_range:
                min_b = size_range.get("min_billions", 3.0)
                max_b = size_range.get("max_billions", 10.0)
                template = size_range.get("label_template", "${value}B market")
                val = round(rng.uniform(min_b, max_b), 1)
                market_size_str = template.replace("${value}", str(val))
            else:
                market_size_str = data.get("market_size", "$4.0B market")

            # 5. Trend Signals
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

        # Default fallback
        return {
            "category": "productivity",
            "keywords": ["smart expense splitting", "collaborative ledger"],
            "market_size": "$4.2B shared household economy",
            "competitors": [
                {
                    "name": "SplitPro",
                    "url": "https://splitpro.io",
                    "description": "Collaborative bill splitting application for groups.",
                    "complaints": ["Lacks automated settlement and dispute resolution."],
                    "source_queries": ["bill splitting app"]
                },
                {
                    "name": "Tricount",
                    "url": "https://tricount.com",
                    "description": "Share group expenses easily on trips, events, or shared flats.",
                    "complaints": ["Relies on honor system."],
                    "source_queries": ["group expenses"]
                },
                {
                    "name": "Settle Up",
                    "url": "https://settleup.io",
                    "description": "Track group expenses for roommates and trips.",
                    "complaints": ["Outdated UI."],
                    "source_queries": ["roommate expense app"]
                },
                {
                    "name": "Venmo Groups",
                    "url": "https://venmo.com",
                    "description": "Social payments app with group split payment features.",
                    "complaints": ["Splitting is manual."],
                    "source_queries": ["split payments"]
                }
            ],
            "raw_complaint_pool": [
                "Paying shared expenses is painful and awkward.",
                "Roommates forget to pay on time constantly.",
                "Manual expense tracking takes hours each month.",
                "No accountability when splitting grocery bills.",
                "Passive aggressive reminders ruin roommate relationships.",
                "Splitwise added paywall timers that make it unusable.",
                "Venmo requests get ignored for weeks.",
                "Need an automated escrow for household bills."
            ],
            "trend_signals": []
        }

    async def search_query(self, query: str) -> Dict[str, Any]:
        """Execute a single Realtime SERP query."""
        if self.mock_mode:
            await asyncio.sleep(0.15)  # Simulate network latency
            return {"query": query, "status": "mocked", "organic": []}

        url = "https://realtime.oxylabs.io/v1/queries"
        payload = {
            "source": "google_search",
            "query": query,
            "geo_location": "United States",
            "parse": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    url,
                    auth=(self.username or "", self.password or ""),
                    json=payload
                )
                if res.status_code == 200:
                    return res.json()
                logger.warning(f"Oxylabs query failed with code {res.status_code}: {res.text}")
                return {"query": query, "error": res.text}
        except Exception as e:
            logger.error(f"Oxylabs request exception for query '{query}': {e}")
            return {"query": query, "error": str(e)}

    async def scrape_page(self, target_url: str) -> Dict[str, Any]:
        """Scrape deep competitor webpage content (pricing, feature list)."""
        if self.mock_mode:
            await asyncio.sleep(0.1)
            return {
                "url": target_url,
                "title": f"Official Portal | {target_url}",
                "content": "Leading platform with premium tiers starting at $9.99/mo, offering real-time tracking, export tools, and team collaboration."
            }

        url = "https://realtime.oxylabs.io/v1/queries"
        payload = {
            "source": "universal",
            "url": target_url,
            "parse": True
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(
                    url,
                    auth=(self.username or "", self.password or ""),
                    json=payload
                )
                if res.status_code == 200:
                    return res.json()
                return {"url": target_url, "error": res.text}
        except Exception as e:
            return {"url": target_url, "error": str(e)}

oxylabs_client = OxylabsClient()
