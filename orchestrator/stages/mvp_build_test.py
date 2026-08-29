import asyncio
import logging
from typing import Callable, Optional
from orchestrator.clients.daytona_client import daytona_client
from orchestrator.models import MvpBuildTestOutput, MvpScaffoldOutput

logger = logging.getLogger("founder0.stage.mvp_build_test")

async def run_mvp_build_test(
    scaffold: MvpScaffoldOutput,
    log: Optional[Callable[[str], None]] = None
) -> MvpBuildTestOutput:
    """
    Stage 2.10: MVP_BUILD_AND_TEST
    There is no build step — the vanilla template is plain HTML/CSS/JS run
    directly by Node. This stage syntax-checks the generated server code,
    starts it, and does a real HTTP health check against it.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    emit(f"🔨 [MVP_BUILD_AND_TEST] Verifying generated code in sandbox {scaffold.sandbox_id}...")
    sandbox = await daytona_client.get_sandbox(scaffold.sandbox_id)
    if not sandbox:
        raise RuntimeError(f"Sandbox {scaffold.sandbox_id} not found")

    emit("⚡ [MVP_BUILD_AND_TEST] Running 'node --check server.js' (syntax verification, no build needed)...")
    check_res = await sandbox.execute_command("node --check server.js")

    for line in check_res["stdout"].split("\n"):
        if line.strip():
            emit(f"  [check:node] {line}")

    if check_res["exit_code"] != 0:
        emit(f"❌ [MVP_BUILD_AND_TEST] server.js failed syntax check with exit code {check_res['exit_code']}.")
        if check_res.get("stderr"):
            emit(f"  [check:stderr] {check_res['stderr']}")
        return MvpBuildTestOutput(
            build_exit_code=check_res["exit_code"],
            build_output=check_res["stdout"] + "\n" + check_res.get("stderr", ""),
            test_passed=False
        )

    emit("🚀 [MVP_BUILD_AND_TEST] Syntax OK. Starting server in background and running a real HTTP health check...")

    # Start the server in the background inside the sandbox.
    start_res = await sandbox.execute_command("nohup node server.js > server.log 2>&1 & sleep 1 && echo STARTED")

    if "STARTED" not in start_res.get("stdout", ""):
        emit(f"❌ [MVP_BUILD_AND_TEST] Server did not report a clean start. Output: {start_res['stdout']}")
        return MvpBuildTestOutput(
            build_exit_code=start_res["exit_code"],
            build_output=start_res["stdout"] + "\n" + start_res.get("stderr", ""),
            test_passed=False
        )

    # Real health check — curl from inside the sandbox against the server we
    # just started, not a hardcoded "200 OK" string.
    health_res = await sandbox.execute_command(
        "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/health"
    )
    status_code_str = health_res.get("stdout", "").strip()

    if health_res["exit_code"] == 0 and status_code_str.startswith("2"):
        emit(f"✅ [MVP_BUILD_AND_TEST] Real HTTP GET /health returned status {status_code_str}. Smoke test passed.")
        return MvpBuildTestOutput(
            build_exit_code=0,
            build_output=check_res["stdout"],
            test_passed=True,
            smoke_test_url=sandbox.preview_url,
            smoke_test_status_code=int(status_code_str) if status_code_str.isdigit() else None
        )

    emit(f"❌ [MVP_BUILD_AND_TEST] Health check failed. curl exit={health_res['exit_code']}, status={status_code_str!r}")
    return MvpBuildTestOutput(
        build_exit_code=1,
        build_output=f"Health check failed: exit={health_res['exit_code']} status={status_code_str}",
        test_passed=False
    )
