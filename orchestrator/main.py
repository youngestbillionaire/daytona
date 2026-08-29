import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
import json
import os
from pathlib import Path
import uuid
from typing import Any, Dict, List, Optional
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from orchestrator.config import settings
from orchestrator.database import get_db, init_db
from orchestrator.models import (
    Artifact,
    CreateRunRequest,
    Run,
    RunResponse,
    StageEvent,
    StageEventResponse,
    TimelineResponse,
)
from orchestrator.state_machine import PipelineRunner, notifier

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and artifacts folders
    await init_db()
    Path("artifacts").mkdir(parents=True, exist_ok=True)
    Path("artifacts/decks").mkdir(parents=True, exist_ok=True)
    Path("artifacts/screenshots").mkdir(parents=True, exist_ok=True)
    Path("artifacts/sandboxes").mkdir(parents=True, exist_ok=True)
    Path("artifacts/narrations").mkdir(parents=True, exist_ok=True)
    yield

app = FastAPI(
    title="FOUNDER-0 Autonomous Startup Engine",
    description="Transforms a 1-sentence startup idea into validated market research, knowledge graph, live running MVP, and pitch deck.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated artifacts statically
if not os.path.exists("artifacts"):
    os.makedirs("artifacts", exist_ok=True)
app.mount("/api/artifacts", StaticFiles(directory="artifacts"), name="artifacts")

# ==========================================
# REST API Endpoints
# ==========================================

@app.post("/api/runs", response_model=RunResponse)
async def create_run(request: CreateRunRequest, db: AsyncSession = Depends(get_db)):
    """Create a new autonomous startup generation run and launch execution."""
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    run_obj = Run(
        id=run_id,
        idea=request.idea.strip(),
        status="running",
        current_stage="IDEA_RECEIVED",
        started_at=datetime.utcnow()
    )
    db.add(run_obj)
    await db.commit()
    await db.refresh(run_obj)

    # Launch state machine in background task
    runner = PipelineRunner(run_id=run_id, idea=request.idea.strip())
    asyncio.create_task(runner.execute())

    return RunResponse.model_validate(run_obj)

@app.get("/api/runs", response_model=List[RunResponse])
async def list_runs(db: AsyncSession = Depends(get_db)):
    """List all previous and ongoing runs ordered by date."""
    result = await db.execute(select(Run).order_by(desc(Run.started_at)))
    runs = result.scalars().all()
    return [RunResponse.model_validate(r) for r in runs]

@app.get("/api/runs/{run_id}", response_model=RunResponse)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch details and artifacts for a specific run."""
    result = await db.execute(select(Run).where(Run.id == run_id))
    run_obj = result.scalars().first()
    if not run_obj:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunResponse.model_validate(run_obj)

@app.get("/api/runs/{run_id}/timeline", response_model=TimelineResponse)
async def get_run_timeline(run_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch structured stage_events timeline with log arrays and duration calculation."""
    run_res = await db.execute(select(Run).where(Run.id == run_id))
    run_obj = run_res.scalars().first()
    if not run_obj:
        raise HTTPException(status_code=404, detail="Run not found")

    events_res = await db.execute(
        select(StageEvent).where(StageEvent.run_id == run_id).order_by(StageEvent.id)
    )
    events = events_res.scalars().all()

    total_duration_ms = None
    if run_obj.finished_at and run_obj.started_at:
        total_duration_ms = (run_obj.finished_at - run_obj.started_at).total_seconds() * 1000

    return TimelineResponse(
        run_id=run_id,
        status=run_obj.status,
        total_duration_ms=total_duration_ms,
        stages=[StageEventResponse.model_validate(e) for e in events],
        metadata={
            "product_name": run_obj.product_name,
            "preview_url": run_obj.preview_url,
            "deck_path": run_obj.deck_path
        }
    )

@app.get("/api/runs/{run_id}/graph")
async def get_run_graph(run_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve Neo4j knowledge graph data for this run."""
    event_res = await db.execute(
        select(StageEvent).where(StageEvent.run_id == run_id, StageEvent.stage == "OPPORTUNITY_GRAPH")
    )
    event = event_res.scalars().first()
    if event and event.output_json:
        return event.output_json
    return {"nodes": [], "edges": [], "node_count": 0, "edge_count": 0}

@app.post("/api/runs/{run_id}/replay", response_model=RunResponse)
async def replay_run(run_id: str, db: AsyncSession = Depends(get_db)):
    """Replay an existing run with the same prompt from scratch."""
    result = await db.execute(select(Run).where(Run.id == run_id))
    run_obj = result.scalars().first()
    if not run_obj:
        raise HTTPException(status_code=404, detail="Run not found")

    new_run_id = f"run_{uuid.uuid4().hex[:12]}"
    new_run = Run(
        id=new_run_id,
        idea=run_obj.idea,
        status="running",
        current_stage="IDEA_RECEIVED",
        started_at=datetime.utcnow()
    )
    db.add(new_run)
    await db.commit()
    await db.refresh(new_run)

    runner = PipelineRunner(run_id=new_run_id, idea=run_obj.idea)
    asyncio.create_task(runner.execute())

    return RunResponse.model_validate(new_run)

@app.get("/api/preview/{sandbox_id}", response_class=HTMLResponse)
async def preview_sandbox(sandbox_id: str):
    """
    Serves the REAL generated MVP for a sandbox: reads public/index.html out of
    that sandbox's local mirror directory (artifacts/sandboxes/{id}/public/)
    and returns it as-is, with a <base> tag injected so its relative asset
    links (style.css, app.js) resolve correctly under this proxy path.

    This only serves what the pipeline actually generated. If the sandbox
    hasn't produced an index.html yet (pipeline still running, or it's a
    live Daytona sandbox whose real preview URL bypasses this route
    entirely), it returns an honest "not ready" page instead of fake content.
    """
    index_path = Path("artifacts") / "sandboxes" / sandbox_id / "public" / "index.html"

    if not index_path.exists():
        return HTMLResponse(
            "<html><body style='font-family: sans-serif; padding: 3rem; "
            "background:#0b0f19; color:#e5e7eb;'>"
            "<h2>MVP not generated yet</h2>"
            "<p>This sandbox has no generated <code>public/index.html</code> on disk yet. "
            "Either the pipeline hasn't reached MVP_CODE_GENERATION for this run, "
            "or this sandbox is a live Daytona sandbox whose real preview URL "
            "should be used instead of this local proxy.</p>"
            "</body></html>",
            status_code=404
        )

    html = index_path.read_text(encoding="utf-8")
    base_tag = f'<base href="/api/preview/{sandbox_id}/">'
    if "<head>" in html:
        html = html.replace("<head>", f"<head>\n  {base_tag}", 1)
    else:
        html = base_tag + html

    return HTMLResponse(html)


@app.get("/api/preview/{sandbox_id}/{file_path:path}")
async def preview_sandbox_asset(sandbox_id: str, file_path: str):
    """Serves a real static asset (style.css, app.js, etc.) generated for this sandbox."""
    base_dir = (Path("artifacts") / "sandboxes" / sandbox_id / "public").resolve()
    target = (base_dir / file_path).resolve()

    if not str(target).startswith(str(base_dir)):
        raise HTTPException(status_code=403, detail="Forbidden")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")

    return FileResponse(target)


# ==========================================
# WebSocket Streaming
# ==========================================

@app.websocket("/ws/runs/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: str):
    """WebSocket stream for real-time stage transitions, log lines, and graph updates."""
    await websocket.accept()
    notifier.subscribe(run_id, websocket)
    try:
        while True:
            # Keep-alive loop
            await websocket.receive_text()
    except WebSocketDisconnect:
        notifier.unsubscribe(run_id, websocket)
    except Exception:
        notifier.unsubscribe(run_id, websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("orchestrator.main:app", host=settings.HOST, port=settings.PORT, reload=True)
