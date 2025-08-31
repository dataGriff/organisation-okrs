FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY web ./web

ENV OKR_DIR=/data/okrs
ENV EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
EXPOSE 8000

VOLUME ["/data/okrs", "/root/.cache/huggingface"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
