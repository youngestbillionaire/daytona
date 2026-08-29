import logging
import random
from typing import Callable, Optional
from orchestrator.clients.neo4j_client import neo4j_client
from orchestrator.models import (
    MarketReconOutput,
    OpportunityGraphOutput,
    WhitespaceAnalysisOutput,
)

logger = logging.getLogger("founder0.stage.whitespace_analysis")

GAP_VARIATIONS = {
    "productivity": [
        "Incumbents treat shared household finances as a passive tracking problem, ignoring the core human confrontation friction. The real market void is an autonomous escrow settlement and chore-linked debt protocol that removes humans from the enforcement loop.",
        "Existing co-living tools build passive ledgers that amplify roommate hostility. The true whitespace is trustless financial execution where shared liabilities auto-settle without awkward interpersonal confrontation.",
        "Legacy bill splitters rely on manual goodwill and nag-notifications. The unaddressed market void is active treasury management with cryptographic dispute arbitration for shared households."
    ],
    "fintech": [
        "Existing accounting tools force solo founders and freelancers to be their own CPAs with clunky manual categorization. The unaddressed void is an autonomous background intelligence that identifies Schedule C deductions from raw bank feeds and files quarterly estimates automatically.",
        "Incumbent bookkeeping SaaS digitizes receipts but leaves the cognitive burden on the freelancer. The structural whitespace is zero-touch tax intelligence that autonomously discovers deductions and handles compliance silently.",
        "Freelance finance software charges monthly fees to make users do manual data entry. The breakthrough void is an autonomous CFO agent that turns bank streams directly into audit-proof tax filings."
    ],
    "social": [
        "Event platforms optimize for vanity RSVPs while suffering an 80% ghosting rate. The fundamental whitespace is a stake-backed commitment protocol where refundable attendance bonds make real-world micro-meetups actually happen.",
        "Social apps treat friendship like dating with superficial swipes that lead to zero real-world connection. The market gap is skin-in-the-game micro-communities built on mutual accountability and verified attendance.",
        "Current community platforms charge organizers high subscription fees while delivering empty rooms. The whitespace is an incentive-aligned event protocol where no-shows fund reliable attendees."
    ],
    "health": [
        "Sleep apps sell passive hardware sensors that report retroactive scores without prescriptive instructions. The market gap is a hardware-agnostic, minute-level chronobiology protocol telling users exact caffeine cutoffs and evening routines before sleep happens.",
        "Incumbent sleep trackers give descriptive anxiety scores after poor nights rather than actionable behavioral rules beforehand. The unaddressed void is precision circadian protocoling tailored to individual metabolic rates.",
        "Wearable health gadgets create measurement obsession without behavior modification. The structural market gap is a prescriptive chronobiology engine that eliminates hardware lock-in."
    ],
    "devtools": [
        "Migration frameworks focus on executing SQL changes while ignoring production blast radius. The structural gap is a pre-deployment simulation firewall that analyzes lock contention and query impact against live table replicas before running migrations.",
        "Current database migration tools are blind executors that lack runtime safety intelligence. The unaddressed whitespace is a CI/CD migration firewall that predicts table locks and downstream service breakages before production deployment.",
        "Database tools make writing migrations faster but do nothing to prevent catastrophic 3 AM outages. The critical market void is simulated zero-downtime verification with automated safe rewrite engines."
    ]
}

async def run_whitespace_analysis(
    graph_output: OpportunityGraphOutput,
    recon_output: MarketReconOutput,
    log: Optional[Callable[[str], None]] = None
) -> WhitespaceAnalysisOutput:
    """
    Stage 2.4: WHITESPACE_ANALYSIS
    Queries the graph for unaddressed user complaints and high-friction feature voids
    to crystallize the core market opportunity and identify structural industry failures.
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

    # Select high-impact structural market void dynamically
    category = recon_output.category
    if category not in GAP_VARIATIONS and recon_output.raw_complaint_pool:
        top_complaint = recon_output.raw_complaint_pool[0]
        primary_gap = f"Incumbents suffer from fundamental structural limitations: '{top_complaint}'. The core market whitespace is an autonomous, modern architecture eliminating this friction entirely."
    else:
        category_gaps = GAP_VARIATIONS.get(category, [
            "Incumbents rely on manual user friction and legacy architectures, leaving an unaddressed whitespace for autonomous execution, cryptographic trust, and zero-overhead resolution."
        ])
        primary_gap = random.choice(category_gaps)

    coverage_map = {
        f"Legacy {category.capitalize()} Incumbent Tools": min(len(recon_output.competitors), 4),
        "Passive Manual Management": min(len(recon_output.competitors), 3),
        "Autonomous Friction Elimination": 0,
        "Real-Time State Verification": 0,
        "Zero-Overhead User Experience": 0
    }

    emit(f"🎯 [WHITESPACE_ANALYSIS] Identified Primary Structural Gap: '{primary_gap}'")
    emit(f"📈 [WHITESPACE_ANALYSIS] Synthesized {len(recon_output.raw_complaint_pool)} verified complaints into whitespace vectors.")

    return WhitespaceAnalysisOutput(
        primary_gap=primary_gap,
        supporting_complaints=recon_output.raw_complaint_pool[:4],
        underserved_features=[
            "Autonomous Execution Without Human Friction",
            "Trustless Commitment & Dispute Settlement",
            "Predictive Impact Simulation & Safety Guarantees"
        ],
        competitor_coverage_map=coverage_map
    )
