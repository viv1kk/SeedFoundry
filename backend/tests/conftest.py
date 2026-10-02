"""Shared fixtures: an in-process client over a temporary var/, and a real
uvicorn server for restart and SSE tests."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from seedfoundry.main import create_app

BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture
def var_dir(tmp_path: Path) -> Path:
    return tmp_path / "var"


@pytest.fixture
def client(var_dir: Path) -> Iterator[TestClient]:
    with TestClient(create_app(var_dir)) as test_client:
        yield test_client


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class Server:
    """A uvicorn process serving seedfoundry.main:app over a given var/."""

    def __init__(self, var_dir: Path) -> None:
        self.var_dir = var_dir
        self.process: subprocess.Popen | None = None

    def start(self) -> None:
        # A fresh port each start, so a restart never waits on the old socket.
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        env = {**os.environ, "SEEDFOUNDRY_VAR_DIR": str(self.var_dir)}
        self.process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "seedfoundry.main:app", "--host", "127.0.0.1", "--port", str(self.port)],
            cwd=BACKEND,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            assert self.process.poll() is None, "server exited during start"
            try:
                with urllib.request.urlopen(self.base + "/api/health", timeout=1):
                    return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("server did not start")

    def kill(self) -> None:
        """Stop hard, as a crash or a closed terminal would."""
        if self.process and self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=10)

    def request(self, method: str, path: str, body: object = None) -> tuple[int, object]:
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(self.base + path, data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                text = response.read()
                return response.status, json.loads(text) if text else None
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read())

    @contextmanager
    def sse(self, path: str, last_event_id: int | None = None):
        req = urllib.request.Request(self.base + path)
        if last_event_id is not None:
            req.add_header("Last-Event-ID", str(last_event_id))
        with urllib.request.urlopen(req, timeout=5) as response:
            yield SseReader(response)


class SseReader:
    def __init__(self, response) -> None:
        self.response = response
        self.headers = response.headers

    def frame(self) -> dict[str, str]:
        """The next frame that carries an event (skips retry and keepalive)."""
        while True:
            fields: dict[str, str] = {}
            while True:
                line = self.response.readline().decode("utf-8")
                if line in ("\n", ""):
                    break
                if line.startswith(":"):
                    continue
                key, _, value = line.rstrip("\n").partition(": ")
                fields[key] = value
            if "event" in fields:
                fields["data"] = json.loads(fields["data"])
                return fields

    def frames(self, count: int) -> list[dict]:
        return [self.frame() for _ in range(count)]


@pytest.fixture
def server(var_dir: Path) -> Iterator[Server]:
    running = Server(var_dir)
    try:
        yield running
    finally:
        running.kill()
