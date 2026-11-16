"""API FastAPI pour le chatbot RAG EMSI."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from api.rag import repondre


BACKEND_DIR = Path(__file__).resolve().parents[1]
IMAGES_DIR = BACKEND_DIR / "data" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


class ChatRequest(BaseModel):
    question: str


class SourceResponse(BaseModel):
    source: str
    page: int | str
    type: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
    images: list[str]


app = FastAPI(title="EMSI ChatBot RAG API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(**repondre(request.question))
