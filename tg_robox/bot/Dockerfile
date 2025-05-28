# bot/Dockerfile
FROM python:3.12-slim

WORKDIR /bot

RUN apt-get update 

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . /bot


CMD ["python", "main.py"]