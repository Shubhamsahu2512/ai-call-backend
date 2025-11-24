# ---------------- Base image ----------------
FROM python:3.13-slim

# ---------------- System dependencies ----------------
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libffi-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ---------------- Working directory ----------------
WORKDIR /app

# ---------------- Copy project files ----------------
COPY main.py .
COPY requirements.txt .

# ---------------- Install Python dependencies ----------------
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# ---------------- Environment variables ----------------
# (You can also set these in Render dashboard)
ENV PYTHONUNBUFFERED=1

# ---------------- Run FastAPI ----------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
