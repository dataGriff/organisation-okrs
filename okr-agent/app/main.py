import os, io, csv, tempfile, zipfile, re, html
from typing import List, Dict, Any, Optional
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
    team: Optional[str] = None     # NEW: echo back filters used
    quarter: Optional[str] = None

state: Dict[str, Any] = {
    "docs": [],
    "store": None,                 # global index
    "team_stores": {},             # NEW: team -> FAISS
    "quarter_stores": {},          # NEW: quarter -> FAISS
    "teams": set(),                # NEW: discovered teams
    "quarters": set(),             # NEW: discovered quarters
    "splitter": RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150),
    "embeddings": None,
}

def _normalize_meta(meta_val: Any) -> str:
    return str(meta_val or "").strip()

def _build():
    docs = load_markdown_docs(OKR_DIR)
    state["docs"] = docs

    teams = set()
    quarters = set()
    for d in docs:
        teams.add(_normalize_meta(d["meta"].get("team")))
        quarters.add(_normalize_meta(d["meta"].get("quarter")))
    teams.discard("")      # clean empties
    quarters.discard("")
    state["teams"] = teams
    state["quarters"] = quarters

    splitter = state["splitter"]
    chunks, metadatas = [], []
    for d in docs:
        t = _normalize_meta(d["meta"].get("team"))
        q = _normalize_meta(d["meta"].get("quarter"))
        for c in splitter.split_text(d["text"]):
            chunks.append(c)
            metadatas.append({
                "path": d["path"], 
                "team": t, 
                "quarter": q,
                "plain_text": d.get("plain_text", "")  # Store plain text for sentence extraction
            })

    if state["embeddings"] is None:
        state["embeddings"] = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    # Global index
    state["store"] = FAISS.from_texts(chunks, state["embeddings"], metadatas=metadatas)

    # Build per-team stores (subset the same chunks)
    state["team_stores"] = {}
    for team in teams:
        team_texts = [c for c, m in zip(chunks, metadatas) if m.get("team") == team]
        team_mds   = [m for m in metadatas if m.get("team") == team]
        if team_texts:
            state["team_stores"][team] = FAISS.from_texts(team_texts, state["embeddings"], metadatas=team_mds)

    # Build per-quarter stores
    state["quarter_stores"] = {}
    for quarter in quarters:
        q_texts = [c for c, m in zip(chunks, metadatas) if m.get("quarter") == quarter]
        q_mds   = [m for m in metadatas if m.get("quarter") == quarter]
        if q_texts:
            state["quarter_stores"][quarter] = FAISS.from_texts(q_texts, state["embeddings"], metadatas=q_mds)

def _ensure_built():
    if state["store"] is None:
        _build()

def _normalize_team_param(team: Optional[str]) -> Optional[str]:
    """Normalize team parameter to match stored team names (case-insensitive)."""
    if not team:
        return None
    team_lower = team.lower()
    for t in state["teams"]:
        if t and t.lower() == team_lower:
            return t
    return team  # return original if no match found

def _normalize_quarter_param(quarter: Optional[str]) -> Optional[str]:
    """Normalize quarter parameter to match stored quarter names (case-insensitive)."""
    if not quarter:
        return None
    quarter_lower = quarter.lower()
    for q in state["quarters"]:
        if q and q.lower() == quarter_lower:
            return q
    return quarter  # return original if no match found

def _infer_filters_from_query(q: str) -> Dict[str, Optional[str]]:
    """Look for any known team/quarter names inside the query text (case-insensitive)."""
    q_low = q.lower()
    team_hit = None
    for t in state["teams"]:
        if t and t.lower() in q_low:
            team_hit = t
            break
    quarter_hit = None
    for qu in state["quarters"]:
        if qu and qu.lower() in q_low:
            quarter_hit = qu
            break
    return {"team": team_hit, "quarter": quarter_hit}

def _pick_store(team: Optional[str], quarter: Optional[str]):
    """
    Choose the most selective store:
    - if team & quarter: use team store, filter results by quarter afterward
    - if only team: team store
    - if only quarter: quarter store
    - else: global store
    """
    if team and team in state["team_stores"]:
        return state["team_stores"][team], "team"
    if quarter and quarter in state["quarter_stores"]:
        return state["quarter_stores"][quarter], "quarter"
    return state["store"], "global"

@app.get("/health")
def health():
    _ensure_built()
    return {
        "status": "ok",
        "docs": len(state["docs"]),
        "teams": sorted(list(state["teams"])),
        "quarters": sorted(list(state["quarters"])),
    }

@app.post("/refresh")
def refresh():
    _build()
    return {"status": "refreshed", "docs": len(state["docs"])}

@app.get("/search", response_model=List[Hit])
def search(
    q: str = Query(..., min_length=2),
    k: int = 5,
    team: Optional[str] = Query(None),        # NEW
    quarter: Optional[str] = Query(None),     # NEW
):
    _ensure_built()
    
    # Normalize team and quarter parameters to match stored names
    team = _normalize_team_param(team)
    quarter = _normalize_quarter_param(quarter)
    
    # auto-infer if not provided
    if not team and not quarter:
        guess = _infer_filters_from_query(q)
        team, quarter = team or guess["team"], quarter or guess["quarter"]

    store, mode = _pick_store(team, quarter)
    results = store.similarity_search(q, k=max(k*2, k))  # overfetch a bit

    # If both filters provided/guessed, post-filter to enforce both
    filtered = []
    for r in results:
        if team and r.metadata.get("team") != team:
            continue
        if quarter and r.metadata.get("quarter") != quarter:
            continue
        filtered.append(r)
        if len(filtered) >= k:
            break
    if not filtered:
        filtered = results[:k]

    out = []
    for r in filtered:
        snippet = r.page_content.strip()
        if len(snippet) > 400:
            snippet = snippet[:400] + "…"
        out.append(Hit(path=r.metadata.get("path", ""), snippet=snippet))
    return out

@app.get("/ask", response_model=AskResponse)
def ask(
    q: str = Query(..., min_length=2),
    k: int = 6,
    team: Optional[str] = Query(None),        # NEW
    quarter: Optional[str] = Query(None),     # NEW
):
    """
    Extractive answer with team/quarter filtering.
    """
    _ensure_built()
    
    # Normalize team and quarter parameters to match stored names
    team = _normalize_team_param(team)
    quarter = _normalize_quarter_param(quarter)
    
    # infer filters if not provided
    if not team and not quarter:
        guess = _infer_filters_from_query(q)
        team, quarter = team or guess["team"], quarter or guess["quarter"]

    store, mode = _pick_store(team, quarter)
    hits = store.similarity_search(q, k=max(k*2, k))

    # enforce both filters if both provided
    enforced = []
    for h in hits:
        if team and h.metadata.get("team") != team:
            continue
        if quarter and h.metadata.get("quarter") != quarter:
            continue
        enforced.append(h)
        if len(enforced) >= k:
            break
    if not enforced:
        enforced = hits[:k]

    # sentence extraction + ranking - convert HTML to plain text first
    sentences, meta_by_idx = [], []
    for h in enforced:
        # Simple HTML to text conversion for sentence extraction
        text_content = h.page_content.strip()
        # Remove HTML tags and decode HTML entities
        text_content = re.sub(r'<[^>]+>', ' ', text_content)
        text_content = html.unescape(text_content)
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        parts = re.split(r'(?<=[.!?])\s+', text_content)
        for s in parts:
            s = s.strip()
            if 40 <= len(s) <= 300:
                sentences.append(s)
                meta_by_idx.append(h.metadata.get("path", ""))

    if not sentences:
        return AskResponse(query=q, bullets=[], citations=[], team=team, quarter=quarter)

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
    for h in enforced[:min(5, len(enforced))]:
        snippet = h.page_content.strip()
        if len(snippet) > 300:
            snippet = snippet[:300] + "…"
        citations.append(Hit(path=h.metadata.get("path", ""), snippet=snippet))

    return AskResponse(query=q, bullets=bullets, citations=citations, team=team, quarter=quarter)

@app.get("/download")
def download(
    q: str = Query(..., min_length=2),
    k: int = 8,
    format: str = "zip",
    team: Optional[str] = Query(None),        # NEW
    quarter: Optional[str] = Query(None),     # NEW
):
    """
    Download matching OKR files (team/quarter aware).
    """
    _ensure_built()
    
    # Normalize team and quarter parameters to match stored names
    team = _normalize_team_param(team)
    quarter = _normalize_quarter_param(quarter)
    
    if not team and not quarter:
        guess = _infer_filters_from_query(q)
        team, quarter = team or guess["team"], quarter or guess["quarter"]

    store, mode = _pick_store(team, quarter)
    hits = store.similarity_search(q, k=max(k*2, k))

    # enforce both filters if needed
    enforced = []
    for h in hits:
        if team and h.metadata.get("team") != team:
            continue
        if quarter and h.metadata.get("quarter") != quarter:
            continue
        enforced.append(h)
        if len(enforced) >= k:
            break
    if not enforced:
        enforced = hits[:k]

    if format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["path", "team", "quarter", "snippet"])
        for h in enforced:
            snippet = h.page_content.strip().replace("\n", " ")
            writer.writerow([h.metadata.get("path", ""), h.metadata.get("team",""), h.metadata.get("quarter",""), snippet[:1000]])
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
            for h in enforced:
                rel_path = h.metadata.get("path", "unknown.md")
                if rel_path in added: continue
                added.add(rel_path)
                abs_path = os.path.join(OKR_DIR, rel_path)
                if os.path.exists(abs_path):
                    zf.write(abs_path, arcname=rel_path)
        return FileResponse(zip_path, filename="okrs.zip")

    raise HTTPException(status_code=400, detail="Unsupported format. Use 'zip' or 'csv'.")

# Static UI
app.mount("/ui", StaticFiles(directory="web", html=True), name="ui")
