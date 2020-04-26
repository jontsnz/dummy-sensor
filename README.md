# Dummy Sensor Project

Setup a dummy sensor that can generate dummy water data. Data can be pushed to screen or to file.

## Getting Started

### Prerequisites

You will need docker installed.

### Installing

Use docker to build the image:

```bash
docker build --rm -t dummy-sensor:latest "."
```

### Starting the sensor

The sensor readings are configured in the ```logan-config.yaml``` file which is built into the container. If you want to add/remove sensors or changes sensor parameters, you need to edit this file and rebuild the image.

On the command line, you can set the **interval** (time in seconds between readings, defaults to 0.2) and the **count** (maximum number of readings before stooping, use -1 for infinite readings).

```bash
docker run --rm -it --name dummy-sensor dummy-sensor:latest --interval 0.1 --count 30
```
