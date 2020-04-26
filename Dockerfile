FROM python:alpine3.7

COPY . /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD [ "python", "dummy-sensor.py", "-c", "logan-config.yaml" ]