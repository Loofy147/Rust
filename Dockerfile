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

# Copy and install the built wheel
COPY --from=build /app/ReasoningAgent/target/wheels/*.whl /tmp/
RUN pip install /tmp/*.whl fastapi uvicorn pydantic sqlalchemy slowapi

# Copy FastAPI app
COPY ./api /app/api
WORKDIR /app/api

# Expose port
EXPOSE 8000

# Healthcheck for orchestration
HEALTHCHECK CMD curl --fail http://localhost:8000/metrics || exit 1

# Start FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]