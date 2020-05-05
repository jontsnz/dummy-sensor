FROM python:alpine3.7

ENV PYTHONUNBUFFERED 1

COPY . /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ARG mqtt_topic
ENV MQTT_TOPIC=$mqtt_topic
RUN echo "MQTT_TOPIC: $mqtt_topic"
ARG mqtt_hostname
ENV MQTT_HOSTNAME=$mqtt_hostname
RUN echo "MQTT_HOSTNAME: $mqtt_hostname"
ARG mqtt_port
ENV MQTT_PORT=$mqtt_port
RUN echo "MQTT_PORT: $mqtt_port"
ARG interval
ENV INTERVAL=$interval
RUN echo "INTERVAL: $interval"
ARG count
ENV COUNT=$count
RUN echo "COUNT: $count"

CMD ["sh", "-c", "echo $INTERVAL; echo $COUNT; echo $MQTT_TOPIC; echo $MQTT_HOSTNAME; echo $MQTT_PORT; python dummy-sensor.py -c wq-config.yaml --count $COUNT --interval $INTERVAL --mqtt_topic $MQTT_TOPIC --mqtt_hostname $MQTT_HOSTNAME --mqtt_port $MQTT_PORT"]
