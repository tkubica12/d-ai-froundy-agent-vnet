# Dockerfile for Products MCP Server (Production Single-Stage)
# Uses uv for fast, reliable dependency management
# Single-stage build for simpler deployment and faster rebuilds

FROM python:3.12-slim

WORKDIR /app

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    PORT=8080

# Copy dependency files first (for layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies using uv (frozen lockfile, no dev dependencies)
RUN uv sync --frozen --no-dev

# Copy application code
COPY *.py ./

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port (for SSE transport if needed)
EXPOSE 8080

# Health check - verify critical dependencies
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD uv run python -c "import fastmcp; import azure.cosmos; import sys; sys.exit(0)" || exit 1

# Run the MCP server
CMD ["uv", "run", "python", "main.py"]
