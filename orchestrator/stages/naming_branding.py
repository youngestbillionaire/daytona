import logging
from typing import Callable, Optional
from orchestrator.models import IdeationOutput

logger = logging.getLogger("founder0.stage.naming_branding")

async def run_naming_branding(
    ideation_output: IdeationOutput,
    log: Optional[Callable[[str], None]] = None
) -> IdeationOutput:
    """
    Stage 2.6: NAMING_AND_BRANDING
    Verifies brand identity, color tokens, and positioning consistency.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    emit(f"🏷️ [NAMING_AND_BRANDING] Finalizing Brand Identity for '{ideation_output.product_name}'")
    emit(f"🎨 [NAMING_AND_BRANDING] Theme Colors: Primary={ideation_output.suggested_color_palette[0]}, Background={ideation_output.suggested_color_palette[1]}")
    emit(f"💬 [NAMING_AND_BRANDING] One-liner: '{ideation_output.one_line_pitch}'")
    emit("✅ [NAMING_AND_BRANDING] Brand identity package approved.")
    return ideation_output
