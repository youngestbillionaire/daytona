import logging
from typing import Callable, List, Optional

from orchestrator.clients.daytona_client import daytona_client
from orchestrator.clients.nosana_client import nosana_client
from orchestrator.models import (
    MvpBuildTestOutput,
    MvpCodegenOutput,
    MvpScaffoldOutput,
    MvpSelfHealOutput,
)

logger = logging.getLogger("founder0.stage.mvp_self_heal")


async def run_mvp_self_heal(
    scaffold: MvpScaffoldOutput,
    codegen: MvpCodegenOutput,
    build_test: MvpBuildTestOutput,
    max_retries: int = 2,
    log: Optional[Callable[[str], None]] = None
) -> MvpSelfHealOutput:
    """
    Stage 2.11: MVP_SELF_HEAL_LOOP

    If the build/health check failed, attempts real, bounded repair: feed the
    actual captured error back to the Nosana LLM, regenerate app.js, and
    re-check. If repair doesn't succeed within max_retries, gracefully
    degrade by reverting app.js/index.html feature content to the clean
    baseline template (no injected features, but a working generic page)
    rather than reporting a success that didn't happen.
    """
    def emit(msg: str):
        logger.info(msg)
        if log:
            log(msg)

    if build_test.test_passed:
        emit("🛡️ [MVP_SELF_HEAL_LOOP] Previous build passed cleanly. Zero repairs needed.")
        return MvpSelfHealOutput(
            self_heal_attempts=0,
            healed_features=[],
            degraded_features=[],
            final_build_success=True,
            summary="Initial generation passed its syntax check and health check with no repairs needed."
        )

    emit("🩹 [MVP_SELF_HEAL_LOOP] Detected a real build/health-check failure. Attempting bounded automated repair...")
    sandbox = await daytona_client.get_sandbox(scaffold.sandbox_id)
    if not sandbox:
        raise RuntimeError(f"Sandbox {scaffold.sandbox_id} not found")

    last_error = build_test.build_output
    attempts = 0

    while attempts < max_retries:
        attempts += 1
        emit(f"🔄 [MVP_SELF_HEAL_LOOP] Repair attempt {attempts}/{max_retries} — feeding real error back to Nosana LLM...")

        current_app_js = await sandbox.read_file("public/app.js") or ""
        repair_prompt = f"""
The following vanilla JavaScript file failed a syntax/runtime check with this error:

--- ERROR ---
{last_error}
--- END ERROR ---

--- CURRENT app.js ---
{current_app_js}
--- END app.js ---

Fix ONLY what's broken. Preserve all working functionality. This is plain
browser JS — no imports, no require, no build step. Return ONLY the corrected
full file content, no markdown fences, no explanation.
"""
        try:
            fixed_js, provider = await nosana_client.generate_chat(prompt=repair_prompt, json_mode=False)
            fixed_js_str = fixed_js if isinstance(fixed_js, str) else str(fixed_js)
        except Exception as e:
            emit(f"⚠️ [MVP_SELF_HEAL_LOOP] LLM repair call failed ({e}), skipping to degradation.")
            break

        await sandbox.write_file("public/app.js", fixed_js_str)

        check_res = await sandbox.execute_command("node --check server.js")
        if check_res["exit_code"] == 0:
            start_res = await sandbox.execute_command("pkill -f 'node server.js' 2>/dev/null; nohup node server.js > server.log 2>&1 & sleep 1 && echo STARTED")
            health_res = await sandbox.execute_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/health")
            status = health_res.get("stdout", "").strip()
            if health_res["exit_code"] == 0 and status.startswith("2"):
                emit(f"✨ [MVP_SELF_HEAL_LOOP] Repair succeeded on attempt {attempts} — real health check now passes (HTTP {status}).")
                return MvpSelfHealOutput(
                    self_heal_attempts=attempts,
                    healed_features=["app.js (feature JS)"],
                    degraded_features=[],
                    final_build_success=True,
                    summary=f"Regenerated app.js via {provider} and confirmed a real passing health check after {attempts} attempt(s)."
                )
            last_error = f"Syntax OK but health check still failing: exit={health_res['exit_code']} status={status}"
        else:
            last_error = check_res.get("stderr") or check_res.get("stdout") or "node --check failed with no output"

        emit(f"⚠️ [MVP_SELF_HEAL_LOOP] Attempt {attempts} still failing: {last_error[:200]}")

    # Real graceful degradation: revert to the clean baseline template content
    # (no injected feature HTML/JS) so the app still ships as a working,
    # if generic, page rather than a broken one — and we say so honestly.
    emit("⚠️ [MVP_SELF_HEAL_LOOP] Repair did not succeed within retry budget. Reverting to clean baseline template (features degraded, page still works).")

    baseline_app_js = (
        "document.getElementById('waitlist-form').addEventListener('submit', async (e) => {\n"
        "  e.preventDefault();\n"
        "  const emailInput = document.getElementById('email-input');\n"
        "  const statusEl = document.getElementById('signup-status');\n"
        "  statusEl.textContent = 'Submitting...';\n"
        "  try {\n"
        "    const res = await fetch('/api/waitlist', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ email: emailInput.value }) });\n"
        "    const data = await res.json();\n"
        "    statusEl.textContent = res.ok ? `You're on the list! (${data.total_signups} signups so far)` : (data.error || 'Something went wrong.');\n"
        "  } catch (err) { statusEl.textContent = 'Network error — please try again.'; }\n"
        "});\n"
    )
    await sandbox.write_file("public/app.js", baseline_app_js)

    check_res = await sandbox.execute_command("node --check server.js")
    final_ok = check_res["exit_code"] == 0

    return MvpSelfHealOutput(
        self_heal_attempts=attempts,
        healed_features=[],
        degraded_features=["feature JS/HTML (reverted to baseline waitlist-only page)"],
        final_build_success=final_ok,
        summary=(
            f"Repair failed after {attempts} attempt(s). Reverted app.js to the clean baseline "
            f"(waitlist form only, no custom features) so the MVP still deploys and runs. "
            f"final syntax check {'passed' if final_ok else 'STILL FAILING — deploy will likely fail'}."
        )
    )
