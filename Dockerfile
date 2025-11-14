FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    tk \
    libgl1 \
    libglib2.0-0 \
    libxext6 \
    libxrender1 \
    libsm6 \
    libice6 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY _main.py /app/_main.py

CMD ["python", "_main.py"]
