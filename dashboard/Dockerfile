FROM python:3.13-slim

WORKDIR /app

# install compiler + libs
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential libfreetype6-dev libpng-dev libjpeg-dev \
      libopenblas-dev liblapack-dev gfortran \
    && rm -rf /var/lib/apt/lists/*

COPY dashboard.py .
COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

CMD ["streamlit","run","dashboard.py","--server.port=8501","--server.address=0.0.0.0"]
