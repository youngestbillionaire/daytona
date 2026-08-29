import asyncio
import logging
from typing import Callable, Optional
from orchestrator.clients.daytona_client import daytona_client
from orchestrator.config import settings
from orchestrator.models import MvpDeployOutput, MvpScaffoldOutput, MvpSelfHealOutput

logger = logging.getLogger("founder0.stage.mvp_deploy")

async def run_mvp_deploy(
    scaffold: MvpScaffoldOutput,
    self_heal: MvpSelfHealOutput,
    log: Optional[Callable[[str], None]] = None
) -> MvpDeployOutput:
    """
    Stage 2.12: MVP_DEPLOY_PREVIEW
    Exposes the sandbox server via Daytona's real preview URL mechanism and
    polls it with real HTTP requests until it's actually reachable, rather
    than sleeping briefly and unconditionally reporting success.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    emit(f"🌐 [MVP_DEPLOY_PREVIEW] Resolving public preview URL for sandbox {scaffold.sandbox_id}...")
    sandbox = await daytona_client.get_sandbox(scaffold.sandbox_id)
    if not sandbox:
        raise RuntimeError(f"Sandbox {scaffold.sandbox_id} not found")

    preview_url = sandbox.preview_url
    emit(f"📡 [MVP_DEPLOY_PREVIEW] Preview URL: {preview_url}")
    emit("🩺 [MVP_DEPLOY_PREVIEW] Polling health check endpoint with real HTTP requests...")

    health_check_passed = False
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        res = await sandbox.execute_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/health")
        status = res.get("stdout", "").strip()
        if res["exit_code"] == 0 and status.startswith("2"):
            health_check_passed = True
            emit(f"✅ [MVP_DEPLOY_PREVIEW] Health check passed on attempt {attempt}/{max_attempts} (HTTP {status}).")
            break
        emit(f"⏳ [MVP_DEPLOY_PREVIEW] Attempt {attempt}/{max_attempts}: not ready yet (exit={res['exit_code']}, status={status!r}). Retrying...")
        await asyncio.sleep(1.5)

    if not health_check_passed:
        emit("❌ [MVP_DEPLOY_PREVIEW] Server never became reachable after retries. MVP is NOT confirmed live.")

    return MvpDeployOutput(
        preview_url=preview_url,
        port=3000,
        health_check_passed=health_check_passed,
        sandbox_status="running" if health_check_passed else "unreachable"
    )
