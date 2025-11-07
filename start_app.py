#!/usr/bin/env python3
"""
Bootstraps the Cooling backend (and optionally the frontend) with one command.

Usage:
    python start_app.py [--host 0.0.0.0] [--port 8001]
                        [--frontend-port 3000] [--no-frontend]
                        [--reload]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "APP" / "backend"
FRONTEND_DIR = REPO_ROOT / "APP" / "frontend"
NODE_BIN = REPO_ROOT / "tools" / "node" / "bin"
LOCAL_BIN = REPO_ROOT / ".npm-global" / "bin"


def ensure_repo_on_path() -> None:
    repo_str = str(REPO_ROOT)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Cooling backend (and frontend) dev servers.")
    parser.add_argument("--host", default=os.getenv("APP_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("APP_PORT", 8001)))
    parser.add_argument("--frontend-port", type=int, default=int(os.getenv("APP_FRONTEND_PORT", 3000)))
    parser.add_argument("--reload", action="store_true", default=os.getenv("APP_RELOAD", "1") == "1")
    parser.add_argument("--no-frontend", action="store_true", help="Skip launching the CRA dev server.")
    return parser.parse_args()


def build_backend_command(args: argparse.Namespace) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "APP.backend.server:app",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if args.reload:
        cmd.append("--reload")
    return cmd


def build_frontend_env(args: argparse.Namespace) -> dict[str, str]:
    env = {}
    path_parts = [str(NODE_BIN), str(LOCAL_BIN), os.environ.get("PATH", "")]
    env["PATH"] = ":".join(path_parts)
    env["TMPDIR"] = str(REPO_ROOT / "tmp")
    api_host = "localhost" if args.host in ("0.0.0.0", "127.0.0.1") else args.host
    env.setdefault("REACT_APP_API_BASE_URL", f"http://{api_host}:{args.port}/api")
    env.setdefault("BROWSER", "none")
    env["PORT"] = str(args.frontend_port)
    return env


def start_process(label: str, cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.Popen:
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    existing_pythonpath = process_env.get("PYTHONPATH", "")
    paths = [str(REPO_ROOT)]
    if existing_pythonpath:
        paths.append(existing_pythonpath)
    process_env["PYTHONPATH"] = os.pathsep.join(paths)
    print(f"[start_app] Launching {label}: {' '.join(cmd)}")
    return subprocess.Popen(cmd, cwd=cwd, env=process_env)


def run() -> None:
    ensure_repo_on_path()
    args = parse_args()
    processes: list[tuple[str, subprocess.Popen]] = []

    backend_cmd = build_backend_command(args)
    processes.append(("backend", start_process("backend", backend_cmd, cwd=BACKEND_DIR)))

    if not args.no_frontend:
        if not NODE_BIN.exists():
            print("[start_app] WARNING: tools/node not found; skipping frontend startup.")
        elif not (FRONTEND_DIR / "package.json").exists():
            print("[start_app] WARNING: frontend folder missing; skipping frontend startup.")
        else:
            frontend_env = build_frontend_env(args)
            yarn_executable = shutil.which("yarn", path=frontend_env["PATH"])
            if not yarn_executable:
                print("[start_app] WARNING: yarn not found in PATH; skipping frontend startup.")
            else:
                processes.append(
                    (
                        "frontend",
                        start_process(
                            "frontend",
                            [yarn_executable, "start"],
                            cwd=FRONTEND_DIR,
                            env=frontend_env,
                        ),
                    )
                )

    try:
        while True:
            for label, proc in processes:
                retcode = proc.poll()
                if retcode is not None:
                    raise SystemExit(f"{label} process exited with code {retcode}")
            time.sleep(1)
    except KeyboardInterrupt as exc:
        print(f"[start_app] Shutting down ({exc}).")
    finally:
        for label, proc in processes:
            if proc.poll() is None:
                print(f"[start_app] Terminating {label}...")
                proc.terminate()
        for _, proc in processes:
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    run()
