"""run.py's children end with it (D-78). M12 found that a launcher ended from outside, as a tool's
stop does, left uvicorn and Vite running: Ctrl+C reaches every process on the console, but a kill
skips launch()'s `finally`. On Windows the launcher now joins a job object that ends every process
in it when the launcher ends.

Each test starts a stand-in launcher that does what run.py does before it starts the servers, then
starts a grandchild through cmd.exe, as `npm run dev` starts node through npm.cmd. The test kills
the stand-in outright and watches the grandchild. Windows only: elsewhere run.py has no job object
and Ctrl+C is the documented way to stop it (operator-guide.md section 8)."""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.skipif(os.name != "nt", reason="the job object is Windows only (D-78)")

LAUNCHER = """
import importlib.util, subprocess, sys, time
spec = importlib.util.spec_from_file_location("run", {run!r})
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)
contained = run.contain_children() if {contain} else False
sleeper = "import os, time; print(os.getpid(), flush=True); time.sleep(60)"
subprocess.Popen(["cmd", "/c", sys.executable, "-c", sleeper])
print("contained" if contained else "not contained", flush=True)
time.sleep(60)
"""

SYNCHRONIZE = 0x00100000
PROCESS_TERMINATE = 0x0001
WAIT_OBJECT_0 = 0

if os.name == "nt":
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]


def start_launcher(contain: bool) -> tuple[subprocess.Popen, int, str]:
    code = LAUNCHER.format(run=str(ROOT / "run.py"), contain=contain)
    launcher = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
    lines = sorted(launcher.stdout.readline().strip() for _ in range(2))  # the pid and the status, in either order
    return launcher, int(lines[0]), lines[1]


def ends_within(handle: int, ms: int) -> bool:
    return kernel32.WaitForSingleObject(handle, ms) == WAIT_OBJECT_0


def open_process(pid: int) -> int:
    handle = kernel32.OpenProcess(SYNCHRONIZE | PROCESS_TERMINATE, False, pid)  # terminate, to clean up
    assert handle, f"process {pid} is not running"
    return handle


def end(launcher: subprocess.Popen, grandchild: int) -> None:
    kernel32.TerminateProcess(grandchild, 1)
    kernel32.CloseHandle(grandchild)
    launcher.stdout.close()


def test_a_killed_launcher_takes_its_grandchildren_with_it():
    launcher, pid, status = start_launcher(contain=True)
    assert status == "contained"
    grandchild = open_process(pid)  # held before the kill, so a reused pid cannot fool the wait
    try:
        launcher.kill()  # TerminateProcess: no Ctrl+C, no finally
        launcher.wait(10)
        assert ends_within(grandchild, 5000), "the grandchild outlived the launcher"
    finally:
        end(launcher, grandchild)


def test_without_the_job_a_killed_launcher_leaves_its_grandchildren_running():
    # The M12 behaviour, kept as the control: it shows the test above can fail.
    launcher, pid, status = start_launcher(contain=False)
    assert status == "not contained"
    grandchild = open_process(pid)
    try:
        launcher.kill()
        launcher.wait(10)
        assert not ends_within(grandchild, 1000)
    finally:
        end(launcher, grandchild)
