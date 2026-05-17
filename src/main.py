from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form

from src.agent import agent, VanguardState
from src.config import config
from src.models import AgentStep, StatusResponse

app = FastAPI(
    title="Vanguard Milano — Autonomous Logistics API",
    description=(
        "AI-powered real-time logistics intelligence engine for the Northern Italian "
        "supply chain. Detects transport strikes, autonomously calculates reroutes, "
        "and executes X402 USDC settlements — zero human latency."
    ),
    version="2.0.0",
)


@app.on_event("startup")
async def startup_event():
    config.validate()


@app.post("/status", response_model=StatusResponse)
async def get_status(
    demo_mode: bool                  = Form(False),
    document:  Optional[UploadFile] = File(None),
):
    """
    Primary agent endpoint.
    Accepts an optional shipping manifest (image / PDF) for multimodal cargo analysis.
    Returns the full RerouteManifest plus the step-by-step agent decision log.
    """
    try:
        doc_bytes = None
        mime_type = None

        if document:
            doc_bytes = await document.read()
            mime_type = document.content_type

        manifest = await agent.analyze_strikes(
            demo_mode=demo_mode,
            document_bytes=doc_bytes,
            mime_type=mime_type,
        )

        steps = [AgentStep(**s) for s in VanguardState.agent_steps]

        return StatusResponse(
            strike_level=manifest.strike_level,
            active_reroutes=manifest.strike_detected,
            manifest=manifest,
            agent_steps=steps,
        )

    except Exception as exc:
        print(f"[VANGUARD][CRITICAL] Backend error: {repr(exc)}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/")
async def root():
    return {
        "agent":     "VANGUARD MILANO",
        "version":   "2.0.0",
        "status":    "operational",
        "endpoints": [
            "POST /status  — run threat scan (+ optional document upload)",
            "GET  /health  — uptime check",
        ],
    }


@app.get("/health")
async def health():
    """Lightweight health-check for Vultr uptime monitoring."""
    return {
        "status":    "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)