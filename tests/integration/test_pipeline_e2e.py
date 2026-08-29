import asyncio
import uuid
import pytest
from sqlalchemy import select
from orchestrator.database import AsyncSessionLocal, init_db
from orchestrator.models import PipelineStage, Run, StageEvent
from orchestrator.state_machine import PipelineRunner

@pytest.mark.asyncio
async def test_full_pipeline_e2e():
    """Integration test running all 15 stages end-to-end via PipelineRunner."""
    await init_db()
    
    test_run_id = f"test_e2e_{uuid.uuid4().hex[:8]}"
    idea = "an app for splitting bills with roommates who hate each other"

    # Pre-create run record
    async with AsyncSessionLocal() as session:
        run_obj = Run(
            id=test_run_id,
            idea=idea,
            status="running",
            current_stage=PipelineStage.IDEA_RECEIVED.value
        )
        session.add(run_obj)
        await session.commit()

    runner = PipelineRunner(run_id=test_run_id, idea=idea)
    await runner.execute()

    # Verify final database state
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Run).where(Run.id == test_run_id))
        completed_run = result.scalars().first()
        
        assert completed_run is not None
        assert completed_run.status == "completed"
        assert completed_run.current_stage == PipelineStage.COMPLETE.value
        assert completed_run.product_name is not None and len(completed_run.product_name) > 0
        assert completed_run.preview_url is not None and "http" in completed_run.preview_url
        assert completed_run.deck_path is not None and "decks" in completed_run.deck_path

        events_res = await session.execute(
            select(StageEvent).where(StageEvent.run_id == test_run_id)
        )
        events = events_res.scalars().all()
        assert len(events) >= 15
        for ev in events:
            assert ev.status == "succeeded"
