import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx
from orchestrator.config import settings

logger = logging.getLogger("founder0.oxylabs")

class OxylabsClient:
    """
    Client for Oxylabs Realtime Search & Web Scraper APIs.
    Gracefully falls back to industry-specific fixtures when in MOCK_MODE
    or when credentials are unconfigured.
    """

    def __init__(self):
        self.username = settings.OXYLABS_USERNAME
        self.password = settings.OXYLABS_PASSWORD
        self.mock_mode = settings.MOCK_MODE or not (self.username and self.password)
        self.fixtures_dir = Path(__file__).resolve().parent.parent.parent / "fixtures" / "market_recon"

    def _match_category(self, query: str) -> str:
        """Infer industry category from user prompt to choose realistic fixture."""
        q = query.lower()
        if any(w in q for w in ["split", "roommate", "chore", "debt", "task", "habit", "todo", "productivity"]):
            return "productivity"
        elif any(w in q for w in ["freelance", "accounting", "tax", "invoice", "finance", "bank", "crypto", "pay"]):
            return "fintech"
        elif any(w in q for w in ["meetup", "hobby", "friend", "community", "social", "event", "club", "group"]):
            return "social"
        elif any(w in q for w in ["sleep", "health", "diet", "fitness", "workout", "caffeine", "recovery"]):
            return "health"
        elif any(w in q for w in ["schema", "database", "migration", "postgres", "sql", "code", "dev", "api"]):
            return "devtools"
        return "productivity"

    def get_fixture_data(self, idea_or_query: str) -> Dict[str, Any]:
        """Load fixture file based on query topic."""
        category = self._match_category(idea_or_query)
        fixture_file = self.fixtures_dir / f"{category}.json"
        if fixture_file.exists():
            with open(fixture_file, "r", encoding="utf-8") as f:
                return json.load(f)
        # Default fallback
        return {
            "category": "productivity",
            "keywords": ["smart expense splitting", "collaborative ledger"],
            "competitors": [
                {
                    "name": "SplitPro",
                    "url": "https://splitpro.io",
                    "description": "Collaborative bill splitting application for groups.",
                    "complaints": ["Lacks automated settlement and dispute resolution."],
                    "source_queries": ["bill splitting app"]
                }
            ],
            "raw_complaint_pool": ["Paying shared expenses is painful and awkward."]
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
