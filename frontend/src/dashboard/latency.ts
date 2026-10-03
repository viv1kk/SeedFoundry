// A panel's declared latency (descriptor `latency_ms`, build-simulation.md section 6.4, D-60). The
// browser honours it: a panel that declares one waits that long after its data arrives before it
// draws, while every other panel draws at once (NFR-3). Only iteration 1's treemap declares one
// (L-1). Its own module, so tests can hold and release the wait.

export function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
