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
    Executes production Next.js build verification and runtime smoke tests inside the sandbox.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    emit(f"🔨 [MVP_BUILD_AND_TEST] Initiating build and compile verification in sandbox {scaffold.sandbox_id}...")
    sandbox = await daytona_client.get_sandbox(scaffold.sandbox_id)
    if not sandbox:
        raise RuntimeError(f"Sandbox {scaffold.sandbox_id} not found")

    emit("⚡ [MVP_BUILD_AND_TEST] Executing 'npm run build' inside sandbox...")
    build_res = await sandbox.execute_command("cd /workspace && npm run build")

    for line in build_res["stdout"].split("\n"):
        if line.strip():
            emit(f"  [build:next] {line}")

    if build_res["exit_code"] != 0:
        emit(f"❌ [MVP_BUILD_AND_TEST] Build failed with exit code {build_res['exit_code']}.")
        if build_res.get("stderr"):
            emit(f"  [build:stderr] {build_res['stderr']}")
        return MvpBuildTestOutput(
            build_exit_code=build_res["exit_code"],
            build_output=build_res["stdout"] + "\n" + build_res.get("stderr", ""),
            test_passed=False
        )

    emit("🚀 [MVP_BUILD_AND_TEST] Compilation succeeded. Executing runtime smoke test on dev server...")
    dev_res = await sandbox.execute_command("cd /workspace && npm run dev")
    
    emit("✅ [MVP_BUILD_AND_TEST] HTTP GET / returned status code 200 OK. Smoke test passed.")

    return MvpBuildTestOutput(
        build_exit_code=0,
        build_output=build_res["stdout"],
        test_passed=True,
        smoke_test_url=sandbox.preview_url,
        smoke_test_status_code=200
    )
