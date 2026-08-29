import asyncio
import logging
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from orchestrator.config import settings

logger = logging.getLogger("founder0.daytona")

try:
    from daytona import AsyncDaytona, DaytonaConfig, CreateSandboxBaseParams
    _DAYTONA_SDK_AVAILABLE = True
except ImportError:
    _DAYTONA_SDK_AVAILABLE = False
    logger.warning(
        "daytona SDK not installed (`pip install daytona`). "
        "Live Daytona execution is unavailable; only MOCK_MODE will work."
    )


class DaytonaSandbox:
    """
    Wraps either:
      - a real `daytona.AsyncSandbox` (live mode), or
      - a local directory simulation (MOCK_MODE / no API key).

    IMPORTANT: in live mode, this NEVER fabricates a success result. If the
    real Daytona API call fails, the exception/non-zero exit code propagates
    to the caller so the pipeline's actual self-heal / failure-handling logic
    runs on a REAL failure, not a fake one.
    """

    def __init__(self, sandbox_id: str, is_mock: bool, local_path: Path, real_sandbox: Optional[Any] = None):
        self.id = sandbox_id
        self.sandbox_id = sandbox_id
        self.is_mock = is_mock
        self.local_path = local_path
        self.workspace_path = str(local_path)
        self._real_sandbox = real_sandbox  # daytona.AsyncSandbox instance, or None if mock
        self.is_running = False

    @property
    def preview_url(self) -> str:
        if not self.is_mock and self._real_sandbox is not None:
            try:
                link = self._real_sandbox.get_preview_link(3000)
                return link.url if hasattr(link, "url") else str(link)
            except Exception as e:
                logger.warning(f"Could not fetch real Daytona preview URL yet: {e}")
        return f"http://localhost:{settings.PORT}/api/preview/{self.sandbox_id}"

    async def write_file(self, relative_path: str, content: str):
        if self.is_mock or self._real_sandbox is None:
            target_file = self.local_path / relative_path
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(content)
            return

        # Live: write to the real sandbox filesystem via the SDK, AND mirror
        # locally so artifacts/ still has a copy for the deck/report stages.
        await self._real_sandbox.fs.upload_file(content.encode("utf-8"), relative_path)
        target_file = self.local_path / relative_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)

    async def read_file(self, relative_path: str) -> Optional[str]:
        target_file = self.local_path / relative_path
        if target_file.exists():
            with open(target_file, "r", encoding="utf-8") as f:
                return f.read()
        return None

    async def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Execute a command. In live mode this calls the REAL Daytona sandbox
        process API and returns its REAL exit code/output — a failing build
        or a broken script comes back as exit_code != 0, not a faked 0.
        """
        if self.is_mock or self._real_sandbox is None:
            await asyncio.sleep(0.3)
            if "node --version" in command:
                return {"exit_code": 0, "stdout": "v20.11.1", "stderr": ""}
            if "node --check" in command:
                return {"exit_code": 0, "stdout": "", "stderr": ""}
            if "nohup node server.js" in command:
                self.is_running = True
                return {"exit_code": 0, "stdout": "STARTED", "stderr": ""}
            if "pkill" in command and "nohup node server.js" in command:
                self.is_running = True
                return {"exit_code": 0, "stdout": "STARTED", "stderr": ""}
            if "curl" in command and "/health" in command:
                return {"exit_code": 0, "stdout": "200", "stderr": ""}
            return {"exit_code": 0, "stdout": f"[MOCK] Command executed: {command}", "stderr": ""}

        response = await self._real_sandbox.process.exec(command, timeout=120)
        self.is_running = True
        return {
            "exit_code": response.exit_code,
            "stdout": response.result,
            "stderr": "" if response.exit_code == 0 else response.result,
        }

    async def exec_command(self, command: str):
        res = await self.execute_command(command)

        class ExecResult:
            def __init__(self, code, out, err):
                self.exit_code = code
                self.stdout = out
                self.stderr = err

            def __getitem__(self, item):
                return getattr(self, item)

        return ExecResult(res["exit_code"], res["stdout"], res["stderr"])


class DaytonaClient:
    """
    Daytona Sandbox client. Uses the real `daytona` Python SDK when
    DAYTONA_API_KEY is set and MOCK_MODE=false. Falls back to a local
    directory simulation only in MOCK_MODE or when the SDK/key is absent —
    that fallback is explicit and logged, never silent.
    """

    def __init__(self):
        self.api_key = settings.DAYTONA_API_KEY
        self.api_url = settings.DAYTONA_API_URL
        self.target = settings.DAYTONA_TARGET
        self.mock_mode = settings.MOCK_MODE or not self.api_key or not _DAYTONA_SDK_AVAILABLE
        self.sandboxes: Dict[str, DaytonaSandbox] = {}
        self.templates_dir = Path(__file__).resolve().parent.parent.parent / "templates" / "vanilla-static-starter"
        self._async_client = None

        if self.mock_mode:
            reason = (
                "MOCK_MODE=true" if settings.MOCK_MODE else
                "no DAYTONA_API_KEY set" if not self.api_key else
                "daytona SDK not installed"
            )
            logger.warning(f"DaytonaClient running in LOCAL SIMULATION mode ({reason}). No real sandboxes will be created.")
        else:
            logger.info(f"DaytonaClient running LIVE against {self.api_url}.")

    def _get_client(self):
        if self._async_client is None:
            self._async_client = AsyncDaytona(DaytonaConfig(api_key=self.api_key, api_url=self.api_url, target=self.target))
        return self._async_client

    async def create_sandbox(self, language: str = "javascript") -> DaytonaSandbox:
        """
        Create a sandbox. In live mode this makes a REAL call to Daytona's
        API and returns a sandbox backed by a REAL remote container — if
        that call fails, the exception propagates (it is NOT swallowed into
        a fake success), so the pipeline's own retry/self-heal logic is what
        handles it, using real information.
        """
        if self.mock_mode:
            sandbox_id = f"sbx_mock_{uuid.uuid4().hex[:12]}"
            local_dir = Path("artifacts") / "sandboxes" / sandbox_id
            local_dir.mkdir(parents=True, exist_ok=True)
            self._copy_template(local_dir)
            sandbox = DaytonaSandbox(sandbox_id=sandbox_id, is_mock=True, local_path=local_dir)
            self.sandboxes[sandbox_id] = sandbox
            return sandbox

        client = self._get_client()
        real_sandbox = await client.create(
            CreateSandboxBaseParams(language=language),
            timeout=90,
        )
        sandbox_id = real_sandbox.id
        local_dir = Path("artifacts") / "sandboxes" / sandbox_id
        local_dir.mkdir(parents=True, exist_ok=True)
        self._copy_template(local_dir)

        # Push the template into the real sandbox too, not just locally.
        for item in local_dir.rglob("*"):
            if item.is_file():
                rel_path = str(item.relative_to(local_dir))
                await real_sandbox.fs.upload_file(item.read_bytes(), rel_path)

        sandbox = DaytonaSandbox(sandbox_id=sandbox_id, is_mock=False, local_path=local_dir, real_sandbox=real_sandbox)
        self.sandboxes[sandbox_id] = sandbox
        logger.info(f"Created REAL Daytona sandbox: {sandbox_id}")
        return sandbox

    def _copy_template(self, local_dir: Path):
        if self.templates_dir.exists():
            for item in self.templates_dir.rglob("*"):
                if item.is_file():
                    rel_path = item.relative_to(self.templates_dir)
                    dest_file = local_dir / rel_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_file)

    async def get_sandbox(self, sandbox_id: str) -> Optional[DaytonaSandbox]:
        return self.sandboxes.get(sandbox_id)

    async def delete_sandbox(self, sandbox_id: str):
        sandbox = self.sandboxes.get(sandbox_id)
        if sandbox and not sandbox.is_mock and sandbox._real_sandbox is not None:
            try:
                client = self._get_client()
                await client.delete(sandbox._real_sandbox)
                logger.info(f"Deleted real Daytona sandbox: {sandbox_id}")
            except Exception as e:
                logger.warning(f"Failed to delete real sandbox {sandbox_id}: {e}")
        self.sandboxes.pop(sandbox_id, None)


daytona_client = DaytonaClient()
