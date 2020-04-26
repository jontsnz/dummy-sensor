"""Sensor Random Data Generator
"""

import os
import sys
import argparse
import yaml
import random
import time
from datetime import datetime
from abc import ABC, abstractmethod
import csv
import json
import paho.mqtt.client as mqtt

class ReadingsOutputter(ABC):

    @abstractmethod
    def output(self, readings):
        pass

class ScreenJsonOutputter(ReadingsOutputter):

    def __init__(self):
        super().__init__()
    
    def output(self, readings):
        print(json.dumps(dict(readings)))

class CSVOutputter(ReadingsOutputter):

    def __init__(self, filename):
        super().__init__()
        self._csvfile = csv.writer(open(filename, 'w'), quoting = csv.QUOTE_NONNUMERIC)
        self._first_line = True

    def output(self, readings):
        print('Writing line to CSV file...%s' % (readings[0][1]))
        if self._first_line:
            self._csvfile.writerow(t[0] for t in readings)
            self._first_line = False
        self._csvfile.writerow(t[1] for t in readings)

class MqttOutputter(ReadingsOutputter):

    def __init__(self, host, port, topic):
        super().__init__()
        self._client = mqtt.Client()
        self._topic = topic
        keepalive = 60
        self._client.connect(host,port,keepalive)

    def output(self, readings):
        print('Pushing readings to MQTT...%s' % (readings[0][1]))
        self._client.publish(self._topic,json.dumps(dict(readings)))

    def __del__(self):
        self._client.disconnect()

class Station:
    def __init__(self, station_config):
        self.station_name = station_config['station_name']
        self.sensors = []
        for sensor_config in station_config['sensors']:
            self.sensors.append(Sensor(sensor_config))

class Sensor:
    def __init__(self, sensor_config):
        self.name = list(sensor_config.keys())[0]
        self._min = sensor_config[self.name]['min']
        self._max = sensor_config[self.name]['max']
        self.reading = sensor_config[self.name]['start']
        self._last_direction = 1
        self._dp = sensor_config[self.name]['dp']
        self._max_step = sensor_config[self.name]['max_step']

    def generate_reading(self):
        step = self._max_step * random.random()
        if random.random() < 0.9:
            direction = self._last_direction
        else:
            direction = -1 * self._last_direction
        if (self.reading + (step * direction) > self._max) or (self.reading + (step * direction) < self._min):
            direction = -1 * direction
        reading = round(self.reading + (step * direction),self._dp)
        reading = min(max(reading, self._min), self._max)
        self.reading = reading
        self._last_direction = direction
        return reading

def generate_readings(config, intervals_secs, max_iterations, outputter):
    station = Station(config['station'])
    print('Generating %d readings for station: %s' % (max_iterations, station.station_name))
    cnt = 0
    while (cnt < max_iterations) or (max_iterations == -1):
        cnt += 1
        timestamp = datetime.now().strftime(config['settings']['timestamp_format'])
        readings = [('TIMESTAMP', timestamp),('RECORD', cnt),('Station', station.station_name)]
        readings.extend([(s.name, s.generate_reading()) for s in station.sensors])
        outputter.output(readings)
        time.sleep(intervals_secs)

def main(arguments):

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-c', '--configfile', help="Config file")
    parser.add_argument('-o', '--outputfile', help="Output file", required=False)
    parser.add_argument('--interval', help="Intervals (seconds)", required=False, type=float ,default=0.5)
    parser.add_argument('--count', help="Number of readings (-1 = infinite)", required=False, type=float, default=5)
    parser.add_argument('--mqtt_topic', help="The MQTT topic to publish", required=False)
    parser.add_argument('--mqtt_hostname', help="The MQTT hostname", required=False, default='localhost')
    parser.add_argument('--mqtt_port', help="The MQTT port", required=False, type=int, default=1883)
    args = parser.parse_args(arguments)

    if args.configfile:
        with open(args.configfile) as config_file:
            try:
                config = yaml.safe_load(config_file)
            except yaml.YAMLError as exc:
                print(exc)
    else:
        print('Config file must be provided')

    if args.mqtt_topic:
        host = args.mqtt_hostname
        port = args.mqtt_port
        topic = args.mqtt_topic
        print('Sending output to MQTT %s:%s on %s' % (host, port, topic))
        outputter = MqttOutputter(host, port, topic)
    elif args.outputfile:
        print('Sending output to file %s' % args.outputfile)
        outputter = CSVOutputter(args.outputfile)
    else:
        outputter = ScreenJsonOutputter()

    if config:
        generate_readings(config, args.interval, args.count, outputter)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
