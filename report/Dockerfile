FROM python:3.11-slim

WORKDIR /code

COPY report/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir aiokafka
RUN pip install --no-cache-dir redis

COPY report/ /code
COPY utils /code/utils
COPY .env /code/.env

EXPOSE 8000

# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "/code/privkey.pem", "--ssl-certfile", "/code/fullchain.pem"]
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers=4", "--certfile=/code/fullchain.pem", "--keyfile=/code/privkey.pem", "--timeout", "120"]
