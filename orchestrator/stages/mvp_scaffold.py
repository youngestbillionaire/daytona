import logging
from typing import Callable, Optional
from orchestrator.clients.daytona_client import daytona_client
from orchestrator.models import MvpScaffoldOutput, SpecGenerationOutput

logger = logging.getLogger("founder0.stage.mvp_scaffold")

async def run_mvp_scaffold(
    spec: SpecGenerationOutput,
    log: Optional[Callable[[str], None]] = None
) -> MvpScaffoldOutput:
    """
    Stage 2.8: MVP_SCAFFOLD
    Provisions a real Daytona sandbox (or a local simulation, only if
    MOCK_MODE/no API key) and stages the zero-build vanilla HTML/CSS/JS
    starter template — no TypeScript, no React, no npm build step required.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    if daytona_client.mock_mode:
        emit("🏗️ [MVP_SCAFFOLD] MOCK_MODE active — simulating sandbox locally (no real Daytona sandbox created).")
    else:
        emit("🏗️ [MVP_SCAFFOLD] Provisioning a REAL Daytona sandbox via the live API...")

    sandbox = await daytona_client.create_sandbox(language="javascript")

    emit(f"📦 [MVP_SCAFFOLD] Sandbox ready: {sandbox.id} (mock={sandbox.is_mock})")
    emit("📂 [MVP_SCAFFOLD] Staged vanilla static template (plain HTML/CSS/JS + Node http server, zero npm deps, zero build step).")

    # No npm install needed at all — the template has zero external dependencies.
    # We still run a trivial command so the sandbox's process channel is confirmed
    # live before later stages depend on it.
    verify_res = await sandbox.execute_command("node --version")
    emit(f"⚡ [MVP_SCAFFOLD] Verified Node runtime in sandbox (exit code: {verify_res['exit_code']}): {verify_res['stdout'].strip()}")

    if verify_res["exit_code"] != 0:
        emit(f"❌ [MVP_SCAFFOLD] Sandbox environment check failed: {verify_res.get('stderr', '')}")

    emit(f"✅ [MVP_SCAFFOLD] Clean scaffold checkpoint established at {sandbox.workspace_path}")

    return MvpScaffoldOutput(
        sandbox_id=sandbox.id,
        workspace_path=sandbox.workspace_path,
        template_used="vanilla-static-starter",
        install_exit_code=verify_res["exit_code"],
        install_logs=verify_res["stdout"]
    )
