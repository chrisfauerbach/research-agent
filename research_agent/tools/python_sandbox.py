"""Execute Python code in a restricted subprocess with timeout."""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from research_agent.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 30
MAX_OUTPUT_CHARS = 8_000


class PythonSandboxTool(BaseTool):
    name = "python_sandbox"
    description = "Execute a Python snippet in a sandboxed subprocess and return stdout/stderr."

    async def run(self, *, query: str, **kwargs: Any) -> ToolResult:
        code = query.strip()
        logger.info("PythonSandbox: executing %d chars of code", len(code))

        with tempfile.TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "script.py"
            script.write_text(code)

            try:
                python = shutil.which("python3") or shutil.which("python") or sys.executable
                proc = subprocess.run(
                    [python, str(script)],
                    capture_output=True,
                    text=True,
                    timeout=TIMEOUT_SECONDS,
                    cwd=tmpdir,
                    env={"PATH": "/usr/bin:/usr/local/bin", "HOME": tmpdir},
                )
                output = proc.stdout[:MAX_OUTPUT_CHARS]
                if proc.stderr:
                    output += f"\n--- stderr ---\n{proc.stderr[:MAX_OUTPUT_CHARS]}"
                success = proc.returncode == 0
            except subprocess.TimeoutExpired:
                output = f"Execution timed out after {TIMEOUT_SECONDS}s"
                success = False
            except Exception as exc:
                output = str(exc)
                success = False

        return ToolResult(tool=self.name, success=success, data=output)
