from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .service import WebSessionService


class MessageRequest(BaseModel):
    content: str = Field(..., min_length=1)


class SectionsRequest(BaseModel):
    sections: list[str] = Field(default_factory=list)


class RunRequest(BaseModel):
    sections: list[str] | None = None


service = WebSessionService()
app = FastAPI(title="MathAgent Web API", version="0.1.0")
frontend_dist = Path(__file__).resolve().parents[3] / "frontend" / "dist"
frontend_assets = frontend_dist / "assets"

if frontend_assets.exists():
    app.mount("/assets", StaticFiles(directory=frontend_assets), name="frontend-assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/meta")
def meta() -> dict[str, object]:
    return {"sections": service.available_sections()}


@app.post("/api/sessions")
def create_session() -> dict[str, object]:
    return service.create_session()


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> dict[str, object]:
    try:
        return service.get_session_summary(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/sessions/{session_id}/messages")
def add_message(session_id: str, payload: MessageRequest) -> dict[str, object]:
    try:
        return service.add_message(session_id, payload.content)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/sessions/{session_id}/sections")
def set_sections(session_id: str, payload: SectionsRequest) -> dict[str, object]:
    try:
        return service.set_report_sections(session_id, payload.sections)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/sessions/{session_id}/run")
def run_session(session_id: str, payload: RunRequest) -> dict[str, object]:
    try:
        return service.run_session(session_id, sections=payload.sections)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/sessions/{session_id}/report")
def get_report(
    session_id: str,
    sections: Annotated[list[str] | None, Query()] = None,
) -> dict[str, object]:
    try:
        return service.get_report(session_id, sections=sections)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/sessions/{session_id}/files")
async def upload_files(
    session_id: str,
    role: Annotated[str, Form(...)],
    files: Annotated[list[UploadFile], File(...)],
) -> dict[str, object]:
    try:
        payload = []
        for file in files:
            payload.append((file.filename or "upload.bin", await file.read()))
        return service.upload_files(session_id, role=role, files=payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/", response_model=None)
def root():
    index_path = frontend_dist / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "message": "MathAgent Web API is running.",
        "frontend_dist_exists": frontend_dist.exists(),
        "docs": "/docs",
    }
