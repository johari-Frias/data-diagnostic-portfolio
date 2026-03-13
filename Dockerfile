# ──────────────────────────────────────────────────────────────────────────────
# Dockerfile – Data Diagnostic Dashboard (Streamlit)
# ──────────────────────────────────────────────────────────────────────────────
# Build:  docker build -t data-diagnostic-dashboard .
# Run:    docker run -p 8501:8501 data-diagnostic-dashboard
# ──────────────────────────────────────────────────────────────────────────────

# ── Stage: production image ──────────────────────────────────────────────────
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── Install system dependencies required by some Python packages ─────────────
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# ── Install Python dependencies (cached unless requirements.txt changes) ─────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Copy application code ───────────────────────────────────────────────────
COPY app.py .
COPY src/ ./src/

# ── Expose the default Streamlit port ────────────────────────────────────────
EXPOSE 8501

# ── Health check – used by Docker / ECS / ALB to verify the container ────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# ── Launch Streamlit bound to 0.0.0.0 so the AWS load balancer can reach it ─
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
