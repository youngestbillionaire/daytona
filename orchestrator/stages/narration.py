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
    Generates an electrifying 60-second venture pitch voiceover script using
    classic rhetorical framing: Hook → Loss Aversion → Contrarian Insight → Solution → Proof → Ask.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    emit(f"🎙️ [NARRATION_GENERATION] Composing persuasive 60-second pitch voiceover for '{ideation.product_name}'...")

    # Build multi-phase rhetorical script
    spoken_script = (
        f"[HOOK]\n"
        f"What if the biggest friction in your daily life wasn't a lack of tools, but the fact that existing software forces you to do the hard work yourself?\n\n"
        f"[THE BLEEDING NECK PROBLEM]\n"
        f"Millions of people struggle with {ideation.one_line_pitch.lower()}. Incumbent apps give you passive scores or clunky reminders, leaving you to deal with the awkward, stressful confrontation.\n\n"
        f"[THE CONTRARIAN INSIGHT]\n"
        f"Here is what everyone else gets wrong: {ideation.contrarian_insight}\n\n"
        f"[THE SOLUTION]\n"
        f"That is why we built {ideation.product_name} — {ideation.tagline}. {ideation.elevator_pitch}\n\n"
        f"[VERIFIABLE PROOF]\n"
        f"We didn't just write a slide deck. Our autonomous MVP is already running live in a Daytona cloud sandbox right now. You can scan the QR code on slide 6 to test it with your phone immediately.\n\n"
        f"[THE DEFENSE & MARKET]\n"
        f"We're tackling a {ideation.tam_estimate} market with a clear wedge: {ideation.go_to_market_wedge}. Our moat compounds with every transaction through our {ideation.technical_moat.lower()}.\n\n"
        f"[THE ASK]\n"
        f"We're opening our Seed round to accelerate our autonomous growth engine. Join us in building the definitive category leader. Thank you."
    )

    narrations_dir = Path("artifacts") / "narrations"
    narrations_dir.mkdir(parents=True, exist_ok=True)
    script_file = narrations_dir / f"{run_id}_script.txt"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(spoken_script)

    word_count = len(spoken_script.split())
    estimated_seconds = int(word_count / 2.5)  # ~150 words per minute cadence

    emit(f"📝 [NARRATION_GENERATION] 60-second pitch script finalized ({word_count} words, ~{estimated_seconds}s spoken duration).")
    emit(f"🔊 [NARRATION_GENERATION] Persuasion script saved to {script_file}")

    return NarrationOutput(
        spoken_script=spoken_script,
        audio_path=None,
        audio_url=None,
        duration_estimate_seconds=estimated_seconds
    )
