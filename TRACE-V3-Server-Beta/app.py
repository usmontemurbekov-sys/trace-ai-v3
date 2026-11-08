"""TRACE V3 research beta: lightweight server-side AI-text signal classifier."""
import os
import re
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from huggingface_hub import hf_hub_download
from joblib import load

MODEL_ID = "rasbt/ai-text-detector-logreg"
MODEL_FILE = "logreg-ai-detector.joblib"
MODEL_LOCAL = Path(__file__).resolve().parent / "model" / MODEL_FILE
_model = None
_error: Optional[str] = None
_lock = threading.Lock()


def load_detector():
    global _model, _error
    if _model is not None:
        return _model
    with _lock:
        if _model is not None:
            return _model
        try:
            # Never load untrusted pickle/joblib files. Pin a trusted model revision before production.
            filename = str(MODEL_LOCAL) if MODEL_LOCAL.exists() else hf_hub_download(
                repo_id=MODEL_ID, filename=MODEL_FILE
            )
            _model = load(filename)
            _error = None
            return _model
        except Exception as exc:
            _error = f"Model initialization failed ({type(exc).__name__}). Check server logs."
            raise RuntimeError(_error) from exc


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Model is loaded at build/startup, not in the visitor's browser.
    try:
        load_detector()
    except Exception as exc:
        print(str(exc), flush=True)
    yield

app = FastAPI(title="TRACE V3 Research API", version="3.0.0", lifespan=lifespan,
              docs_url=None, redoc_url=None)
origins = [x.strip() for x in os.environ.get("ALLOWED_ORIGINS", "https://trace-ai-detector.usmontemurbekov72.workers.dev").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"],
                   allow_headers=["Content-Type"])

class TextRequest(BaseModel):
    text: str = Field(min_length=100, max_length=40000)


@app.get("/api/health")
def health():
    return {"status": "ready" if _model is not None else "model_unavailable",
            "model": MODEL_ID, "model_ready": _model is not None,
            "error": _error if _model is None else None}


@app.post("/api/analyze")
def analyze(payload: TextRequest):
    text = payload.text.strip()
    words = re.findall(r"\b[\w’'-]+\b", text, flags=re.UNICODE)
    if len(words) < 40:
        raise HTTPException(status_code=422, detail="Please enter at least 40 words.")
    if len(words) > 6000:
        raise HTTPException(status_code=422, detail="Please enter no more than 6,000 words.")
    if _model is None:
        raise HTTPException(status_code=503, detail="Detection model is currently unavailable. Please retry later.")
    # Trim length to bound inference time, and report coverage transparently.
    excerpt = " ".join(words[:1500])
    try:
        classes = list(_model.classes_)
        ai_col = classes.index(1)
        signal = float(_model.predict_proba([excerpt])[0, ai_col])
    except Exception as exc:
        print(f"Inference failed: {type(exc).__name__}", flush=True)
        raise HTTPException(status_code=503, detail="Classifier could not complete this request.") from exc
    return {"model_ready": True, "model": MODEL_ID, "ai_signal": signal,
            "words_analyzed": min(len(words),1500), "total_words": len(words),
            "disclaimer": "Unvalidated on TRACE use cases. Not evidence of AI authorship or misconduct."}


@app.get("/")
def homepage():
    return FileResponse(Path(__file__).parent / "index.html")
