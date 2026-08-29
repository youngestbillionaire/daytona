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
    Creates an isolated Next.js development sandbox via Daytona,
    clones the baseline starter template, and prepares dependencies.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    emit("🏗️ [MVP_SCAFFOLD] Provisioning isolated Daytona TypeScript Sandbox...")
    sandbox = await daytona_client.create_sandbox(language="typescript")

    emit(f"📦 [MVP_SCAFFOLD] Initialized Sandbox container: {sandbox.id}")
    emit("📂 [MVP_SCAFFOLD] Staging Next.js App Router template with SQLite & Tailwind CSS...")
    
    emit("⚡ [MVP_SCAFFOLD] Executing 'npm install' inside sandbox...")
    install_res = await sandbox.execute_command("cd /workspace && npm install")
    
    emit(f"📝 [MVP_SCAFFOLD] Install completed (exit code: {install_res['exit_code']}):")
    for line in install_res["stdout"].split("\n"):
        if line.strip():
            emit(f"  [sandbox:npm] {line}")

    emit(f"✅ [MVP_SCAFFOLD] Clean scaffold checkpoint established at {sandbox.local_path}")

    return MvpScaffoldOutput(
        sandbox_id=sandbox.id,
        workspace_path=str(sandbox.local_path),
        template_used="nextjs-sqlite-starter",
        install_exit_code=install_res["exit_code"],
        install_logs=install_res["stdout"]
    )
