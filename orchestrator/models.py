from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Integer, JSON, String, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# ==========================================
# Database ORM Models
# ==========================================

class PipelineStage(str, Enum):
    IDEA_RECEIVED = "IDEA_RECEIVED"
    MARKET_RECON = "MARKET_RECON"
    COMPETITOR_ENRICHMENT = "COMPETITOR_ENRICHMENT"
    OPPORTUNITY_GRAPH = "OPPORTUNITY_GRAPH"
    WHITESPACE_ANALYSIS = "WHITESPACE_ANALYSIS"
    IDEATION = "IDEATION"
    NAMING_AND_BRANDING = "NAMING_AND_BRANDING"
    SPEC_GENERATION = "SPEC_GENERATION"
    MVP_SCAFFOLD = "MVP_SCAFFOLD"
    MVP_CODE_GENERATION = "MVP_CODE_GENERATION"
    MVP_BUILD_AND_TEST = "MVP_BUILD_AND_TEST"
    MVP_SELF_HEAL_LOOP = "MVP_SELF_HEAL_LOOP"
    MVP_DEPLOY_PREVIEW = "MVP_DEPLOY_PREVIEW"
    SCREENSHOT_CAPTURE = "SCREENSHOT_CAPTURE"
    DECK_GENERATION = "DECK_GENERATION"
    NARRATION_GENERATION = "NARRATION_GENERATION"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"

class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"

class Run(Base):
    __tablename__ = "runs"

    id = Column(String(64), primary_key=True, index=True)
    idea = Column(Text, nullable=False)
    status = Column(String(32), default="pending", index=True)
    current_stage = Column(String(64), default=PipelineStage.IDEA_RECEIVED.value)
    product_name = Column(String(128), nullable=True)
    tagline = Column(String(256), nullable=True)
    preview_url = Column(String(512), nullable=True)
    deck_path = Column(String(512), nullable=True)
    narration_path = Column(String(512), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, default=dict)

    events = relationship("StageEvent", back_populates="run", cascade="all, delete-orphan", order_by="StageEvent.id")
    artifacts = relationship("Artifact", back_populates="run", cascade="all, delete-orphan")

class StageEvent(Base):
    __tablename__ = "stage_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("runs.id"), nullable=False, index=True)
    stage = Column(String(64), nullable=False, index=True)
    status = Column(String(32), default=StageStatus.PENDING.value)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    input_json = Column(JSON, nullable=True)
    output_json = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    logs = Column(JSON, default=list)  # List of string log lines

    run = relationship("Run", back_populates="events")

class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(String(64), primary_key=True, index=True)
    run_id = Column(String(64), ForeignKey("runs.id"), nullable=False, index=True)
    stage = Column(String(64), nullable=False)
    name = Column(String(256), nullable=False)
    artifact_type = Column(String(64), nullable=False)  # 'json', 'html', 'pdf', 'image', 'audio', 'zip'
    file_path = Column(String(512), nullable=False)
    url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("Run", back_populates="artifacts")

# ==========================================
# Pydantic Schemas for API & Stage I/O
# ==========================================

# 2.1 Market Recon
class CompetitorRecon(BaseModel):
    name: str
    url: str
    description: str
    complaints: List[str] = Field(default_factory=list)
    source_queries: List[str] = Field(default_factory=list)

class MarketReconOutput(BaseModel):
    category: str = "general"
    extracted_keywords: List[str] = Field(default_factory=list)
    competitors: List[CompetitorRecon] = Field(default_factory=list)
    raw_complaint_pool: List[str] = Field(default_factory=list)

# 2.2 Competitor Enrichment
class PricingTier(BaseModel):
    name: str
    price: str
    billing_period: str = "month"

class EnrichedCompetitor(BaseModel):
    name: str
    url: str
    description: str
    value_prop: str
    features: List[str] = Field(default_factory=list)
    pricing_tiers: List[PricingTier] = Field(default_factory=list)
    complaints: List[str] = Field(default_factory=list)

class CompetitorEnrichmentOutput(BaseModel):
    enriched_competitors: List[EnrichedCompetitor] = Field(default_factory=list)

# 2.3 Opportunity Graph
class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # 'Idea', 'Competitor', 'Feature', 'Complaint', 'PricingTier'
    properties: Dict[str, Any] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str  # 'OFFERS', 'HAS_PRICING', 'ABOUT', 'RAISED_AGAINST', 'TARGETS'
    properties: Dict[str, Any] = Field(default_factory=dict)

class OpportunityGraphOutput(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0
    graph_summary: Dict[str, int] = Field(default_factory=dict)

# 2.4 Whitespace Analysis
class WhitespaceAnalysisOutput(BaseModel):
    primary_gap: str
    supporting_complaints: List[str] = Field(default_factory=list)
    underserved_features: List[str] = Field(default_factory=list)
    competitor_coverage_map: Dict[str, int] = Field(default_factory=dict)

# 2.5 & 2.6 Ideation + Naming and Branding
class CoreFeature(BaseModel):
    name: str
    description: str
    user_value: str

class TargetUserPersona(BaseModel):
    name: str
    description: str
    pain_points: List[str] = Field(default_factory=list)

class IdeationOutput(BaseModel):
    product_name: str
    tagline: str
    one_line_pitch: str
    elevator_pitch: str
    core_features: List[CoreFeature]
    target_user_persona: TargetUserPersona
    monetization_model: str
    pricing_suggestion: str
    differentiation_from_competitors: str
    contrarian_insight: str = "The market assumes the current approach is good enough — it isn't."
    technical_moat: str = "Proprietary autonomous resolution engine with network-effect data flywheel."
    tam_estimate: str = "$2.4B global addressable market"
    go_to_market_wedge: str = "Viral organic adoption through existing pain-point communities on Reddit and Twitter."
    psychological_hook: str = "Loss aversion — users adopt because the cost of NOT switching is viscerally painful."
    ten_x_factor: str = "Not 2x better, but eliminates the problem entirely by removing human friction from the loop."
    rejected_names: List[str] = Field(default_factory=list)
    rejected_names_reasoning: List[str] = Field(default_factory=list)
    brand_tone: str = "modern, bold, minimalist"
    suggested_color_palette: List[str] = Field(default_factory=lambda: ["#0284c7", "#0f172a", "#38bdf8"])
    served_by_provider: str = "nosana"

# 2.7 Spec Generation
class SpecPage(BaseModel):
    route: str = "/"
    purpose: str = "landing page"
    sections: List[str] = Field(default_factory=lambda: ["hero", "features", "signup-cta"])

class SpecField(BaseModel):
    name: str
    type: str

class SpecDataModel(BaseModel):
    name: str
    fields: List[SpecField] = Field(default_factory=list)

class SpecFeature(BaseModel):
    feature_name: str
    ui_description: str
    component_name: str

class SpecGenerationOutput(BaseModel):
    pages: List[SpecPage] = Field(default_factory=list)
    data_models: List[SpecDataModel] = Field(default_factory=list)
    feature_implementations: List[SpecFeature] = Field(default_factory=list)

# 2.8 MVP Scaffold
class MvpScaffoldOutput(BaseModel):
    sandbox_id: str
    workspace_path: str
    template_used: str = "nextjs-sqlite-starter"
    install_exit_code: int = 0
    install_logs: str = ""

# 2.9 MVP Code Generation
class GeneratedFile(BaseModel):
    path: str
    content: str
    component_name: Optional[str] = None

class MvpCodegenOutput(BaseModel):
    generated_files: List[GeneratedFile] = Field(default_factory=list)
    hero_copy: Dict[str, str] = Field(default_factory=dict)
    static_check_passed: bool = True

# 2.10 MVP Build and Test
class MvpBuildTestOutput(BaseModel):
    build_exit_code: int
    build_output: str
    test_passed: bool
    smoke_test_url: Optional[str] = None
    smoke_test_status_code: Optional[int] = None

# 2.11 MVP Self Heal Loop
class MvpSelfHealOutput(BaseModel):
    self_heal_attempts: int = 0
    healed_features: List[str] = Field(default_factory=list)
    degraded_features: List[str] = Field(default_factory=list)
    final_build_success: bool = True
    summary: str = ""

# 2.12 MVP Deploy Preview
class MvpDeployOutput(BaseModel):
    preview_url: str
    port: int = 3000
    health_check_passed: bool = True
    sandbox_status: str = "running"

# 2.13 Screenshot Capture
class ScreenshotOutput(BaseModel):
    screenshot_path: str
    screenshot_url: str
    captured_at: datetime = Field(default_factory=datetime.utcnow)

# 2.14 Deck Generation
class DeckGenerationOutput(BaseModel):
    deck_html_path: str
    deck_pdf_path: Optional[str] = None
    deck_url: str
    slides_count: int = 8
    qr_code_url: Optional[str] = None

# 2.15 Narration Generation
class NarrationOutput(BaseModel):
    spoken_script: str
    audio_path: Optional[str] = None
    audio_url: Optional[str] = None
    duration_estimate_seconds: int = 45

# API Request/Response Schemas
class CreateRunRequest(BaseModel):
    idea: str

class RunResponse(BaseModel):
    id: str
    idea: str
    status: str
    current_stage: str
    product_name: Optional[str] = None
    tagline: Optional[str] = None
    preview_url: Optional[str] = None
    deck_path: Optional[str] = None
    narration_path: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="metadata_json")

    class Config:
        from_attributes = True
        populate_by_name = True

class StageEventResponse(BaseModel):
    id: int
    run_id: str
    stage: str
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    input_json: Optional[Dict[str, Any]] = None
    output_json: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    logs: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True

class TimelineResponse(BaseModel):
    run_id: str
    status: str
    total_duration_ms: Optional[float] = None
    stages: List[StageEventResponse] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
