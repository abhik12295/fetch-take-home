FROM python:3.8

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install psycopg2-binary
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "fetch.py"]