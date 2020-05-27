"""Sensor Random Data Generator

This script generates random sensor data based on the configuration file.
Output can be sent to the screen, a CVS file, or an MQTT topic.
"""

import os
import sys
import argparse
import yaml
import random
import time
from datetime import datetime
from datetime import timedelta
from abc import ABC, abstractmethod
import csv
import json
import paho.mqtt.client as mqtt
import logging

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ReadingsOutputter(ABC):
    """Abstract readings output class
    """

    @abstractmethod
    def output(self, readings):
        """ Implement this method to write readings somewhere
        """
        pass

class ScreenJsonOutputter(ReadingsOutputter):
    """Class for sending readings to the screen in JSON format
    """

    def __init__(self):
        super().__init__()
    
    def output(self, readings):
        logger.info(json.dumps(dict(readings)))

class CSVOutputter(ReadingsOutputter):
    """ Class for sending readings to a CSV file
    """

    def __init__(self, filename):
        """Initialise class

        Parameters
        ----------
        filename : str
            The name of the CSV file to create
        """
        super().__init__()
        self._csvfile = csv.writer(open(filename, 'w'), quoting = csv.QUOTE_NONNUMERIC)
        self._first_line = True

    def output(self, readings):
        logger.info('Writing line to CSV file...%s' % (readings[0][1]))
        if self._first_line:
            self._csvfile.writerow(t[0] for t in readings)
            self._first_line = False
        self._csvfile.writerow(t[1] for t in readings)

class MqttOutputter(ReadingsOutputter):
    """ Class for sending readings to an MQTT topic
    """

    def __init__(self, host, port, topic):
        """Initialise class

        Parameters
        ----------
        host : str
            MQTT host name
        port : int
            MQTT port
        topic : str
            MQTT topic where readings will be pushed to
        """
        super().__init__()
        self._client = mqtt.Client()
        self._topic = topic
        keepalive = 60
        self._client.connect(host,port,keepalive)
        self.silent = False
 
    def output(self, readings):
        if not self.silent:
            logger.info('Pushing readings to MQTT...%s' % (readings[0][1]))
        self._client.publish(self._topic,json.dumps(dict(readings)))

    def __del__(self):
        """Class destructor. Clean up MQTT connection.
        """
        self._client.disconnect()

class Station:
    """ This class defines a sensor station that has a
        name and may contain 1 or more sensors.    
    """

    def __init__(self, station_config):
        """Class initialise.

        Parameters
        ----------
        station_config : dict
            Dictionary containing station configuration (including sensors)
        """
        self.station_name = station_config['station_name']
        self.sensors = []
        for sensor_config in station_config['sensors']:
            self.sensors.append(Sensor(sensor_config))

class Sensor:
    """This class defines a given sensor: its name, possible values and precision.
    """

    def __init__(self, sensor_config):
        """Class initialise. 

        Parameters
        ----------
        sensor_config : dict
            Configuration for this sensor
        """
        self.name = list(sensor_config.keys())[0]
        self._min = sensor_config[self.name]['min']
        self._max = sensor_config[self.name]['max']
        self.reading = sensor_config[self.name]['start']
        self._last_direction = 1
        self._dp = sensor_config[self.name]['dp']
        self._max_step = sensor_config[self.name]['max_step']

    def generate_reading(self):
        """Generate a single reading for this sensor

        Returns
        -------
        float
            A randomly geerated reading for this sensor
        """
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
    """Continuosly generate readings for a station and send them to the outputter.
        This method will run forever if no interatio limit is provided.

    Parameters
    ----------
    config : dict
        Dictionary containing station configuration (including sensors)
    interval_secs : int
        How many seconds to wait between each generated reading
    max_iterations : int
        How many readings to generate before stopping. Never stops if -1.
    outputter : obj
        The ReadingsOutputter to send sensor readings to
    """
    station = Station(config['station'])
    logger.info('Generating %d readings for station: %s' % (max_iterations, station.station_name))
    cnt = 0
    while (cnt < max_iterations) or (max_iterations == -1):
        cnt += 1
        timestamp = datetime.now().strftime(config['settings']['timestamp_format'])
        readings = [('TIMESTAMP', timestamp),('RECORD', cnt),('Station', station.station_name)]
        readings.extend([(s.name, s.generate_reading()) for s in station.sensors])
        outputter.output(readings)
        time.sleep(intervals_secs)

def generate_backfill_readings(config, intervals_secs, outputter, from_date):
    """Generate backdated sensor readings for a station from a given date until now

    Parameters
    ----------
    config : dict
        Dictionary containing station configuration (including sensors)
    interval_secs : int
        How many seconds between each generated reading
    outputter : obj
        The ReadingsOutputter to send sensor readings to
    from_date : date
        The starting date to generate readings from
    """
    station = Station(config['station'])
    logger.info('Generating backfill readings for station: %s since %s' % (station.station_name, from_date))
    cnt = 0
    next_time = from_date
    while (next_time < datetime.now()):
        cnt += 1
        if cnt % 1000 == 0:
            logger.info('Date %s, count=%d' % (next_time, cnt))
        timestamp = next_time.strftime(config['settings']['timestamp_format'])
        readings = [('TIMESTAMP', timestamp),('RECORD', cnt),('Station', station.station_name)]
        readings.extend([(s.name, s.generate_reading()) for s in station.sensors])
        outputter.output(readings)
        next_time = next_time + timedelta(seconds=intervals_secs)

def main(arguments):
    """Main method"""

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
    parser.add_argument('--backfill_from', help="Backfill readings starting from this date eg. 2020-01-31", required=False)
    args = parser.parse_args(arguments)
    config = None

    if args.configfile:
        with open(args.configfile) as config_file:
            try:
                config = yaml.safe_load(config_file)
            except yaml.YAMLError as exc:
                logger.exception(exc)
    else:
        logger.error('Config file must be provided')

    if not config:
        sys.exit(1)

    if args.mqtt_topic:
        host = args.mqtt_hostname
        port = args.mqtt_port
        topic = args.mqtt_topic
        logger.info('Sending output to MQTT %s:%s on %s' % (host, port, topic))
        outputter = MqttOutputter(host, port, topic)
    elif args.outputfile:
        logger.info('Sending output to file %s' % args.outputfile)
        outputter = CSVOutputter(args.outputfile)
    else:
        logger.info('Sending output to screen')
        outputter = ScreenJsonOutputter()

    if config:
        if args.backfill_from:
            from_date = datetime.strptime(args.backfill_from, '%Y-%m-%d')
            logger.info('Back-filling data from %s' % from_date)
            outputter.silent = True
            generate_backfill_readings(config, args.interval, outputter, from_date)
            logger.info('Back-fill completed')
        else:
            # Kick off sensor data generation loop
            generate_readings(config, args.interval, args.count, outputter)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
