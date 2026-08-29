import asyncio
from datetime import datetime
import json
import logging
import traceback
from typing import Any, Callable, Dict, List, Optional, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from orchestrator.database import AsyncSessionLocal
from orchestrator.models import (
    Artifact,
    PipelineStage,
    Run,
    StageEvent,
    StageStatus,
)
from orchestrator.stages import (
    run_competitor_enrichment,
    run_deck_generation,
    run_ideation,
    run_market_recon,
    run_mvp_build_test,
    run_mvp_codegen,
    run_mvp_deploy,
    run_mvp_scaffold,
    run_mvp_self_heal,
    run_naming_branding,
    run_narration_generation,
    run_opportunity_graph,
    run_screenshot_capture,
    run_spec_generation,
    run_whitespace_analysis,
)

logger = logging.getLogger("founder0.orchestrator.statemachine")

class WebSocketNotifier:
    """Manages active WebSocket connections subscribed to run updates."""
    def __init__(self):
        self.subscribers: Dict[str, Set[Any]] = {}

    def subscribe(self, run_id: str, websocket: Any):
        if run_id not in self.subscribers:
            self.subscribers[run_id] = set()
        self.subscribers[run_id].add(websocket)

    def unsubscribe(self, run_id: str, websocket: Any):
        if run_id in self.subscribers:
            self.subscribers[run_id].discard(websocket)
            if not self.subscribers[run_id]:
                del self.subscribers[run_id]

    async def broadcast(self, run_id: str, event_type: str, data: Dict[str, Any]):
        if run_id not in self.subscribers:
            return
        payload = json.dumps({"event": event_type, "run_id": run_id, "data": data})
        dead = []
        for ws in self.subscribers[run_id]:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for d in dead:
            self.subscribers[run_id].discard(d)

notifier = WebSocketNotifier()

class PipelineRunner:
    """Coordinates end-to-end execution of the 15-stage FOUNDER-0 state machine."""

    def __init__(self, run_id: str, idea: str):
        self.run_id = run_id
        self.idea = idea

    async def _emit_log(self, stage: str, message: str, stage_logs: List[str]):
        timestamp = datetime.utcnow().strftime("%H:%M:%S.%f")[:-3]
        formatted = f"[{timestamp}] {message}"
        stage_logs.append(formatted)
        await notifier.broadcast(self.run_id, "log", {
            "stage": stage,
            "log": formatted
        })

    async def _record_stage_start(self, session: AsyncSession, stage: str, input_data: Optional[Dict[str, Any]] = None) -> StageEvent:
        event = StageEvent(
            run_id=self.run_id,
            stage=stage,
            status=StageStatus.RUNNING.value,
            started_at=datetime.utcnow(),
            input_json=input_data,
            logs=[]
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)

        # Update run status
        result = await session.execute(select(Run).where(Run.id == self.run_id))
        run_obj = result.scalars().first()
        if run_obj:
            run_obj.current_stage = stage
            run_obj.status = "running"
            await session.commit()

        await notifier.broadcast(self.run_id, "stage_transition", {
            "stage": stage,
            "status": "running"
        })
        return event

    async def _record_stage_success(self, session: AsyncSession, event: StageEvent, output_data: Dict[str, Any], logs: List[str]):
        event.status = StageStatus.SUCCEEDED.value
        event.finished_at = datetime.utcnow()
        event.output_json = output_data
        event.logs = logs
        await session.commit()

        await notifier.broadcast(self.run_id, "stage_transition", {
            "stage": event.stage,
            "status": "succeeded",
            "output": output_data
        })

    async def _record_stage_failure(self, session: AsyncSession, event: StageEvent, error_msg: str, logs: List[str]):
        event.status = StageStatus.FAILED.value
        event.finished_at = datetime.utcnow()
        event.error = error_msg
        event.logs = logs
        await session.commit()

        await notifier.broadcast(self.run_id, "stage_transition", {
            "stage": event.stage,
            "status": "failed",
            "error": error_msg
        })

    async def execute(self):
        """Execute all 15 stages sequentially with structured state tracking."""
        logger.info(f"🚀 Starting FOUNDER-0 run {self.run_id} for idea: '{self.idea}'")

        async with AsyncSessionLocal() as session:
            try:
                # Stage 1: IDEA_RECEIVED
                stage_logs = []
                log_cb = lambda msg: asyncio.create_task(self._emit_log(PipelineStage.IDEA_RECEIVED.value, msg, stage_logs))
                ev = await self._record_stage_start(session, PipelineStage.IDEA_RECEIVED.value, {"idea": self.idea})
                await self._emit_log(PipelineStage.IDEA_RECEIVED.value, f"💡 Idea ingested: '{self.idea}'", stage_logs)
                await self._record_stage_success(session, ev, {"idea": self.idea}, stage_logs)

                # Stage 2: MARKET_RECON
                stage_logs = []
                log_cb = lambda msg: asyncio.create_task(self._emit_log(PipelineStage.MARKET_RECON.value, msg, stage_logs))
                ev = await self._record_stage_start(session, PipelineStage.MARKET_RECON.value, {"idea": self.idea})
                recon_out = await run_market_recon(self.idea, log=log_cb)
                await self._record_stage_success(session, ev, recon_out.model_dump(mode='json'), stage_logs)

                # Stage 3: COMPETITOR_ENRICHMENT
                stage_logs = []
                log_cb = lambda msg: asyncio.create_task(self._emit_log(PipelineStage.COMPETITOR_ENRICHMENT.value, msg, stage_logs))
                ev = await self._record_stage_start(session, PipelineStage.COMPETITOR_ENRICHMENT.value, recon_out.model_dump(mode='json'))
                enrichment_out = await run_competitor_enrichment(recon_out, log=log_cb)
                await self._record_stage_success(session, ev, enrichment_out.model_dump(mode='json'), stage_logs)

                # Stage 4: OPPORTUNITY_GRAPH
                stage_logs = []
                log_cb = lambda msg: asyncio.create_task(self._emit_log(PipelineStage.OPPORTUNITY_GRAPH.value, msg, stage_logs))
                ev = await self._record_stage_start(session, PipelineStage.OPPORTUNITY_GRAPH.value, {"nodes_count": len(enrichment_out.enriched_competitors)})
                graph_out = await run_opportunity_graph(self.idea, recon_out, enrichment_out, log=log_cb)
                await self._record_stage_success(session, ev, graph_out.model_dump(mode='json'), stage_logs)
                # Broadcast graph update for UI visualization
                await notifier.broadcast(self.run_id, "graph_update", graph_out.model_dump(mode='json'))

                # Stage 5: WHITESPACE_ANALYSIS
                stage_logs = []
                log_cb = lambda msg: asyncio.create_task(self._emit_log(PipelineStage.WHITESPACE_ANALYSIS.value, msg, stage_logs))
                ev = await self._record_stage_start(session, PipelineStage.WHITESPACE_ANALYSIS.value, graph_out.model_dump(mode='json'))
                whitespace_out = await run_whitespace_analysis(graph_out, recon_out, log=log_cb)
                await self._record_stage_success(session, ev, whitespace_out.model_dump(mode='json'), stage_logs)

                # Stage 6: IDEATION
                stage_logs = []
                log_cb = lambda msg: asyncio.create_task(self._emit_log(PipelineStage.IDEATION.value, msg, stage_logs))
                ev = await self._record_stage_start(session, PipelineStage.IDEATION.value, whitespace_out.model_dump(mode='json'))
                ideation_out = await run_ideation(self.idea, whitespace_out, log=log_cb)
                await self._record_stage_success(session, ev, ideation_out.model_dump(mode='json'), stage_logs)

                # Stage 7: NAMING_AND_BRANDING
                stage_logs = []
                log_cb = lambda msg: asyncio.create_task(self._emit_log(PipelineStage.NAMING_AND_BRANDING.value, msg, stage_logs))
                ev = await self._record_stage_start(session, PipelineStage.NAMING_AND_BRANDING.value, ideation_out.model_dump(mode='json'))
                branding_out = await run_naming_branding(ideation_out, log=log_cb)
                await self._record_stage_success(session, ev, branding_out.model_dump(mode='json'), stage_logs)

                # Update Run entity with product name and tagline
                run_res = await session.execute(select(Run).where(Run.id == self.run_id))
                r_obj = run_res.scalars().first()
                if r_obj:
                    r_obj.product_name = ideation_out.product_name
                    r_obj.tagline = ideation_out.tagline
                    await session.commit()

                # Stage 8: SPEC_GENERATION
                stage_logs = []
                log_cb = lambda msg: asyncio.create_task(self._emit_log(PipelineStage.SPEC_GENERATION.value, msg, stage_logs))
                ev = await self._record_stage_start(session, PipelineStage.SPEC_GENERATION.value, ideation_out.model_dump(mode='json'))
                spec_out = await run_spec_generation(ideation_out, log=log_cb)
                await self._record_stage_success(session, ev, spec_out.model_dump(mode='json'), stage_logs)

                # Stage 9: MVP_SCAFFOLD
                stage_logs = []
                log_cb = lambda msg: asyncio.create_task(self._emit_log(PipelineStage.MVP_SCAFFOLD.value, msg, stage_logs))
                ev = await self._record_stage_start(session, PipelineStage.MVP_SCAFFOLD.value, spec_out.model_dump(mode='json'))
                scaffold_out = await run_mvp_scaffold(spec_out, log=log_cb)
                await self._record_stage_success(session, ev, scaffold_out.model_dump(mode='json'), stage_logs)

                # Stage 10: MVP_CODE_GENERATION
                stage_logs = []
                log_cb = lambda msg: asyncio.create_task(self._emit_log(PipelineStage.MVP_CODE_GENERATION.value, msg, stage_logs))
                ev = await self._record_stage_start(session, PipelineStage.MVP_CODE_GENERATION.value, {"sandbox_id": scaffold_out.sandbox_id})
                codegen_out = await run_mvp_codegen(scaffold_out, ideation_out, spec_out, log=log_cb)
                await self._record_stage_success(session, ev, codegen_out.model_dump(mode='json'), stage_logs)

                # Stage 11: MVP_BUILD_AND_TEST
                stage_logs = []
                log_cb = lambda msg: asyncio.create_task(self._emit_log(PipelineStage.MVP_BUILD_AND_TEST.value, msg, stage_logs))
                ev = await self._record_stage_start(session, PipelineStage.MVP_BUILD_AND_TEST.value, {"sandbox_id": scaffold_out.sandbox_id})
                build_out = await run_mvp_build_test(scaffold_out, log=log_cb)
                await self._record_stage_success(session, ev, build_out.model_dump(mode='json'), stage_logs)

                # Stage 12: MVP_SELF_HEAL_LOOP
                stage_logs = []
                log_cb = lambda msg: asyncio.create_task(self._emit_log(PipelineStage.MVP_SELF_HEAL_LOOP.value, msg, stage_logs))
                ev = await self._record_stage_start(session, PipelineStage.MVP_SELF_HEAL_LOOP.value, {"test_passed": build_out.test_passed})
                heal_out = await run_mvp_self_heal(scaffold_out, codegen_out, build_out, log=log_cb)
                await self._record_stage_success(session, ev, heal_out.model_dump(mode='json'), stage_logs)

                # Stage 13: MVP_DEPLOY_PREVIEW
                stage_logs = []
                log_cb = lambda msg: asyncio.create_task(self._emit_log(PipelineStage.MVP_DEPLOY_PREVIEW.value, msg, stage_logs))
                ev = await self._record_stage_start(session, PipelineStage.MVP_DEPLOY_PREVIEW.value, {"sandbox_id": scaffold_out.sandbox_id})
                deploy_out = await run_mvp_deploy(scaffold_out, heal_out, log=log_cb)
                await self._record_stage_success(session, ev, deploy_out.model_dump(mode='json'), stage_logs)

                # Update Run preview URL
                r_res = await session.execute(select(Run).where(Run.id == self.run_id))
                r_obj = r_res.scalars().first()
                if r_obj:
                    r_obj.preview_url = deploy_out.preview_url
                    await session.commit()

                # Stage 14: SCREENSHOT_CAPTURE
                stage_logs = []
                log_cb = lambda msg: asyncio.create_task(self._emit_log(PipelineStage.SCREENSHOT_CAPTURE.value, msg, stage_logs))
                ev = await self._record_stage_start(session, PipelineStage.SCREENSHOT_CAPTURE.value, deploy_out.model_dump(mode='json'))
                screenshot_out = await run_screenshot_capture(self.run_id, deploy_out, ideation_out, log=log_cb)
                await self._record_stage_success(session, ev, screenshot_out.model_dump(mode='json'), stage_logs)

                # Stage 15: DECK_GENERATION
                stage_logs = []
                log_cb = lambda msg: asyncio.create_task(self._emit_log(PipelineStage.DECK_GENERATION.value, msg, stage_logs))
                ev = await self._record_stage_start(session, PipelineStage.DECK_GENERATION.value, {"deck": True})
                deck_out = await run_deck_generation(self.run_id, ideation_out, recon_out, whitespace_out, graph_out, deploy_out, screenshot_out, log=log_cb)
                await self._record_stage_success(session, ev, deck_out.model_dump(mode='json'), stage_logs)

                # Update Run deck path
                r_res = await session.execute(select(Run).where(Run.id == self.run_id))
                r_obj = r_res.scalars().first()
                if r_obj:
                    r_obj.deck_path = deck_out.deck_url
                    await session.commit()

                # Stage 16: NARRATION_GENERATION
                stage_logs = []
                log_cb = lambda msg: asyncio.create_task(self._emit_log(PipelineStage.NARRATION_GENERATION.value, msg, stage_logs))
                ev = await self._record_stage_start(session, PipelineStage.NARRATION_GENERATION.value, {"deck_url": deck_out.deck_url})
                narration_out = await run_narration_generation(self.run_id, ideation_out, deck_out, log=log_cb)
                await self._record_stage_success(session, ev, narration_out.model_dump(mode='json'), stage_logs)

                # Finalize COMPLETE State
                r_res = await session.execute(select(Run).where(Run.id == self.run_id))
                r_obj = r_res.scalars().first()
                if r_obj:
                    r_obj.status = "completed"
                    r_obj.current_stage = PipelineStage.COMPLETE.value
                    r_obj.finished_at = datetime.utcnow()
                    r_obj.narration_path = narration_out.spoken_script
                    await session.commit()

                await notifier.broadcast(self.run_id, "run_completed", {
                    "status": "completed",
                    "preview_url": deploy_out.preview_url,
                    "deck_url": deck_out.deck_url,
                    "product_name": ideation_out.product_name
                })

                logger.info(f"🏆 Pipeline Run {self.run_id} completed successfully!")

            except Exception as e:
                err_str = f"{str(e)}\n{traceback.format_exc()}"
                logger.error(f"Pipeline Run {self.run_id} encountered fatal error: {err_str}")
                r_res = await session.execute(select(Run).where(Run.id == self.run_id))
                r_obj = r_res.scalars().first()
                if r_obj:
                    r_obj.status = "failed"
                    r_obj.current_stage = PipelineStage.FAILED.value
                    r_obj.finished_at = datetime.utcnow()
                    await session.commit()

                await notifier.broadcast(self.run_id, "run_failed", {
                    "status": "failed",
                    "error": str(e)
                })
