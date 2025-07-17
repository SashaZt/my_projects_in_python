# client/Dockerfile
FROM python:3.12-slim

WORKDIR /client

RUN apt-get update

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]