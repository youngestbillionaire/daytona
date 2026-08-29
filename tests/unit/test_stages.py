import pytest
from orchestrator.models import PipelineStage
from orchestrator.stages import (
    run_market_recon,
    run_competitor_enrichment,
    run_opportunity_graph,
    run_whitespace_analysis,
    run_ideation,
    run_naming_branding,
    run_spec_generation,
    run_mvp_scaffold,
    run_mvp_codegen,
    run_mvp_build_test,
    run_mvp_self_heal,
    run_mvp_deploy,
    run_screenshot_capture,
    run_deck_generation,
    run_narration_generation,
)

@pytest.mark.asyncio
async def test_stage_market_recon():
    idea = "an app for splitting bills with roommates who hate each other"
    recon = await run_market_recon(idea)
    assert len(recon.competitors) > 0
    assert len(recon.raw_complaint_pool) > 0
    assert recon.category in ["productivity", "fintech", "social", "health", "devtools"]

@pytest.mark.asyncio
async def test_stage_competitor_enrichment():
    idea = "an app for splitting bills with roommates who hate each other"
    recon = await run_market_recon(idea)
    enrichment = await run_competitor_enrichment(recon)
    assert len(enrichment.enriched_competitors) > 0
    assert len(enrichment.enriched_competitors[0].features) > 0

@pytest.mark.asyncio
async def test_stage_opportunity_graph_and_whitespace():
    idea = "an app for splitting bills with roommates who hate each other"
    recon = await run_market_recon(idea)
    enrichment = await run_competitor_enrichment(recon)
    graph = await run_opportunity_graph(idea, recon, enrichment)
    assert graph.node_count > 0
    assert len(graph.nodes) > 0

    whitespace = await run_whitespace_analysis(graph, recon)
    assert len(whitespace.primary_gap) > 10
    assert len(whitespace.supporting_complaints) > 0

@pytest.mark.asyncio
async def test_stage_ideation_and_spec():
    idea = "an app for splitting bills with roommates who hate each other"
    recon = await run_market_recon(idea)
    enrichment = await run_competitor_enrichment(recon)
    graph = await run_opportunity_graph(idea, recon, enrichment)
    whitespace = await run_whitespace_analysis(graph, recon)

    ideation = await run_ideation(idea, whitespace)
    assert ideation.product_name != ""
    assert len(ideation.core_features) == 3
    assert len(ideation.contrarian_insight) > 10
    assert len(ideation.technical_moat) > 10
    assert len(ideation.tam_estimate) > 0
    assert len(ideation.ten_x_factor) > 10

    branding = await run_naming_branding(ideation)
    assert branding.product_name == ideation.product_name

    spec = await run_spec_generation(ideation)
    assert len(spec.feature_implementations) > 0
    assert len(spec.data_models) > 0

@pytest.mark.asyncio
async def test_stage_mvp_pipeline():
    idea = "an app for splitting bills with roommates who hate each other"
    recon = await run_market_recon(idea)
    enrichment = await run_competitor_enrichment(recon)
    graph = await run_opportunity_graph(idea, recon, enrichment)
    whitespace = await run_whitespace_analysis(graph, recon)
    ideation = await run_ideation(idea, whitespace)
    spec = await run_spec_generation(ideation)

    scaffold = await run_mvp_scaffold(spec)
    assert scaffold.sandbox_id.startswith("sbx_")

    codegen = await run_mvp_codegen(scaffold, ideation, spec)
    assert len(codegen.generated_files) > 0
    assert codegen.static_check_passed is True

    build_test = await run_mvp_build_test(scaffold)
    assert build_test.build_exit_code == 0
    assert build_test.test_passed is True

    self_heal = await run_mvp_self_heal(scaffold, codegen, build_test)
    assert self_heal.final_build_success is True

    deploy = await run_mvp_deploy(scaffold, self_heal)
    assert deploy.health_check_passed is True
    assert deploy.preview_url.startswith("http")

    screenshot = await run_screenshot_capture("test_run_123", deploy, ideation)
    assert screenshot.screenshot_path != ""

    deck = await run_deck_generation("test_run_123", ideation, recon, whitespace, graph, deploy, screenshot)
    assert deck.slides_count == 8
    assert deck.deck_url.startswith("/api/artifacts/decks")

    narration = await run_narration_generation("test_run_123", ideation, deck)
    assert len(narration.spoken_script) > 50
