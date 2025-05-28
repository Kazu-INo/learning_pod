# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files and required files for build
COPY pyproject.toml LICENSE README.md ./
COPY src/ ./src/

# Install dependencies using uv
RUN uv pip install --system -e .

# Stage 2: Runtime
FROM python:3.11-slim

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy Python environment from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy source code and required files
COPY src/ ./src/
COPY pyproject.toml LICENSE README.md ./

# Install the package in development mode
RUN pip install -e .

# Create outputs directory
RUN mkdir -p outputs

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Set entrypoint and default command
ENTRYPOINT ["learnpod"]
CMD ["--help"] 