import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from orchestrator.database import AsyncSessionLocal, init_db
from orchestrator.main import app
from orchestrator.models import Run, PipelineStage

@pytest.mark.asyncio
async def test_api_create_and_list_runs():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create run
        idea = "an AI accountant that saves freelancers $5000 a year"
        res = await client.post("/api/runs", json={"idea": idea})
        assert res.status_code == 200
        data = res.json()
        assert data["id"].startswith("run_")
        assert data["idea"] == idea
        assert data["status"] == "running"
        run_id = data["id"]

        # 2. List runs
        list_res = await client.get("/api/runs")
        assert list_res.status_code == 200
        runs = list_res.json()
        assert any(r["id"] == run_id for r in runs)

        # 3. Get single run
        get_res = await client.get(f"/api/runs/{run_id}")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == run_id

        # 4. Get run timeline
        timeline_res = await client.get(f"/api/runs/{run_id}/timeline")
        assert timeline_res.status_code == 200
        t_data = timeline_res.json()
        assert t_data["run_id"] == run_id
        assert "stages" in t_data

        # 5. Get graph
        graph_res = await client.get(f"/api/runs/{run_id}/graph")
        assert graph_res.status_code == 200

        # 6. Replay run
        replay_res = await client.post(f"/api/runs/{run_id}/replay")
        assert replay_res.status_code == 200
        replayed_data = replay_res.json()
        assert replayed_data["id"] != run_id
        assert replayed_data["idea"] == idea

@pytest.mark.asyncio
async def test_api_404_handling():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/runs/non_existent_run_id_999")
        assert res.status_code == 404

        res_timeline = await client.get("/api/runs/non_existent_run_id_999/timeline")
        assert res_timeline.status_code == 404

@pytest.mark.asyncio
async def test_api_sandbox_preview():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/preview/sbx_test_preview_123")
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]
        assert "FOUNDER-0" in res.text
