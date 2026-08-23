FROM python:3.11-slim

WORKDIR /app

COPY pull-username.py .
RUN pip install --no-cache-dir requests nats-py

CMD ["python", "pull-username.py"]
