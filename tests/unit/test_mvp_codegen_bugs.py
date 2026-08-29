import pytest
from orchestrator.stages.mvp_codegen import validate_component_code, escape_jsx_string, run_mvp_codegen
from orchestrator.stages.spec_generation import sanitize_component_name
from orchestrator.models import (
    IdeationOutput,
    MvpScaffoldOutput,
    SpecDataModel,
    SpecFeature,
    SpecGenerationOutput,
    SpecPage,
    TargetUserPersona,
)
from orchestrator.clients.daytona_client import daytona_client

def test_validate_component_code_valid():
    valid_code = """
export default function ValidComponent() {
  const data = [1, 2, 3];
  return (
    <div>
      {data.map(d => (<span key={d}>{d}</span>))}
    </div>
  );
}
"""
    assert validate_component_code(valid_code) is True

def test_validate_component_code_missing_export():
    code = "function Foo() { return <div />; }"
    assert validate_component_code(code) is False

def test_validate_component_code_eval_injection():
    code = """
export default function Malicious() {
  eval('alert(1)');
  return <div />;
}
"""
    assert validate_component_code(code) is False

def test_validate_component_code_unbalanced_braces():
    code = "export default function Broken() { return <div>{foo; </div>; }"
    assert validate_component_code(code) is False

def test_validate_component_code_unbalanced_parentheses():
    code = "export default function Broken() { return (<div>hello</div>; }"
    assert validate_component_code(code) is False

def test_validate_component_code_unbalanced_brackets():
    code = "export default function Broken() { const x = [1, 2; return <div>{x}</div>; }"
    assert validate_component_code(code) is False

def test_validate_component_code_empty_and_none():
    assert validate_component_code("") is False
    assert validate_component_code("   ") is False
    assert validate_component_code(None) is False

def test_escape_jsx_string():
    assert escape_jsx_string(None) == ""
    assert escape_jsx_string("") == ""
    assert escape_jsx_string('Hello "World"') == 'Hello \\"World\\"'
    assert escape_jsx_string('<script>alert("XSS")</script>Normal Text') == 'alert(\\"XSS\\")Normal Text'

def test_sanitize_component_name():
    assert sanitize_component_name("Autonomous Escrow") == "AutonomousEscrowCard"
    assert sanitize_component_name("123 numerical feature") == "Feature123NumericalFeatureCard"
    assert sanitize_component_name("AI-Powered Real-Time Analytics!") == "AIPoweredRealTimeAnalyticsCard"
    assert sanitize_component_name("CustomDashboardView") == "CustomDashboardView"
    assert sanitize_component_name("SecurityModule") == "SecurityModule"
    assert sanitize_component_name("") == "FeatureCard"

@pytest.mark.asyncio
async def test_codegen_with_special_characters():
    sandbox = await daytona_client.create_sandbox()
    scaffold = MvpScaffoldOutput(sandbox_id=sandbox.sandbox_id, workspace_path=sandbox.workspace_path)
    
    ideation = IdeationOutput(
        product_name="XSS & Quote Test",
        tagline="A test product that handles quotes \"properly\" and safely",
        one_line_pitch="Testing special <script> chars and quotes",
        elevator_pitch="Full pitch with tricky symbols: & < > ' \"",
        core_features=[],
        target_user_persona=TargetUserPersona(name="Tester", description="Tests edge cases", pain_points=[]),
        monetization_model="Freemium",
        pricing_suggestion="Free / $10",
        differentiation_from_competitors="None"
    )
    
    spec = SpecGenerationOutput(
        pages=[SpecPage(route="/", purpose="Test", sections=["hero"])],
        data_models=[SpecDataModel(name="Test", fields=[])],
        feature_implementations=[
            SpecFeature(
                feature_name='Feature with "Double Quotes" & <script>alert(1)</script>',
                ui_description='Description with "quotes" and {nested} braces',
                component_name="SpecialCharCard"
            )
        ]
    )
    
    codegen_res = await run_mvp_codegen(scaffold, ideation, spec)
    assert codegen_res.static_check_passed is True
    assert len(codegen_res.generated_files) == 2  # Component + page.tsx
