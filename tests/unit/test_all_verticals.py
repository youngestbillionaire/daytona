import pytest
from pathlib import Path
from orchestrator.stages import (
    run_market_recon,
    run_competitor_enrichment,
    run_opportunity_graph,
    run_whitespace_analysis,
    run_ideation,
    run_deck_generation,
)
from orchestrator.models import MvpDeployOutput, ScreenshotOutput

VERTICAL_IDEAS = [
    ("productivity", "an autonomous roommate expense escrow and chore settlement app"),
    ("fintech", "an AI accountant that automatically discovers Schedule C deductions from bank feeds"),
    ("social", "a stake-backed meetup app with refundable attendance bonds that eliminates ghosting"),
    ("health", "a prescriptive chronobiology and caffeine cutoff protocol app without hardware lock-in"),
    ("devtools", "a pre-deployment Postgres migration linter and lock contention simulation firewall"),
]

@pytest.mark.asyncio
@pytest.mark.parametrize("expected_category,idea", VERTICAL_IDEAS)
async def test_vertical_pipeline_execution(expected_category: str, idea: str):
    # 1. Market Recon
    recon = await run_market_recon(idea)
    assert recon.category == expected_category
    assert len(recon.competitors) >= 4
    assert len(recon.raw_complaint_pool) >= 8

    # 2. Competitor Enrichment
    enrichment = await run_competitor_enrichment(recon)
    assert len(enrichment.enriched_competitors) >= 4

    # 3. Opportunity Graph
    graph = await run_opportunity_graph(idea, recon, enrichment)
    assert graph.node_count > 0
    assert graph.edge_count > 0

    # 4. Whitespace Analysis
    whitespace = await run_whitespace_analysis(graph, recon)
    assert len(whitespace.primary_gap) > 20
    assert len(whitespace.supporting_complaints) > 0

    # 5. Ideation
    ideation = await run_ideation(idea, whitespace)
    assert len(ideation.product_name) > 0
    assert len(ideation.tagline) > 0
    assert len(ideation.contrarian_insight) > 10
    assert len(ideation.technical_moat) > 10
    assert len(ideation.tam_estimate) > 0
    assert len(ideation.ten_x_factor) > 10
    assert len(ideation.core_features) == 3

    # 6. Deck Generation
    deploy_dummy = MvpDeployOutput(preview_url="http://localhost:8000/api/preview/sbx_test")
    screenshot_dummy = ScreenshotOutput(screenshot_path="", screenshot_url="/api/artifacts/screenshots/test.png")
    
    deck = await run_deck_generation(
        run_id=f"test_vert_{expected_category}",
        ideation=ideation,
        recon=recon,
        whitespace=whitespace,
        graph=graph,
        deploy=deploy_dummy,
        screenshot=screenshot_dummy
    )
    assert deck.slides_count == 8
    assert deck.deck_url.startswith("/api/artifacts/decks")
    assert Path(deck.deck_html_path).exists()
    
    html_content = Path(deck.deck_html_path).read_text(encoding="utf-8")
    assert ideation.product_name in html_content
    assert ideation.contrarian_insight in html_content
