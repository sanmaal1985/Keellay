"""Smoke test for a built wheel, run outside the source tree (not collected by pytest):

    uv run --isolated --no-project --with dist/*.whl tests/check_wheel.py

Checks that the installed package starts and carries the method files inside it.
"""

import json
import subprocess
import sys
from pathlib import Path

result = subprocess.run([sys.executable, "-m", "keellay", "info"], capture_output=True, text=True, check=True)
info = json.loads(result.stdout)

assert info["status"] == "ok", info
assert info["method_bundled"], f"method files are not bundled in the wheel: {info}"
assert (Path(info["method_dir"]) / "README.md").is_file(), f"method README missing: {info}"

print(f"smoke test passed: keellay {info['version']}, method at {info['method_dir']}")
