# Dockerfile for building the autonomous AI agents project

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt requirements-dev.txt pyproject.toml setup.cfg ./
# copy each package directory preserving its name
# copy each package directory preserving its folder name
COPY ai_tpm_agent /app/ai_tpm_agent
COPY ai_multi_agent /app/ai_multi_agent
COPY ai_org_agent /app/ai_org_agent
COPY market_ops /app/market_ops
COPY run_agent.py cli.py ./

# install in editable mode plus runtime deps
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt && \
    python -m pip install -e . && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# default entrypoint launches the Market Ops API; command-line args can override
ENTRYPOINT ["python", "-m", "market_ops.cli", "api"]
