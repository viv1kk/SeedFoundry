"""The clock the runner paces builds by. Simulated time (`sim_t`) never comes from it:
the clock only decides how long to wait in real time before playing the next beat
(seed-reuse-notes.md §2.4). Tests use FakeClock and never sleep for real."""

from __future__ import annotations

import asyncio
import heapq
import itertools
from typing import Protocol


class Clock(Protocol):
    def now(self) -> float: ...
    async def sleep(self, seconds: float) -> None: ...


class RealClock:
    """The event loop's monotonic clock: progress is read from it, never added up from
    the slices that were asked for, so load cannot stretch a build (Seed v0.1, M22)."""

    def now(self) -> float:
        return asyncio.get_running_loop().time()

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)


class FakeClock:
    """Virtual time for tests. With `auto`, every sleep moves time on at once, so a
    build plays in full without waiting. Without it, sleepers wait for advance()."""

    def __init__(self, auto: bool = True) -> None:
        self.auto = auto
        self.t = 0.0
        self.slept = 0  # how many sleeps were asked for
        self.longest = 0.0  # the longest one
        self._waiters: list[tuple[float, int, asyncio.Future[None]]] = []
        self._order = itertools.count()

    def now(self) -> float:
        return self.t

    async def sleep(self, seconds: float) -> None:
        self.slept += 1
        self.longest = max(self.longest, seconds)
        if self.auto:
            self.t += max(seconds, 0.0)
            await asyncio.sleep(0)
            return
        future: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        heapq.heappush(self._waiters, (self.t + max(seconds, 0.0), next(self._order), future))
        await future

    async def advance(self, seconds: float) -> None:
        """Move time on, waking each sleeper at its own deadline, in order, and letting
        it run until it sleeps again or finishes."""
        target = self.t + seconds
        while self._waiters and self._waiters[0][0] <= target:
            deadline, _, future = heapq.heappop(self._waiters)
            self.t = max(self.t, deadline)
            if not future.done():
                future.set_result(None)
            await settle()
        self.t = target
        await settle()


async def settle(rounds: int = 20) -> None:
    """Let ready tasks run: a woken sleeper applies its beats and sleeps again within a
    few turns of the loop."""
    for _ in range(rounds):
        await asyncio.sleep(0)
