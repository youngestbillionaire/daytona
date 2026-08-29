import json
import logging
import re
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

def sanitize_component_name(raw_name: str) -> str:
    """Generate a clean, valid PascalCase React component name."""
    if not raw_name:
        return "FeatureCard"
    clean = re.sub(r"[^a-zA-Z0-9\s_-]", " ", raw_name)
    words = clean.replace("-", " ").replace("_", " ").split()
    if not words:
        return "FeatureCard"

    pascal_words = []
    for w in words:
        if len(w) == 1:
            pascal_words.append(w.upper())
        elif w[0].islower():
            pascal_words.append(w[0].upper() + w[1:])
        else:
            pascal_words.append(w)

    pascal = "".join(pascal_words)
    if not (pascal.endswith("Card") or pascal.endswith("Module") or pascal.endswith("View")):
        pascal += "Card"
    if pascal[0].isdigit():
        pascal = "Feature" + pascal
    return pascal

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
You are a Principal Frontend Architect translating a venture product specification into production Next.js 14 component architectures.

PRODUCT: {ideation.product_name} - {ideation.tagline}
ONE-LINE PITCH: {ideation.one_line_pitch}
ELEVATOR PITCH: {ideation.elevator_pitch}
TARGET PERSONA: {ideation.target_user_persona.name}
CORE FEATURES:
{json.dumps([f.model_dump() for f in ideation.core_features], indent=2)}

TECHNICAL ARCHITECTURE REQUIREMENTS:
1. Generate modular React Client components for each core feature with PascalCase names ending in 'Card'.
2. Provide specific UI interaction descriptions detailing interactive state (toggles, calculations, simulated workflows, feedback toasts).
3. Include SQLite data models for user signup, analytics events, and feature-specific transaction/commitment logs.

Return a strict JSON object with this EXACT schema:
{{
  "pages": [
    {{"route": "/", "purpose": "Interactive Landing Page & Verified Live MVP Demo", "sections": ["hero", "problem-breakdown", "features-grid", "live-demo-interactive", "signup-cta"]}}
  ],
  "data_models": [
    {{"name": "WaitlistSignup", "fields": [{{"name": "email", "type": "string"}}, {{"name": "created_at", "type": "datetime"}}]}},
    {{"name": "AppEvent", "fields": [{{"name": "event_type", "type": "string"}}, {{"name": "payload", "type": "string"}}]}}
  ],
  "feature_implementations": [
    {{"feature_name": "string", "ui_description": "string (concrete interaction description with state indicators)", "component_name": "PascalCaseComponentCard"}}
  ]
}}
"""
    parsed_json, provider = await nosana_client.generate_chat(
        prompt=prompt,
        system_prompt="You are a Principal Frontend Architect at a top-tier engineering firm. Output strict, valid JSON only.",
        json_mode=True
    )

    if "feature_implementations" not in parsed_json or not parsed_json["feature_implementations"]:
        # Structured deterministic spec generator
        features = []
        for idx, feat in enumerate(ideation.core_features):
            cname = sanitize_component_name(feat.name)
            features.append(SpecFeature(
                feature_name=feat.name,
                ui_description=f"Interactive card rendering {feat.name} with live simulation state, status metrics, and payoff indicator for {feat.user_value}.",
                component_name=cname
            ))

        output = SpecGenerationOutput(
            pages=[
                SpecPage(route="/", purpose="Interactive Landing Page & Verified Live MVP Demo", sections=["hero", "features-grid", "signup-cta"])
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
        # Sanitize component names in returned json to guarantee valid TypeScript identifiers
        for feat in parsed_json.get("feature_implementations", []):
            if "component_name" in feat:
                feat["component_name"] = sanitize_component_name(feat["component_name"])
            elif "feature_name" in feat:
                feat["component_name"] = sanitize_component_name(feat["feature_name"])
        output = SpecGenerationOutput(**parsed_json)

    emit(f"📋 [SPEC_GENERATION] Generated specification for {len(output.feature_implementations)} modular components and {len(output.data_models)} data schemas.")
    for feat in output.feature_implementations:
        emit(f"  └─ Component: {feat.component_name} ({feat.feature_name})")

    return output
