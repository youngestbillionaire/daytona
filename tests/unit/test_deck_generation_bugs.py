import pytest
from pathlib import Path
from orchestrator.stages.deck_generation import run_deck_generation
from orchestrator.models import (
    CoreFeature,
    IdeationOutput,
    MarketReconOutput,
    MvpDeployOutput,
    OpportunityGraphOutput,
    ScreenshotOutput,
    TargetUserPersona,
    WhitespaceAnalysisOutput,
)

@pytest.mark.asyncio
async def test_deck_generation_empty_complaints_and_palette():
    run_id = "test_deck_edge_1"
    ideation = IdeationOutput(
        product_name="MinimalDeck",
        tagline="A minimalist brand tagline with precision",
        one_line_pitch="Minimal one-liner",
        elevator_pitch="Full 4-sentence elevator pitch demonstrating robustness against empty lists.",
        core_features=[
            CoreFeature(name="Feat 1", description="Desc 1", user_value="Value 1")
        ],
        target_user_persona=TargetUserPersona(name="Minimalist", description="Minimal persona", pain_points=[]),
        monetization_model="Subscription",
        pricing_suggestion="Free / $10",
        differentiation_from_competitors="10x faster",
        suggested_color_palette=[]  # Empty list test
    )
    recon = MarketReconOutput(
        category="productivity",
        extracted_keywords=["test"],
        competitors=[],  # Empty competitors test
        raw_complaint_pool=[]  # Empty complaints test
    )
    whitespace = WhitespaceAnalysisOutput(
        primary_gap="No competitor covers this market segment.",
        supporting_complaints=[],
        underserved_features=[]
    )
    graph = OpportunityGraphOutput(nodes=[], edges=[], node_count=0, edge_count=0)
    deploy = MvpDeployOutput(preview_url="http://localhost:8000/api/preview/sbx_test")
    screenshot = ScreenshotOutput(screenshot_path="", screenshot_url="/api/artifacts/screenshots/test.png")

    deck_out = await run_deck_generation(run_id, ideation, recon, whitespace, graph, deploy, screenshot)
    assert deck_out.slides_count == 8
    assert Path(deck_out.deck_html_path).exists()
    
    html = Path(deck_out.deck_html_path).read_text(encoding="utf-8")
    assert "MinimalDeck" in html
    assert "INSTITUTIONAL SEED DECK" in html
    assert "Competitive Matrix" in html

@pytest.mark.asyncio
async def test_deck_generation_html_special_chars():
    run_id = "test_deck_edge_2"
    ideation = IdeationOutput(
        product_name="XSS<Safe>&'\"Company",
        tagline="Protecting systems & data from <attacks>",
        one_line_pitch="Secure & reliable zero-downtime platform",
        elevator_pitch="Safe pitch with & and <tag> characters.",
        core_features=[
            CoreFeature(name="A & B Protocol", description="Handles <x> & <y>", user_value="Zero risk")
        ],
        target_user_persona=TargetUserPersona(name="Security Lead", description="Guards systems", pain_points=[]),
        monetization_model="Usage & Tiers",
        pricing_suggestion="$99 / mo",
        differentiation_from_competitors="Complete isolation",
        suggested_color_palette=["#0284c7", "#0f172a", "#38bdf8"]
    )
    recon = MarketReconOutput(category="devtools", competitors=[], raw_complaint_pool=["Test complaint <1> & <2>"])
    whitespace = WhitespaceAnalysisOutput(primary_gap="Security gap in <legacy> tools.", supporting_complaints=[])
    graph = OpportunityGraphOutput(nodes=[], edges=[], node_count=5, edge_count=4)
    deploy = MvpDeployOutput(preview_url="http://localhost:8000/api/preview/sbx_test")
    screenshot = ScreenshotOutput(screenshot_path="", screenshot_url="/api/artifacts/screenshots/test.png")

    deck_out = await run_deck_generation(run_id, ideation, recon, whitespace, graph, deploy, screenshot)
    assert Path(deck_out.deck_html_path).exists()
