from __future__ import annotations
import sys
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"


def main() -> int:
    # Ensure we're in repo root
    cwd = str(ROOT)

    # Prefer venv pytest if available
    pytest_cmd = [sys.executable, "-m", "pytest", "-q", str(TESTS_DIR)]

    print(f"Running tests in: {TESTS_DIR}")
    try:
        result = subprocess.run(pytest_cmd, cwd=cwd)
        return result.returncode
    except FileNotFoundError:
        print("pytest is not installed in this environment. Install with: pip install pytest")
        return 127


if __name__ == "__main__":
    raise SystemExit(main())
