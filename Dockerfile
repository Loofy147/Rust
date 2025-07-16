# --- Stage 1: Build Rust extension as Python wheel ---
FROM python:3.12-slim AS build

# Install system dependencies for Rust and Python
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libssl-dev \
        pkg-config \
        curl \
        git \
        ca-certificates \
        && rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:$PATH"

# Install maturin
RUN pip install maturin

# Copy Rust project
COPY ./ReasoningAgent /app/ReasoningAgent
WORKDIR /app/ReasoningAgent

# Build Python wheel
RUN maturin build --release --strip

# --- Stage 2: Runtime ---
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends libssl-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy built wheel from build stage
COPY --from=build /app/ReasoningAgent/target/wheels/*.whl ./

# Install FastAPI, Uvicorn, SQLAlchemy, slowapi, prometheus, celery, redis, and the Rust extension
RUN pip install *.whl fastapi uvicorn sqlalchemy pydantic slowapi prometheus_fastapi_instrumentator prometheus_client celery redis

# Copy API code
COPY ./api ./api

# Expose port
EXPOSE 8000

# Entrypoint for API (default)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Entrypoint for Celery worker (override in docker-compose)
# CMD ["celery", "-A", "api.worker", "worker", "--loglevel=info"]