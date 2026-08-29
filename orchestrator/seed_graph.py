import asyncio
import logging
from orchestrator.clients.neo4j_client import neo4j_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("founder0.seed_graph")

CATEGORIES_SEED = [
    {
        "category": "productivity",
        "competitors": [
            {"name": "Splitwise", "url": "https://splitwise.com", "features": ["Expense Splitting", "Debt Simplification", "Group Balances"]},
            {"name": "Tricount", "url": "https://tricount.com", "features": ["Group Expenses", "Offline Mode"]}
        ],
        "complaints": [
            "Excessive ads and wait times on free tier",
            "Awkward reminders with uncooperative roommates"
        ]
    },
    {
        "category": "fintech",
        "competitors": [
            {"name": "FreshBooks", "url": "https://freshbooks.com", "features": ["Invoicing", "Time Tracking", "Expense Management"]},
            {"name": "Wave", "url": "https://waveapps.com", "features": ["Free Invoicing", "Bank Sync"]}
        ],
        "complaints": [
            "Per-client pricing limits freelance growth",
            "Manual categorization takes hours every week"
        ]
    },
    {
        "category": "social",
        "competitors": [
            {"name": "Meetup", "url": "https://meetup.com", "features": ["Event Scheduling", "Local Discovery", "RSVP Management"]}
        ],
        "complaints": [
            "Expensive organizer subscriptions",
            "High RSVP flake and ghost rate"
        ]
    },
    {
        "category": "health",
        "competitors": [
            {"name": "Whoop", "url": "https://whoop.com", "features": ["Strain Tracking", "Sleep Coaching", "Recovery Score"]}
        ],
        "complaints": [
            "Costly hardware and perpetual subscription",
            "Lacks specific habit action timing"
        ]
    },
    {
        "category": "devtools",
        "competitors": [
            {"name": "Prisma Migrate", "url": "https://prisma.io", "features": ["Declarative Migrations", "Schema Diffing"]}
        ],
        "complaints": [
            "Locks production tables unexpectedly on alter statements",
            "Complex CI/CD shadow database setup"
        ]
    }
]

async def seed_baseline_graph():
    """Seeds baseline nodes and relationships across 5 categories."""
    logger.info("🌱 Seeding Neo4j Opportunity Knowledge Graph with baseline category data...")
    await neo4j_client.connect()

    for item in CATEGORIES_SEED:
        cat = item["category"]
        for comp in item["competitors"]:
            comp_id = f"seed_comp_{comp['name'].lower()}"
            await neo4j_client.merge_node(
                node_id=comp_id,
                label=comp["name"],
                node_type="Competitor",
                properties={"url": comp["url"], "category": cat, "is_seed": True}
            )
            for feat in comp["features"]:
                feat_id = f"seed_feat_{feat.lower().replace(' ', '_')}"
                await neo4j_client.merge_node(
                    node_id=feat_id,
                    label=feat,
                    node_type="Feature",
                    properties={"category": cat, "is_seed": True}
                )
                await neo4j_client.merge_relationship(
                    source_id=comp_id,
                    target_id=feat_id,
                    relationship="OFFERS"
                )

        for comp_text in item["complaints"]:
            complaint_id = f"seed_complaint_{comp_text[:15].lower().replace(' ', '_')}"
            await neo4j_client.merge_node(
                node_id=complaint_id,
                label=comp_text[:25] + "...",
                node_type="Complaint",
                properties={"text": comp_text, "category": cat, "is_seed": True}
            )

    export = await neo4j_client.get_graph_export()
    logger.info(f"✅ Baseline graph seeded successfully! Total Nodes: {export['node_count']}, Total Relationships: {export['edge_count']}")

if __name__ == "__main__":
    asyncio.run(seed_baseline_graph())
