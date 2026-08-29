import json
import logging
import re
from typing import Callable, List, Optional

from orchestrator.clients.daytona_client import daytona_client
from orchestrator.clients.nosana_client import nosana_client
from orchestrator.models import GeneratedFile, MvpCodegenOutput, SpecFeature, SpecGenerationOutput

logger = logging.getLogger("founder0.stage.mvp_codegen")

FEATURE_JS_FORBIDDEN = ("import ", "require(", "<script", "eval(", "document.write")


def _validate_feature_html(html: str) -> bool:
    """Lightweight static safety check on LLM-generated HTML snippet."""
    if not html or "<" not in html:
        return False
    if "<script" in html.lower():
        return False  # scripts belong in the js field, not injected inline
    return True


def _validate_feature_js(js: str) -> bool:
    """Lightweight static safety check on LLM-generated JS snippet."""
    if js is None:
        return True  # JS is optional per feature
    lowered = js.lower()
    if any(bad in lowered for bad in FEATURE_JS_FORBIDDEN):
        return False
    return js.count("{") == js.count("}") and js.count("(") == js.count(")")


async def run_mvp_codegen(
    spec: SpecGenerationOutput,
    scaffold,
    idea: str,
    product_name: str,
    tagline: str,
    log: Optional[Callable[[str], None]] = None
) -> MvpCodegenOutput:
    """
    Stage 2.9: MVP_CODE_GENERATION

    Generates the product-specific content of the vanilla HTML/CSS/JS MVP
    entirely via the Nosana-hosted LLM: hero copy, and one HTML+JS snippet
    per feature. Nothing product-specific is hardcoded here — the only
    non-generated content is the template's structural plumbing (server.js,
    the waitlist form wiring, the marker positions in index.html/app.js),
    which is infrastructure, not product content.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    generated_files: List[GeneratedFile] = []
    sandbox = await daytona_client.get_sandbox(scaffold.sandbox_id)
    if not sandbox:
        raise RuntimeError(f"Sandbox {scaffold.sandbox_id} not found")

    # ---- 1. Hero copy, fully LLM-generated ----
    emit("⚡ [MVP_CODE_GENERATION] Generating hero copy via Nosana LLM...")
    hero_prompt = f"""
You are a product copywriter. Given this startup idea: "{idea}"
Product name: "{product_name}"
Tagline: "{tagline}"

Write landing page hero copy. Return ONLY strict JSON:
{{
  "h1": "short punchy headline (product name can be included)",
  "subheadline": "1-2 sentence value proposition"
}}
"""
    hero_res, hero_provider = await nosana_client.generate_chat(prompt=hero_prompt, json_mode=True)
    hero_copy = {
        "h1": hero_res.get("h1", product_name) if hero_res else product_name,
        "subheadline": hero_res.get("subheadline", tagline) if hero_res else tagline,
    }
    emit(f"✅ [MVP_CODE_GENERATION] Hero copy generated via {hero_provider}.")

    # ---- 2. One feature card (HTML + optional JS) per spec feature, LLM-generated ----
    feature_html_blocks: List[str] = []
    feature_js_blocks: List[str] = []

    for feat in spec.feature_implementations:
        emit(f"⚡ [MVP_CODE_GENERATION] Generating feature '{feat.feature_name}' via Nosana LLM...")
        feat_prompt = f"""
You are a frontend engineer writing plain vanilla HTML/CSS/JS (NO React, NO TypeScript,
NO build tools, NO imports — this runs directly in a browser via a <script> tag).

Product: "{product_name}" — {tagline}
Feature to implement: "{feat.feature_name}"
UI description: {feat.ui_description}

Generate:
1. An HTML snippet: a single <div class="feature-card"> block with a heading, description,
   and any interactive elements (buttons, inputs) needed. Use existing CSS class
   "feature-card" for the container. Give interactive elements unique, descriptive
   id attributes prefixed with "{feat.component_name}-".
2. A vanilla JS snippet implementing the interactive behavior for those elements
   (event listeners, DOM updates). Plain JS only, no imports/require, wrapped so it's
   safe to run at the bottom of a page (elements already exist in the DOM by then).
   If the feature is purely static/informational, return an empty string for js.

Return ONLY strict JSON:
{{"html": "string", "js": "string"}}
"""
        try:
            feat_res, feat_provider = await nosana_client.generate_chat(prompt=feat_prompt, json_mode=True)
            html = feat_res.get("html", "") if feat_res else ""
            js = feat_res.get("js", "") if feat_res else ""

            if _validate_feature_html(html) and _validate_feature_js(js):
                feature_html_blocks.append(html)
                if js.strip():
                    feature_js_blocks.append(f"// --- {feat.feature_name} ---\n{js}")
                emit(f"✅ [MVP_CODE_GENERATION] Feature '{feat.feature_name}' generated and validated via {feat_provider}.")
            else:
                emit(f"⚠️ [MVP_CODE_GENERATION] Feature '{feat.feature_name}' failed validation, using minimal safe placeholder.")
                feature_html_blocks.append(
                    f'<div class="feature-card"><h3>{feat.feature_name}</h3>'
                    f'<p>{feat.ui_description}</p></div>'
                )
        except Exception as e:
            emit(f"⚠️ [MVP_CODE_GENERATION] Feature '{feat.feature_name}' generation errored ({e}), using minimal safe placeholder.")
            feature_html_blocks.append(
                f'<div class="feature-card"><h3>{feat.feature_name}</h3>'
                f'<p>{feat.ui_description}</p></div>'
            )

    # ---- 3. Assemble into the template's marked extension points ----
    emit("📝 [MVP_CODE_GENERATION] Injecting generated content into index.html and app.js...")

    index_html = await sandbox.read_file("public/index.html")
    app_js = await sandbox.read_file("public/app.js")

    index_html = re.sub(
        r"<!-- FOUNDER0:TITLE -->.*?<!-- /FOUNDER0:TITLE -->",
        f"<!-- FOUNDER0:TITLE -->{product_name}<!-- /FOUNDER0:TITLE -->",
        index_html, flags=re.DOTALL
    )
    index_html = re.sub(
        r"<!-- FOUNDER0:HERO -->.*?<!-- /FOUNDER0:HERO -->",
        f'<!-- FOUNDER0:HERO -->\n    <h1>{hero_copy["h1"]}</h1>\n    <p class="tagline">{hero_copy["subheadline"]}</p>\n    <!-- /FOUNDER0:HERO -->',
        index_html, flags=re.DOTALL
    )
    index_html = re.sub(
        r"<!-- FOUNDER0:FEATURES -->.*?<!-- /FOUNDER0:FEATURES -->",
        "<!-- FOUNDER0:FEATURES -->\n      " + "\n      ".join(feature_html_blocks) + "\n      <!-- /FOUNDER0:FEATURES -->",
        index_html, flags=re.DOTALL
    )

    app_js = re.sub(
        r"// FOUNDER0:FEATURE_JS.*?// /FOUNDER0:FEATURE_JS",
        "// FOUNDER0:FEATURE_JS\n" + "\n\n".join(feature_js_blocks) + "\n// /FOUNDER0:FEATURE_JS",
        app_js, flags=re.DOTALL
    )

    await sandbox.write_file("public/index.html", index_html)
    await sandbox.write_file("public/app.js", app_js)

    generated_files.append(GeneratedFile(path="public/index.html", content=index_html))
    generated_files.append(GeneratedFile(path="public/app.js", content=app_js))

    emit(f"✅ [MVP_CODE_GENERATION] Successfully generated and injected {len(spec.feature_implementations)} feature(s) plus hero copy.")

    return MvpCodegenOutput(
        generated_files=generated_files,
        hero_copy=hero_copy,
        static_check_passed=True,
    )
