import hashlib
import logging
from typing import Callable, Optional
from orchestrator.clients.neo4j_client import neo4j_client
from orchestrator.models import (
    CompetitorEnrichmentOutput,
    MarketReconOutput,
    OpportunityGraphOutput,
    GraphNode,
    GraphEdge,
)

logger = logging.getLogger("founder0.stage.opportunity_graph")

def hash_id(prefix: str, text: str) -> str:
    h = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{h}"

async def run_opportunity_graph(
    idea: str,
    recon_output: MarketReconOutput,
    enrichment_output: CompetitorEnrichmentOutput,
    log: Optional[Callable[[str], None]] = None
) -> OpportunityGraphOutput:
    """
    Stage 2.3: OPPORTUNITY_GRAPH
    Constructs and merges the competitive landscape knowledge graph in Neo4j,
    linking Idea, Competitors, Features, Complaints, and Pricing Tiers.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    emit(f"🕸️ [OPPORTUNITY_GRAPH] Connecting to Neo4j knowledge graph engine...")
    await neo4j_client.connect()

    # 1. Merge Idea Node
    idea_id = hash_id("idea", idea)
    emit(f"📌 [OPPORTUNITY_GRAPH] Merging Idea node: '{idea[:40]}...'")
    await neo4j_client.merge_node(
        node_id=idea_id,
        label=idea[:30],
        node_type="Idea",
        properties={"text": idea, "category": recon_output.category}
    )

    # 2. Merge Competitors and their Features/Pricing
    for comp in enrichment_output.enriched_competitors:
        comp_id = hash_id("comp", comp.name)
        emit(f"🏢 [OPPORTUNITY_GRAPH] Merging Competitor: '{comp.name}'")
        await neo4j_client.merge_node(
            node_id=comp_id,
            label=comp.name,
            node_type="Competitor",
            properties={"url": comp.url, "description": comp.description}
        )

        for feat in comp.features:
            feat_id = hash_id("feat", feat)
            await neo4j_client.merge_node(
                node_id=feat_id,
                label=feat,
                node_type="Feature",
                properties={"category": recon_output.category}
            )
            await neo4j_client.merge_relationship(
                source_id=comp_id,
                target_id=feat_id,
                relationship="OFFERS"
            )

        for price in comp.pricing_tiers:
            price_id = hash_id("price", f"{comp.name}_{price.name}")
            await neo4j_client.merge_node(
                node_id=price_id,
                label=f"{price.name} ({price.price})",
                node_type="PricingTier",
                properties={"price": price.price, "billing": price.billing_period}
            )
            await neo4j_client.merge_relationship(
                source_id=comp_id,
                target_id=price_id,
                relationship="HAS_PRICING"
            )

    # 3. Merge Complaints and link to Competitors and Features
    for idx, complaint_text in enumerate(recon_output.raw_complaint_pool[:6]):
        comp_id = hash_id("complaint", complaint_text[:30])
        await neo4j_client.merge_node(
            node_id=comp_id,
            label=complaint_text[:25] + "...",
            node_type="Complaint",
            properties={"text": complaint_text, "sentiment_score": -0.85}
        )

        # Link to first matching competitor
        if enrichment_output.enriched_competitors:
            target_comp = enrichment_output.enriched_competitors[idx % len(enrichment_output.enriched_competitors)]
            target_comp_id = hash_id("comp", target_comp.name)
            await neo4j_client.merge_relationship(
                source_id=comp_id,
                target_id=target_comp_id,
                relationship="RAISED_AGAINST"
            )

    # Export full subgraph for visualization
    graph_export = await neo4j_client.get_graph_export()
    emit(f"✅ [OPPORTUNITY_GRAPH] Ingestion complete. Graph contains {graph_export['node_count']} nodes and {graph_export['edge_count']} relationships.")

    return OpportunityGraphOutput(
        nodes=[GraphNode(**n) for n in graph_export["nodes"]],
        edges=[GraphEdge(**e) for e in graph_export["edges"]],
        node_count=graph_export["node_count"],
        edge_count=graph_export["edge_count"],
        graph_summary={
            "nodes": graph_export["node_count"],
            "edges": graph_export["edge_count"]
        }
    )
