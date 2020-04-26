# Dummy Sensor Project

Setup a dummy sensor that generates dummy water data which can be pushed to either the screen, a file, or MQTT.

## Getting Started

### Prerequisites

You will need Docker Compose and Docker installed.

### Installing

Use ```docker-compose``` to build the images:

```bash
docker compose build
```

### Sensor configuration

The sensor readings are configured in the ```wq-config.yaml``` file which is built into the container. If you want to add/remove sensors or changes sensor parameters, you need to edit this file and rebuild the image.

### Start the sensor and MQTT and push readings to MQTT

Use ```docker-compose``` to start up the MQTT server and start the dummy sensor. The dummy sensor will push data to MQTT in JSON format. The dummy-server service in the doocker-compose.yaml contains configuration parameters that you might want to change.

- **interval** This is the time in seconds between readings. Currently set to ```0.5``` = 2 readings per second.
- **count** This is the maximum number of readings before stopping. Currently set to ```-1``` for infinite readings
- **mqtt_topic** This is the MQTT topic that the sensor readings will be published to. Currently set to ```topic/dummy-sensor```

```bash
docker-compose up -d
```

Use a mosquitto client (eg. [Eclipse Mosquitto](https://mosquitto.org/)) to check that the duumy sensor is ending readings.

```bash
mosquitto_sub -p 1883 -t topic/dummy-sensor
```

And you can stop it by:

```bash
docker-compose down
```

### Start the sensor directly

Alternatively, you can run the sensor directly from your Python virtual environment:

```bash
pip install -r requirements.txt

# Output readings to screen
python dummy-sensor.py -c wq-config.yaml --interval 0.1 --count 30

# Output readings to file
python dummy-sensor.py -c wq-config.yaml --interval 0.1 --count 30 -o wq-data.txt

# Output readings to a locally available MQTT server
python dummy-sensor.py -c wq-config.yaml --interval 0.1 --count 30 --mqtt-topic topic/dummy-sensor --mqtt-hostname localhost --mqtt-port 1833
```
