FROM python:3.12-slim as base

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
  gcc \
  g++ \
  pkg-config \
  libheif-dev \
  libde265-dev \
  libx265-dev \
  && rm -rf /var/lib/apt/lists/*

FROM base as builder

# Copy requirements file
COPY requirements.txt .

# Create wheels
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

FROM base

# Copy wheels from builder stage and install
COPY --from=builder /app/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links /wheels -r requirements.txt \
  && rm -rf /wheels

# Copy application code
COPY src/ ./src/
COPY compress.py .

# Create uploads directory
RUN mkdir -p uploads

# Set environment variables
ENV FLASK_ENV=production
ENV PORT=5000
ENV UPLOAD_FOLDER=uploads

# Expose port
EXPOSE 5000

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/ || exit 1

# Run the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "src.app:app"]
