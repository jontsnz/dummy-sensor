FROM python:3

ADD dummy-sensor.py /
ADD logan-config.yaml /

RUN pip install pyyaml

CMD [ "python", "dummy-sensor.py", "-c", "logan-config.yaml" ]