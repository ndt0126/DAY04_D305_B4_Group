from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure starter_v0 root is in Python path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version
from chat import run_model_tool_loop, write_transcript, now_iso, safe_slug, trim_history

load_lab_env(ROOT_DIR)

app = FastAPI(
    title="Research Agent API Backend",
    description="FastAPI server powering the Research Agent FE UI",
    version="1.0.0",
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ARTIFACTS_DIR = ROOT_DIR / "artifacts"
TRANSCRIPTS_DIR = ROOT_DIR / "transcripts"
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"



class ChatTurnRequest(BaseModel):
    user_input: str
    provider: str = "openai"
    model: Optional[str] = None
    version: str = "baseline"
    history: List[dict[str, str]] = []
    history_window: int = 5
    max_tool_rounds: int = 4


@app.get("/api/health")
def health_check():
    return {"status": "ok", "timestamp": now_iso()}


@app.get("/api/config")
def get_config(version: str = "baseline"):
    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    
    system_prompt = system_prompt_path.read_text(encoding="utf-8") if system_prompt_path.exists() else ""
    tool_declarations = load_tool_declarations(tools_path) if tools_path.exists() else []
    artifact_version = build_artifact_version(version, system_prompt_path, tools_path)
    
    return {
        "providers": ["openai", "openrouter", "anthropic", "gemini"],
        "active_version": version,
        "artifact_version": artifact_version.artifact_version,
        "system_prompt": system_prompt,
        "tools": tool_declarations,
    }


@app.post("/api/chat")
def chat_endpoint(req: ChatTurnRequest):
    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"

    if not system_prompt_path.exists():
        raise HTTPException(status_code=400, detail="system_prompt.md not found in artifacts/")
    if not tools_path.exists():
        raise HTTPException(status_code=400, detail="tools.yaml not found in artifacts/")

    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(tool_declarations)

    try:
        provider = make_provider(req.provider)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid provider '{req.provider}': {str(exc)}")

    selected_model = req.model or getattr(provider, "default_model", None)
    artifact_version = build_artifact_version(req.version, system_prompt_path, tools_path)

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([
        safe_slug(req.version),
        safe_slug(req.provider),
        timestamp,
    ])
    transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"

    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(req.history, req.history_window),
        {"role": "user", "content": req.user_input},
    ]

    turn_record = {
        "turn_index": len(req.history) // 2 + 1,
        "started_at": now_iso(),
        "user": req.user_input,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    try:
        result = run_model_tool_loop(
            provider=provider,
            messages=messages,
            tools=openai_tools,
            model=req.model,
            max_tool_rounds=req.max_tool_rounds,
        )
        turn_record.update(result)
    except Exception as exc:
        turn_record.update({
            "status": "provider_error",
            "error": f"{type(exc).__name__}: {str(exc)}",
            "assistant_text": f"Error from provider: {str(exc)}"
        })

    turn_record["ended_at"] = now_iso()

    # Save transcript
    transcript_data = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": req.provider,
        "model": selected_model,
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "history_window": req.history_window,
        "max_tool_rounds": req.max_tool_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [turn_record],
    }
    write_transcript(transcript_path, transcript_data)

    return {
        "status": turn_record.get("status"),
        "assistant_text": turn_record.get("assistant_text") or "",
        "rounds": turn_record.get("rounds", []),
        "tool_events": turn_record.get("tool_events", []),
        "error": turn_record.get("error"),
        "artifact_version": artifact_version.artifact_version,
        "transcript_id": transcript_id,
        "transcript_path": str(transcript_path),
        "provider": req.provider,
        "model": selected_model,
    }


@app.get("/api/transcripts")
def list_transcripts():
    if not TRANSCRIPTS_DIR.exists():
        return []

    items = []
    for p in sorted(TRANSCRIPTS_DIR.glob("*.transcript.json"), reverse=True):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            items.append({
                "transcript_id": data.get("transcript_id", p.stem),
                "created_at": data.get("created_at"),
                "provider": data.get("provider"),
                "model": data.get("model"),
                "artifact_version": data.get("artifact_version"),
                "turns_count": len(data.get("turns", [])),
                "path": str(p),
            })
        except Exception:
            continue
    return items


@app.get("/api/transcripts/{transcript_id}")
def get_transcript(transcript_id: str):
    p = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    if not p.exists():
        # Try finding by wildcard if full name wasn't passed
        matches = list(TRANSCRIPTS_DIR.glob(f"*{transcript_id}*.json"))
        if matches:
            p = matches[0]
        else:
            raise HTTPException(status_code=404, detail=f"Transcript '{transcript_id}' not found.")

    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error reading transcript: {str(exc)}")


if FRONTEND_DIST.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_excludes=["transcripts/*", "runs/*", "*.transcript.json"]
    )


