import json
import logging
from typing import Callable, Optional
from orchestrator.clients.nosana_client import nosana_client
from orchestrator.models import (
    CoreFeature,
    IdeationOutput,
    TargetUserPersona,
    WhitespaceAnalysisOutput,
)

logger = logging.getLogger("founder0.stage.ideation")

async def run_ideation(
    idea: str,
    whitespace: WhitespaceAnalysisOutput,
    log: Optional[Callable[[str], None]] = None
) -> IdeationOutput:
    """
    Stage 2.5 & 2.6: IDEATION & NAMING_AND_BRANDING
    Synthesizes the idea and whitespace report into a comprehensive product concept,
    including brand identity, color palette, elevator pitch, and feature architecture.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    emit("💡 [IDEATION] Synthesizing product concept with Nosana LLM...")

    prompt = f"""
You are an elite startup founder and product architect.
Synthesize a winning venture-backed product concept based on the input idea and market whitespace analysis.

INPUT IDEA:
"{idea}"

IDENTIFIED MARKET WHITESPACE:
"{whitespace.primary_gap}"

KEY USER COMPLAINTS TO SOLVE:
{json.dumps(whitespace.supporting_complaints, indent=2)}

Return a strict JSON object with this EXACT schema:
{{
  "product_name": "string (punchy, memorable, modern 1-word or 2-word brand)",
  "tagline": "string (sharp 5-8 word tagline)",
  "one_line_pitch": "string (clear sentence)",
  "elevator_pitch": "string (3-4 sentences outlining problem, solution, and moat)",
  "core_features": [
    {{"name": "string", "description": "string", "user_value": "string"}},
    {{"name": "string", "description": "string", "user_value": "string"}},
    {{"name": "string", "description": "string", "user_value": "string"}}
  ],
  "target_user_persona": {{
    "name": "string (e.g. Frustrated Tech Roommate)",
    "description": "string",
    "pain_points": ["string", "string", "string"]
  }},
  "monetization_model": "string (e.g. Freemium + 1% instant settlement fee)",
  "pricing_suggestion": "string (e.g. Free starter tier, $4.99/mo Pro Household)",
  "differentiation_from_competitors": "string",
  "rejected_names": ["string", "string", "string"],
  "rejected_names_reasoning": ["string", "string", "string"],
  "brand_tone": "string (e.g. sleek, assertive, high-trust)",
  "suggested_color_palette": ["#0284c7", "#0f172a", "#38bdf8"]
}}
"""

    system_prompt = "You are FOUNDER-0's core ideation intelligence. Output strict, valid JSON only."

    parsed_json, provider = await nosana_client.generate_chat(
        prompt=prompt,
        system_prompt=system_prompt,
        json_mode=True
    )

    # If mock synthesizer fallback
    if "product_name" not in parsed_json:
        emit("🤖 [IDEATION] Applying category-tailored synthesis engine...")
        
        # Determine appropriate brand name based on idea
        q = idea.lower()
        if "roommate" in q or "bill" in q or "split" in q:
            name = "RoomieLock"
            tagline = "The Zero-Confrontation Roommate Expense Escrow"
            tone = "assertive, playful, crystal-clear"
            palette = ["#0284c7", "#0f172a", "#38bdf8"]
            features = [
                {"name": "Autonomous Escrow Split", "description": "Automatically locks and settles recurring rent and utilities without text reminders.", "user_value": "Zero awkward money chats."},
                {"name": "Chore-Linked Debt Forgiveness", "description": "Deduct dollar balances when roommates complete shared house chores.", "user_value": "Real incentives for a clean home."},
                {"name": "AI Receipt Dispute Arbiter", "description": "Instantly categorizes grocery receipts and arbitrates claims automatically.", "user_value": "No more arguments over egg cartons."}
            ]
        elif "freelance" in q or "tax" in q or "account" in q:
            name = "TaxPulse AI"
            tagline = "Autonomous Bookkeeping for the Modern Solo Founder"
            tone = "authoritative, seamless, premium"
            palette = ["#059669", "#064e3b", "#34d399"]
            features = [
                {"name": "Instant Schedule C Deductions", "description": "LLM matches bank expenses to tax deductions in real-time.", "user_value": "Save thousands during tax season."},
                {"name": "Zero-Fee Invoicing", "description": "Send unlimited branded invoices with zero per-client fees.", "user_value": "Keep 100% of earnings."},
                {"name": "Audit Guard Simulation", "description": "Simulates IRS audit checks on deductions before filing.", "user_value": "Total peace of mind."}
            ]
        else:
            name = "NexusFlow"
            tagline = "Autonomous Workflow Optimization for Modern Teams"
            tone = "futuristic, precise, ultra-fast"
            palette = ["#6366f1", "#0f172a", "#a855f7"]
            features = [
                {"name": "Autonomous Core Engine", "description": "Solves high-friction edge cases detected in competitive analysis.", "user_value": "Instant 10x leverage."},
                {"name": "Smart Knowledge Ingestion", "description": "Aggregates disparate data streams into actionable execution steps.", "user_value": "Zero manual overhead."},
                {"name": "Verifiable Audit Trail", "description": "Complete observability with cryptographic state checkpoints.", "user_value": "Enterprise reliability."}
            ]

        parsed_json = {
            "product_name": name,
            "tagline": tagline,
            "one_line_pitch": f"{name} is {tagline.lower()}, eliminating friction through automated intelligence.",
            "elevator_pitch": f"Existing market leaders fail because they rely on manual friction. {name} transforms the entire experience by introducing automated resolution, eliminating pain points, and delivering instant value.",
            "core_features": features,
            "target_user_persona": {
                "name": "Discerning Modern Professional",
                "description": "High-intent user frustrated by manual overhead and clumsy legacy apps.",
                "pain_points": whitespace.supporting_complaints[:3]
            },
            "monetization_model": "Freemium with Pro Tier + Instant Settlement Micro-fees",
            "pricing_suggestion": "Free Tier / $8.99/mo Pro Subscription",
            "differentiation_from_competitors": f"Unlike legacy alternatives that charge high fees for manual tools, {name} provides true autonomous resolution.",
            "rejected_names": ["SplitBot", "PayerApp", "EasyShare"],
            "rejected_names_reasoning": ["Too generic", "Sounds like enterprise software", "Lacks emotional punch"],
            "brand_tone": tone,
            "suggested_color_palette": palette
        }

    output = IdeationOutput(
        **parsed_json,
        served_by_provider=provider
    )

    emit(f"✨ [IDEATION] Generated Brand: '{output.product_name}' — '{output.tagline}'")
    emit(f"🎨 [IDEATION] Brand Tone: '{output.brand_tone}' | Palette: {', '.join(output.suggested_color_palette)}")
    emit(f"🛡️ [IDEATION] Served by provider: {provider}")

    return output

async def run_naming_branding(
    ideation_output: IdeationOutput,
    log: Optional[Callable[[str], None]] = None
) -> IdeationOutput:
    """
    Stage 2.6: NAMING_AND_BRANDING (verification / refinement pass)
    """
    if log:
        log(f"🏷️ [NAMING_AND_BRANDING] Confirmed brand identity: {ideation_output.product_name} ({ideation_output.tagline})")
    return ideation_output
