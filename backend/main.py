"""AI-CCTV Sentinel — FastAPI backend foundation (Task 1)."""

from fastapi import FastAPI

app = FastAPI(
    title="AI-CCTV Sentinel API",
    description=(
        "Backend foundation for the self-learning edge-AI "
        "CCTV animal hazard detection system."
    ),
    version="0.1.0",
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "project": "AI-CCTV Sentinel",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
    }
