"""Start SeedFactory's backend and frontend together, or run both test suites.

    python run.py          start both processes; Ctrl+C stops both
    python run.py test     run the backend and frontend test suites

The backend runs from backend/.venv. If that does not exist, uv makes it;
where uv is blocked or missing, run.ps1 makes it with pip instead.

On Windows both processes also stop when the launcher is ended from outside
(a job object, D-78). Elsewhere, stop it with Ctrl+C, which stops both.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

sys.path.insert(0, str(BACKEND))
from seedfoundry.config import BACKEND_HOST, BACKEND_PORT, FRONTEND_PORT  # noqa: E402

BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}/api/health"
FRONTEND_URL = f"http://127.0.0.1:{FRONTEND_PORT}/"


def backend_python() -> str:
    scripts = "Scripts/python.exe" if os.name == "nt" else "bin/python"
    venv = BACKEND / ".venv" / scripts
    if not venv.exists():
        if not shutil.which("uv"):
            sys.exit("No backend environment. On Windows run run.ps1, elsewhere: uv sync --project backend")
        subprocess.run(["uv", "sync", "--project", str(BACKEND)], check=True)
    return str(venv)


def npm() -> str:
    found = shutil.which("npm")
    if not found:
        sys.exit("npm is not on the path. Install Node.js 22.18 or newer.")
    return found


def ensure_frontend_packages() -> None:
    if not (FRONTEND / "node_modules").exists():
        subprocess.run([npm(), "install"], cwd=FRONTEND, check=True)


def answers(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1):
            return True
    except OSError:
        return False


def wait_for(url: str, name: str, process: subprocess.Popen, seconds: float = 60) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"{name} exited before it answered")
        if answers(url):
            return
        time.sleep(0.25)
    raise RuntimeError(f"{name} did not answer at {url} within {seconds:.0f} s")


def contain_children() -> bool:
    """On Windows, put this launcher in a job object that ends every process in it when its last
    handle closes (D-78). The handle is this process's own, and the children (uvicorn, npm and the
    node it starts) join the job as they start, so they end with the launcher however it ends:
    Ctrl+C, a closed window, or a kill from outside, which skips launch()'s `finally`. Returns
    False where there is no job object (elsewhere, or if Windows refuses), and the launcher then
    relies on Ctrl+C alone, as before."""
    if os.name != "nt":
        return False
    import ctypes
    from ctypes import wintypes

    class BasicLimits(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD),
        ]

    class ExtendedLimits(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", BasicLimits), ("IoInfo", ctypes.c_uint64 * 6),
            ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        return False
    limits = ExtendedLimits()
    limits.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    extended_limit_information = 9
    if not kernel32.SetInformationJobObject(job, extended_limit_information, ctypes.byref(limits), ctypes.sizeof(limits)):
        return False
    # The handle is never closed: it closes when this process ends, whichever way it ends.
    return bool(kernel32.AssignProcessToJobObject(job, kernel32.GetCurrentProcess()))


def stop(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        # npm.cmd starts node as a child; stop the whole tree.
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)], capture_output=True)
    else:
        process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def launch() -> int:
    for url, name in ((BACKEND_URL, "backend"), (FRONTEND_URL, "frontend")):
        if answers(url):
            sys.exit(f"Something already answers at {url}. Stop the earlier {name} server first.")
    python = backend_python()
    ensure_frontend_packages()
    contain_children()
    processes: list[subprocess.Popen] = []
    try:
        backend = subprocess.Popen(
            [python, "-m", "uvicorn", "seedfoundry.main:app",
             "--host", BACKEND_HOST, "--port", str(BACKEND_PORT),
             # An open SSE stream never ends by itself; do not wait on it at shutdown.
             "--timeout-graceful-shutdown", "2"],
            cwd=BACKEND,
        )
        processes.append(backend)
        wait_for(BACKEND_URL, "backend", backend)
        frontend = subprocess.Popen([npm(), "run", "dev"], cwd=FRONTEND)
        processes.append(frontend)
        wait_for(FRONTEND_URL, "frontend", frontend)
        print(f"\nSeedFactory ready at {FRONTEND_URL}  (Ctrl+C stops both)\n", flush=True)
        while all(p.poll() is None for p in processes):
            time.sleep(0.5)
        return 1
    except KeyboardInterrupt:
        return 0
    except RuntimeError as error:
        print(f"Launch failed: {error}", file=sys.stderr)
        return 1
    finally:
        for process in reversed(processes):
            stop(process)


def test() -> int:
    python = backend_python()
    ensure_frontend_packages()
    backend = subprocess.run([python, "-m", "pytest"], cwd=BACKEND).returncode
    frontend = subprocess.run([npm(), "test"], cwd=FRONTEND).returncode
    print(f"\nbackend: {'pass' if backend == 0 else 'FAIL'}, frontend: {'pass' if frontend == 0 else 'FAIL'}")
    return 0 if backend == 0 and frontend == 0 else 1


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "launch"
    if command not in ("launch", "test"):
        sys.exit(__doc__)
    sys.exit(launch() if command == "launch" else test())
