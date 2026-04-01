# Use a lightweight Python base
FROM python:3.12-slim

# Install uv directly from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1

# Install dependencies first (better caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copy your source code
COPY . .

# Install the project
RUN uv sync --frozen --no-dev

# Set the path to use the virtualenv created by uv
ENV PATH="/app/.venv/bin:$PATH"

# Default port for Render (though the YAML will specify commands)
EXPOSE 10000

# Default command (used by the 'web' service)
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "10000"]