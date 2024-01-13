FROM python:3.10

WORKDIR /code/app

COPY ./requirements.txt /code/requirements.txt

RUN pip install -r /code/requirements.txt

COPY ./app /code/app

ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0"]