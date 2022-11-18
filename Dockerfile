FROM python:3.8-slim

ENV PYTHONUNBUFFERED True

ENV APP_HOME /app
ENV PORT 8080
WORKDIR $APP_HOME
COPY . ./

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app