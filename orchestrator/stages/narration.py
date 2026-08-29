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
    Generates a high-energy 45-second spoken pitch voiceover script and optional TTS audio artifact.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    emit(f"🎙️ [NARRATION_GENERATION] Composing 45-second spoken pitch script for '{ideation.product_name}'...")

    spoken_script = (
        f"Hi everyone. We built {ideation.product_name} because {ideation.one_line_pitch}. "
        f"Today, users are frustrated by legacy tools that require tedious manual coordination. "
        f"With {ideation.product_name}, {ideation.elevator_pitch} "
        f"Our autonomous MVP is already running live in a Daytona sandbox—you can scan the QR code to test it right now. "
        f"We're scaling our early waitlist and would love your support. Thank you!"
    )

    narrations_dir = Path("artifacts") / "narrations"
    narrations_dir.mkdir(parents=True, exist_ok=True)
    script_file = narrations_dir / f"{run_id}_script.txt"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(spoken_script)

    emit(f"📝 [NARRATION_GENERATION] Spoken script finalized ({len(spoken_script.split())} words, ~45s cadence).")
    emit("🔊 [NARRATION_GENERATION] Script saved as artifact.")

    return NarrationOutput(
        spoken_script=spoken_script,
        audio_path=None,
        audio_url=None,
        duration_estimate_seconds=45
    )
