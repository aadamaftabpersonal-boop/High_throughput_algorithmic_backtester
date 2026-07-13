# sandbox/run_sandboxed.py
"""
Wraps `docker run` with a hard wall-clock timeout — kills the container
if it hasn't finished within TIMEOUT_SECONDS.
"""
import subprocess
import sys

TIMEOUT_SECONDS = 60

def run_sandbox(strategy_path: str, data_path: str, output_dir: str) -> int:
    cmd = [
        "docker", "run", "--rm",
        "--memory=512m", "--memory-swap=512m", "--cpus=1.0", "--pids-limit=100",
        "--network", "none", "--read-only", "--tmpfs", "/tmp",
        "-v", f"{strategy_path}:/app/user_strategy.py:ro",
        "-v", f"{data_path}:/data/input.parquet:ro",
        "-v", f"{output_dir}:/output",
        "backtester-sandbox",
    ]
    try:
        result = subprocess.run(cmd, timeout=TIMEOUT_SECONDS, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(f"Container exited with error:\n{result.stderr}", file=sys.stderr)
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"Sandbox exceeded {TIMEOUT_SECONDS}s timeout — killed.", file=sys.stderr)
        return -1


if __name__ == "__main__":
    import os
    root = os.getcwd()
    code = run_sandbox(
        strategy_path=f"{root}/sandbox/user_strategy.py",
        data_path=f"{root}/data/raw/AAPL_TEST_clean.parquet",
        output_dir=f"{root}/sandbox/sandbox_output",
    )
    print(f"Exit code: {code}")