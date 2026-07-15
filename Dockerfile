FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak-ng \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Set UTF-8 locale (fixes silent C++ espeak-ng failures with non-ASCII text)
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Set espeak-ng data path so piper-phonemize can find it
ENV ESPEAK_DATA_PATH=/usr/lib/x86_64-linux-gnu/espeak-ng-data

# Expose port
EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
