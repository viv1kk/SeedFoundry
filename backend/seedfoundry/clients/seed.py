"""SeedClient and its simulated implementation (D-22): Seed v0.1's API as SeedFoundry
drives it in phases 5 to 8 and 11. Nothing leaves the process. Ids and latencies come
from the build's seeded RNG; state names are Seed v0.1's (seed-reuse-notes.md §3.1).
Checksums are real: the simulated server hashes the bytes it is given."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import Any, Protocol

API = "/v0.1"


@dataclass(frozen=True)
class ApiCall:
    method: str
    path: str
    status: int
    latency_ms: int
    simulated: bool
    body: dict[str, Any] = field(default_factory=dict)

    def as_data(self) -> dict[str, object]:
        return {
            "method": self.method,
            "path": self.path,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "simulated": self.simulated,
            "response": self.body,
        }

    @property
    def message(self) -> str:
        label = " (simulated)" if self.simulated else ""
        return f"{self.method} {self.path} {self.status}{label}"


class SeedClient(Protocol):
    def health(self) -> ApiCall: ...
    def create_seed(self, manifest: dict[str, Any]) -> ApiCall: ...
    def provision_sandbox(self, seed_id: str) -> ApiCall: ...
    def upload(self, sandbox_id: str, name: str, content: bytes) -> ApiCall: ...
    def dry_run(self, sandbox_id: str, dataset: str) -> ApiCall: ...
    def plant(self, seed_id: str, layers: list[str]) -> ApiCall: ...
    def status(self, seed_id: str) -> ApiCall: ...
    def advance(self, seed_id: str, stage: str, state: str) -> ApiCall: ...
    def answer(self, seed_id: str, request_id: str, body: dict[str, Any]) -> ApiCall: ...
    def cleanup(self, seed_id: str, operation: str) -> ApiCall: ...
    def collect(self, seed_id: str, weeks: tuple[int, int]) -> ApiCall: ...
    def teardown(self, sandbox_id: str) -> ApiCall: ...


class SimulatedSeedClient:
    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.state = "UNINITIALIZED"

    def _call(self, method: str, path: str, code: int, **body: Any) -> ApiCall:
        return ApiCall(method, f"{API}{path}", code, self.rng.randint(40, 320), simulated=True, body=body)

    def _id(self, prefix: str) -> str:
        return f"{prefix}-{self.rng.getrandbits(16):04x}"

    def health(self) -> ApiCall:
        return self._call("GET", "/health", 200, status="ok", version="0.1")

    def create_seed(self, manifest: dict[str, Any]) -> ApiCall:
        return self._call("POST", "/seeds", 201, seed_id=self._id("seed"), name=manifest.get("seed"))

    def provision_sandbox(self, seed_id: str) -> ApiCall:
        return self._call("POST", "/sandboxes", 201, sandbox_id=self._id("sbx"), seed_id=seed_id, egress=False)

    def upload(self, sandbox_id: str, name: str, content: bytes) -> ApiCall:
        digest = hashlib.sha256(content).hexdigest()
        return self._call("PUT", f"/sandboxes/{sandbox_id}/files/{name}", 201, name=name, bytes=len(content), sha256=digest)

    def dry_run(self, sandbox_id: str, dataset: str) -> ApiCall:
        return self._call("POST", f"/sandboxes/{sandbox_id}/dry-run", 200, dataset=dataset, completed=True)

    def plant(self, seed_id: str, layers: list[str]) -> ApiCall:
        self.state = "INITIALIZED"
        return self._call("POST", f"/seeds/{seed_id}/plant", 200, phase="INIT", state=self.state, layers=layers)

    def status(self, seed_id: str) -> ApiCall:
        return self._call("GET", f"/seeds/{seed_id}", 200, state=self.state)

    def advance(self, seed_id: str, stage: str, state: str) -> ApiCall:
        self.state = state
        return self._call("POST", f"/seeds/{seed_id}/{stage}", 202, state=state)

    def answer(self, seed_id: str, request_id: str, body: dict[str, Any]) -> ApiCall:
        return self._call("POST", f"/seeds/{seed_id}/requests/{request_id}", 200, request_id=request_id, answered=sorted(body))

    def cleanup(self, seed_id: str, operation: str) -> ApiCall:
        self.state = "CLOSING_SEEDING"
        return self._call("POST", f"/seeds/{seed_id}/cleanup/{operation}", 200, state=self.state, operation=operation)

    def collect(self, seed_id: str, weeks: tuple[int, int]) -> ApiCall:
        self.state = "RUNNING"
        return self._call("POST", f"/seeds/{seed_id}/collect", 200, state=self.state, weeks=list(weeks))

    def teardown(self, sandbox_id: str) -> ApiCall:
        return self._call("DELETE", f"/sandboxes/{sandbox_id}", 204, residue=0)
