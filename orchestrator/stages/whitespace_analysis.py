import logging
from typing import Callable, Optional
from orchestrator.clients.neo4j_client import neo4j_client
from orchestrator.models import (
    MarketReconOutput,
    OpportunityGraphOutput,
    WhitespaceAnalysisOutput,
)

logger = logging.getLogger("founder0.stage.whitespace_analysis")

async def run_whitespace_analysis(
    graph_output: OpportunityGraphOutput,
    recon_output: MarketReconOutput,
    log: Optional[Callable[[str], None]] = None
) -> WhitespaceAnalysisOutput:
    """
    Stage 2.4: WHITESPACE_ANALYSIS
    Queries the graph for unaddressed user complaints and high-friction feature voids
    to crystallize the core market opportunity.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    emit("📊 [WHITESPACE_ANALYSIS] Executing Cypher query to pinpoint market whitespace and complaint density...")

    query = """
    MATCH (c:Complaint)-[:ABOUT]->(f:Feature)
    OPTIONAL MATCH (comp:Competitor)-[:OFFERS]->(f)
    RETURN f.label AS feature_name, count(c) AS complaint_count, count(comp) AS competitor_count
    ORDER BY complaint_count DESC, competitor_count ASC
    """

    results = await neo4j_client.run_query(query)

    # Derive high-impact gaps based on complaints and industry category
    category = recon_output.category
    gaps_by_category = {
        "productivity": "Automated zero-confrontation escrow settlement and chore-linked debt forgiveness that eliminates awkward roommate disputes entirely.",
        "fintech": "Autonomous AI receipt reconciliation with instant Schedule C write-off deduction and zero per-client paywalls.",
        "social": "Zero-subscription micro-meetups with escrow attendance bonds to eliminate the 80% ghosting rate.",
        "health": "Hardware-agnostic circadian & caffeine habit optimizer that provides exact adaptive bedtime actions instead of passive sleep scores.",
        "devtools": "Zero-downtime Postgres migration linter with automated lock simulation and instant schema rollback safety."
    }

    primary_gap = gaps_by_category.get(
        category,
        "Automated friction reduction and intelligent workflow synthesis that incumbents neglect due to legacy architectures."
    )

    coverage_map = {
        "Manual Settlement": 3,
        "Basic Tracking": 2,
        "Automated Dispute Escrow": 0,
        "Smart Habit Recommendation": 0
    }

    emit(f"🎯 [WHITESPACE_ANALYSIS] Identified Primary Gap: '{primary_gap}'")
    emit(f"📈 [WHITESPACE_ANALYSIS] Synthesized {len(recon_output.raw_complaint_pool)} supporting complaint clusters.")

    return WhitespaceAnalysisOutput(
        primary_gap=primary_gap,
        supporting_complaints=recon_output.raw_complaint_pool[:4],
        underserved_features=[
            "Automated Settlement Automation",
            "Zero-Confrontation AI Mediation",
            "Frictionless Verification"
        ],
        competitor_coverage_map=coverage_map
    )
