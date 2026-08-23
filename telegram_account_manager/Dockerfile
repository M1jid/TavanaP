FROM python:3.11-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --proxy http://192.168.10.53:10809 --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./ /code

EXPOSE 9000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
