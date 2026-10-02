"""FastAPI app. Every route is under /api. M0 serves the health check only."""

from fastapi import FastAPI

app = FastAPI(title="SeedFoundry")


@app.get("/api/health")
def health() -> dict[str, str]:
    """Readiness, which run.py polls before announcing the app."""
    return {"status": "ok", "app": "SeedFoundry"}
