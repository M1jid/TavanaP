FROM python:3.11-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip install --no-cache-dir aiokafka
RUN pip install --no-cache-dir pydantic_settings
RUN pip install --no-cache-dir sqlalchemy
RUN pip install --no-cache-dir psycopg2-binary

COPY . /code/

EXPOSE 8000

CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "8000"]
