import pytest
from pathlib import Path
from orchestrator.stages.narration import run_narration_generation
from orchestrator.models import (
    CoreFeature,
    DeckGenerationOutput,
    IdeationOutput,
    TargetUserPersona,
)

@pytest.mark.asyncio
async def test_narration_script_structure_and_duration():
    run_id = "test_narr_1"
    ideation = IdeationOutput(
        product_name="PulseOps",
        tagline="Autonomous Infrastructure Reliability That Never Sleeps",
        one_line_pitch="Predicting outages before alerts trigger",
        elevator_pitch="We monitor distributed system telemetry to detect cascading failures. Real-time remediation eliminates manual on-call paging.",
        core_features=[
            CoreFeature(name="Anomaly Detector", description="Real-time stream analysis", user_value="No false alerts"),
            CoreFeature(name="Auto-Rollback", description="Safe rollback execution", user_value="Zero downtime"),
            CoreFeature(name="Root Cause AI", description="Instant root cause diagnosis", user_value="Fast resolution")
        ],
        target_user_persona=TargetUserPersona(name="DevOps Lead", description="Manages clusters", pain_points=[]),
        monetization_model="Per host",
        pricing_suggestion="$20/host/month",
        differentiation_from_competitors="Active remediation instead of passive alerts"
    )
    deck = DeckGenerationOutput(deck_html_path="dummy.html", deck_url="/dummy", slides_count=8)

    narration_out = await run_narration_generation(run_id, ideation, deck)
    assert len(narration_out.spoken_script) > 100
    assert "PATTERN INTERRUPT HOOK" in narration_out.spoken_script
    assert "THE BLEEDING NECK PROBLEM" in narration_out.spoken_script
    assert "THE CONTRARIAN TRUTH" in narration_out.spoken_script
    assert "VERIFIABLE PROOF & DAYTONA RUNNING MVP" in narration_out.spoken_script
    assert narration_out.duration_estimate_seconds >= 40
    assert narration_out.duration_estimate_seconds <= 120

    script_path = Path("artifacts") / "narrations" / f"{run_id}_script.txt"
    assert script_path.exists()
