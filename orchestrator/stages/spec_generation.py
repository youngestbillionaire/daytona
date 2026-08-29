import json
import logging
from typing import Callable, Optional
from orchestrator.clients.nosana_client import nosana_client
from orchestrator.models import (
    IdeationOutput,
    SpecDataModel,
    SpecFeature,
    SpecField,
    SpecGenerationOutput,
    SpecPage,
)

logger = logging.getLogger("founder0.stage.spec_generation")

async def run_spec_generation(
    ideation: IdeationOutput,
    log: Optional[Callable[[str], None]] = None
) -> SpecGenerationOutput:
    """
    Stage 2.7: SPEC_GENERATION
    Translates product concepts and core features into structured engineering specs:
    UI component definitions, data schemas, and interaction flows.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    emit(f"📐 [SPEC_GENERATION] Transforming concept '{ideation.product_name}' into technical specification...")

    prompt = f"""
Convert this startup product concept into a concrete, structured technical MVP engineering spec.

PRODUCT: {ideation.product_name} - {ideation.tagline}
ELEVATOR PITCH: {ideation.elevator_pitch}
CORE FEATURES:
{json.dumps([f.model_dump() for f in ideation.core_features], indent=2)}

Return a strict JSON object with this EXACT schema:
{{
  "pages": [
    {{"route": "/", "purpose": "Interactive Landing Page & MVP Demo", "sections": ["hero", "features", "signup-cta"]}}
  ],
  "data_models": [
    {{"name": "WaitlistSignup", "fields": [{{"name": "email", "type": "string"}}, {{"name": "created_at", "type": "datetime"}}]}},
    {{"name": "AppEvent", "fields": [{{"name": "event_type", "type": "string"}}, {{"name": "payload", "type": "string"}}]}}
  ],
  "feature_implementations": [
    {{"feature_name": "string", "ui_description": "string", "component_name": "PascalCaseComponent"}}
  ]
}}
"""
    parsed_json, provider = await nosana_client.generate_chat(
        prompt=prompt,
        system_prompt="You are a principal frontend engineer. Output strict JSON only.",
        json_mode=True
    )

    if "feature_implementations" not in parsed_json:
        # Structured deterministic spec generator
        features = []
        for idx, feat in enumerate(ideation.core_features):
            cname = "".join(w.capitalize() for w in feat.name.replace("-", " ").replace("_", " ").split()) + "Card"
            features.append(SpecFeature(
                feature_name=feat.name,
                ui_description=f"Interactive card rendering {feat.name} with live demo toggles and value indicators for {feat.user_value}.",
                component_name=cname
            ))
        
        output = SpecGenerationOutput(
            pages=[
                SpecPage(route="/", purpose="Interactive Landing Page & MVP Demo", sections=["hero", "features", "signup-cta"])
            ],
            data_models=[
                SpecDataModel(name="WaitlistSignup", fields=[
                    SpecField(name="email", type="string"),
                    SpecField(name="created_at", type="datetime")
                ]),
                SpecDataModel(name="AppEvent", fields=[
                    SpecField(name="event_type", type="string"),
                    SpecField(name="payload", type="string")
                ])
            ],
            feature_implementations=features
        )
    else:
        output = SpecGenerationOutput(**parsed_json)

    emit(f"📋 [SPEC_GENERATION] Generated specification for {len(output.feature_implementations)} modular components and {len(output.data_models)} data schemas.")
    for feat in output.feature_implementations:
        emit(f"  └─ Component: {feat.component_name} ({feat.feature_name})")

    return output
