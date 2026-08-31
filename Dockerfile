# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Keep Python output unbuffered (logs show up immediately on Render) and
# stop pip from writing .pyc cache files into the image.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first so this layer is cached unless requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the app. .env is deliberately excluded via .dockerignore —
# real keys are injected as Render environment variables at runtime, never baked
# into the image.
COPY . .

# Render assigns the external port dynamically via $PORT — do not hardcode 8501.
# Locally (docker run without -e PORT), it falls back to 8501.
ENV PORT=8501
EXPOSE 8501

# Shell form so $PORT is expanded at container start (exec form CMD does not do this).
CMD streamlit run app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
