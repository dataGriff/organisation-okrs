import os, io, csv, tempfile, zipfile
from typing import List, Dict, Any
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.parser import load_markdown_docs

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

OKR_DIR = os.getenv("OKR_DIR", "/data/okrs")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

app = FastAPI(title="OKR Markdown Agent (No-API-Key)")

# Relaxed CORS for local use (tighten in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

class Hit(BaseModel):
    path: str
    snippet: str

class AskResponse(BaseModel):
    query: str
    bullets: List[str]
    citations: List[Hit]

state: Dict[str, Any] = {
    "docs": [],
    "store": None,
    "splitter": RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150),
    "embeddings": None,
}

def _build():
    docs = load_markdown_docs(OKR_DIR)
    state["docs"] = docs
    splitter = state["splitter"]

    chunks, metadatas = [], []
    for d in docs:
        for c in splitter.split_text(d["text"]):
            chunks.append(c)
            metadatas.append({"path": d["path"], **d.get("meta", {})})

    if state["embeddings"] is None:
        state["embeddings"] = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    state["store"] = FAISS.from_texts(chunks, state["embeddings"], metadatas=metadatas)

def _ensure_built():
    if state["store"] is None:
        _build()

@app.get("/health")
def health():
    _ensure_built()
    return {"status": "ok", "docs": len(state["docs"])}

@app.post("/refresh")
def refresh():
    _build()
    return {"status": "refreshed", "docs": len(state["docs"])}

@app.get("/search", response_model=List[Hit])
def search(q: str = Query(..., min_length=2), k: int = 5):
    _ensure_built()
    results = state["store"].similarity_search(q, k=k)
    out = []
    for r in results:
        snippet = r.page_content.strip()
        if len(snippet) > 400:
            snippet = snippet[:400] + "…"
        out.append(Hit(path=r.metadata.get("path", ""), snippet=snippet))
    return out

@app.get("/ask", response_model=AskResponse)
def ask(q: str = Query(..., min_length=2), k: int = 6):
    """
    Extractive answer (no LLM):
    - Retrieve top-k chunks
    - Rank sentences by cosine similarity
    - Return best few as bullets + citations
    """
    _ensure_built()
    hits = state["store"].similarity_search(q, k=k)

    import re
    sentences, meta_by_idx = [], []
    for h in hits:
        parts = re.split(r'(?<=[.!?])\s+', h.page_content.strip())
        for s in parts:
            s = s.strip()
            if 40 <= len(s) <= 300:
                sentences.append(s)
                meta_by_idx.append(h.metadata.get("path", ""))

    if not sentences:
        return AskResponse(query=q, bullets=[], citations=[])

    emb = state["embeddings"]
    q_vec = emb.embed_query(q)
    s_vecs = emb.embed_documents(sentences)

    def cos(a, b):
        import math
        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(y*y for y in b))
        return dot / (na * nb + 1e-12)

    scored = [(cos(q_vec, v), i) for i, v in enumerate(s_vecs)]
    scored.sort(reverse=True)

    top, seen = [], set()
    for score, i in scored:
        key = sentences[i][:80]
        if key in seen: continue
        seen.add(key)
        top.append((score, i))
        if len(top) >= 6: break

    bullets = [sentences[i] for (_, i) in top]

    citations: List[Hit] = []
    for h in hits[:min(5, len(hits))]:
        snippet = h.page_content.strip()
        if len(snippet) > 300:
            snippet = snippet[:300] + "…"
        citations.append(Hit(path=h.metadata.get("path", ""), snippet=snippet))

    return AskResponse(query=q, bullets=bullets, citations=citations)

@app.get("/download")
def download(q: str = Query(..., min_length=2), k: int = 8, format: str = "zip"):
    """
    Package matching OKR files for download:
    - format=zip → okrs.zip (full .md files)
    - format=csv → okrs.csv (path, snippet rows)
    """
    _ensure_built()
    hits = state["store"].similarity_search(q, k=k)

    if format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["path", "snippet"])
        for h in hits:
            snippet = h.page_content.strip().replace("\n", " ")
            writer.writerow([h.metadata.get("path", ""), snippet[:1000]])
        data = buf.getvalue().encode("utf-8")
        return StreamingResponse(
            io.BytesIO(data),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="okrs.csv"'}
        )

    if format == "zip":
        tmpdir = tempfile.mkdtemp()
        zip_path = os.path.join(tmpdir, "okrs.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            added = set()
            for h in hits:
                rel_path = h.metadata.get("path", "unknown.md")
                if rel_path in added: continue
                added.add(rel_path)
                abs_path = os.path.join(OKR_DIR, rel_path)
                if os.path.exists(abs_path):
                    zf.write(abs_path, arcname=rel_path)
        return FileResponse(zip_path, filename="okrs.zip")

    raise HTTPException(status_code=400, detail="Unsupported format. Use 'zip' or 'csv'.")

# Serve the UI at /ui
app.mount("/ui", StaticFiles(directory="web", html=True), name="ui")
