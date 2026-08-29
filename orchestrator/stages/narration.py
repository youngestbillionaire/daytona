import logging
from pathlib import Path
from typing import Callable, Optional
from orchestrator.config import settings
from orchestrator.models import DeckGenerationOutput, IdeationOutput, NarrationOutput

logger = logging.getLogger("founder0.stage.narration")

async def run_narration_generation(
    run_id: str,
    ideation: IdeationOutput,
    deck: DeckGenerationOutput,
    log: Optional[Callable[[str], None]] = None
) -> NarrationOutput:
    """
    Stage 2.15: NARRATION_GENERATION
    Generates an electrifying 60-90 second venture pitch voiceover script using
    classic rhetorical framing: Pattern Interrupt Hook → Bleeding Neck Pain → Contrarian Truth
    → 10x Moat Solution → Live Daytona Sandbox Proof → Exponential Traction Ask.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    emit(f"🎙️ [NARRATION_GENERATION] Composing high-impact persuasive voiceover script for '{ideation.product_name}'...")

    features_highlight = ", ".join(f.name for f in ideation.core_features[:3])

    # Build multi-phase rhetorical script with performance pacing markers
    spoken_script = (
        f"═══ {ideation.product_name.upper()} — 60-SECOND VENTURE PITCH ═══\n\n"
        f"[00:00 - 00:10 | PATTERN INTERRUPT HOOK]\n"
        f"What if the single biggest friction in your daily life wasn't a lack of tools, but the fact that every existing software forces you to do the painful emotional heavy-lifting yourself?\n"
        f"[PAUSE 1.5s]\n\n"
        f"[00:10 - 00:22 | THE BLEEDING NECK PROBLEM]\n"
        f"Millions of people struggle daily with {ideation.one_line_pitch.lower()}. Incumbent apps give you passive scores, awkward reminders, and spreadsheets — leaving you to absorb the confrontation and wasted hours.\n"
        f"[PAUSE 1.0s]\n\n"
        f"[00:22 - 00:36 | THE CONTRARIAN TRUTH]\n"
        f"Here is the non-obvious truth that incumbents completely miss: {ideation.contrarian_insight}\n"
        f"[PAUSE 1.5s]\n\n"
        f"[00:36 - 00:50 | THE 10X SOLUTION ARCHITECTURE]\n"
        f"That is why we built {ideation.product_name} — {ideation.tagline}. {ideation.elevator_pitch} Powered by {features_highlight}.\n"
        f"[PAUSE 1.0s]\n\n"
        f"[00:50 - 01:05 | VERIFIABLE PROOF & DAYTONA RUNNING MVP]\n"
        f"This isn't a Figma prototype or a concept deck. Our autonomous MVP is compiled and running live in a Daytona cloud sandbox right now. Scan the QR code on slide 6 to test the live application directly on your phone.\n"
        f"[PAUSE 1.2s]\n\n"
        f"[01:05 - 01:20 | THE COMPOUNDING MOAT & SEED ASK]\n"
        f"We are capturing a {ideation.tam_estimate} market through our viral beachhead: {ideation.go_to_market_wedge}. Our moat compounds with every transaction through our {ideation.technical_moat.lower()}.\n"
        f"We're opening our Seed round to scale distribution and build the definitive category king. Thank you."
    )

    narrations_dir = Path("artifacts") / "narrations"
    narrations_dir.mkdir(parents=True, exist_ok=True)
    script_file = narrations_dir / f"{run_id}_script.txt"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(spoken_script)

    word_count = len(spoken_script.split())
    # ~140 words per minute cadence excluding markup headers
    clean_words = [w for w in spoken_script.split() if not w.startswith("[") and not w.startswith("═══")]
    estimated_seconds = max(45, int(len(clean_words) / 2.4))

    emit(f"📝 [NARRATION_GENERATION] 60-second pitch script finalized ({len(clean_words)} spoken words, ~{estimated_seconds}s cadence).")
    emit(f"🔊 [NARRATION_GENERATION] Persuasion voiceover script saved to {script_file}")

    return NarrationOutput(
        spoken_script=spoken_script,
        audio_path=None,
        audio_url=None,
        duration_estimate_seconds=estimated_seconds
    )
