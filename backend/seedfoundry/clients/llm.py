"""LLMClient and its simulated implementation (D-22). No model is called: token counts
and latencies come from the build's seeded RNG (build-simulation.md §1), so the same
intake and iteration always give the same figures (NFR-1)."""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from typing import Protocol

SIMULATED_MODEL = "simulated-llm"
# The simulated model's context window, in tokens: what a planted Seed's files are measured against
# (D-82). No model is asked; like every token count here, it is simulated.
SIMULATED_CONTEXT_WINDOW = 32_000


@dataclass(frozen=True)
class LLMCall:
    task: str
    model: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    simulated: bool

    def as_data(self) -> dict[str, object]:
        return asdict(self)

    @property
    def message(self) -> str:
        label = " (simulated)" if self.simulated else ""
        return f"{self.task}: {self.tokens_in:,} tokens in, {self.tokens_out:,} out{label}"


class LLMClient(Protocol):
    def call(self, task: str, text: str, output: tuple[int, int]) -> LLMCall:
        """Run one task over `text`; `output` is the expected size of the answer in tokens."""
        ...


class SimulatedLLMClient:
    def __init__(self, rng: random.Random) -> None:
        self.rng = rng

    def call(self, task: str, text: str, output: tuple[int, int]) -> LLMCall:
        # About four bytes a token, with a little jitter, so bigger inputs read as bigger calls.
        tokens_in = max(1, round(len(text.encode("utf-8")) / 4 * self.rng.uniform(0.96, 1.04)))
        tokens_out = self.rng.randint(*output)
        latency_ms = self.rng.randint(600, 2400)
        return LLMCall(task, SIMULATED_MODEL, tokens_in, tokens_out, latency_ms, simulated=True)
