# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    glpk-utils \
    libglpk-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the working directory
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
