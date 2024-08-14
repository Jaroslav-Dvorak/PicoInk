# SPDX-FileCopyrightText: Copyright (c) 2023 Jose D. Montoya
#
# SPDX-License-Identifier: MIT
"""
`sht4x`
================================================================================

MicroPython Driver fot the Sensirion Temperature and Humidity SHT40, SHT41 and SHT45 Sensor


* Author: Jose D. Montoya

"""

import time
import struct
import json
from micropython import const
from collections import OrderedDict

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/jposada202020/MicroPython_SHT4X.git"

_RESET = const(0x94)

HIGH_PRECISION = const(0)
MEDIUM_PRECISION = const(1)
LOW_PRECISION = const(2)
temperature_precision_options = (HIGH_PRECISION, MEDIUM_PRECISION, LOW_PRECISION)
temperature_precision_values = {
    HIGH_PRECISION: const(0xFD),
    MEDIUM_PRECISION: const(0xF6),
    LOW_PRECISION: const(0xE0),
}

HEATER200mW = const(0)
HEATER110mW = const(1)
HEATER20mW = const(2)
heater_power_values = (HEATER200mW, HEATER110mW, HEATER20mW)

TEMP_1 = const(0)
TEMP_0_1 = const(1)
heat_time_values = (TEMP_1, TEMP_0_1)

wat_config = {
    HEATER200mW: (0x39, 0x32),
    HEATER110mW: (0x2F, 0x24),
    HEATER20mW: (0x1E, 0x15),
}


class SHT4X:
    """Driver for the SHT4X Sensor connected over I2C.

    :param ~machine.I2C i2c: The I2C bus the SHT4X is connected to.
    :param int address: The I2C device address. Defaults to :const:`0x44`

    :raises RuntimeError: if the sensor is not found

    **Quickstart: Importing and using the device**

    Here is an example of using the :class:`SHT4X` class.
    First you will need to import the libraries to use the sensor

    .. code-block:: python

        from machine import Pin, I2C
        from micropython_sht4x import sht4x

    Once this is done you can define your `machine.I2C` object and define your sensor object

    .. code-block:: python

        i2c = I2C(1, sda=Pin(2), scl=Pin(3))
        sht = sht4x.SHT4X(i2c)

    Now you have access to the attributes

    .. code-block:: python

        temp = sht.temperature
        hum = sht.relative_humidity

    """

    def __init__(self, i2c, filename, address: int = 0x44) -> None:
        self._i2c = i2c
        self._address = address
        self._data = bytearray(6)

        self._command = 0xFD
        self._temperature_precision = LOW_PRECISION
        self._heater_power = HEATER20mW
        self._heat_time = TEMP_0_1

        self.filename = filename
        self.settings = self.settings_load()
        self.displ_min = self.settings["Minimum"]
        self.displ_max = self.settings["Maximum"]
        self.offset = self.settings["Offset"]

        self.units_classes = {
            "temperature": ("°C", "temperature"),
            "humidity": ("%", "humidity")
        }
        self.last_values = OrderedDict()

    @property
    def temperature_precision(self) -> str:
        """
        Sensor temperature_precision

        +------------------------------------+------------------+
        | Mode                               | Value            |
        +====================================+==================+
        | :py:const:`sht4x.HIGH_PRECISION`   | :py:const:`0`    |
        +------------------------------------+------------------+
        | :py:const:`sht4x.MEDIUM_PRECISION` | :py:const:`1`    |
        +------------------------------------+------------------+
        | :py:const:`sht4x.LOW_PRECISION`    | :py:const:`2`    |
        +------------------------------------+------------------+

        """
        values = ("HIGH_PRECISION", "MEDIUM_PRECISION", "LOW_PRECISION")
        return values[self._temperature_precision]

    @temperature_precision.setter
    def temperature_precision(self, value: int) -> None:
        if value not in temperature_precision_values:
            raise ValueError("Value must be a valid temperature_precision setting")
        self._temperature_precision = value
        self._command = temperature_precision_values[value]

    @property
    def relative_humidity(self) -> float:
        """
        The current relative humidity in % rH
        The RH conversion formula (1) allows values to be reported
        which are outside the range of 0 %RH … 100 %RH. Relative
        humidity values which are smaller than 0 %RH and larger than
        100 %RH are non-physical, however these “uncropped” values might
        be found beneficial in some cases (e.g. when the distribution of
        the sensors at the measurement boundaries are of interest)
        """
        return self.measurements[1]

    @property
    def temperature(self) -> float:
        """The current temperature in Celsius"""
        return self.measurements[0]

    @property
    def measurements(self):
        """both `temperature` and `relative_humidity`, read simultaneously
        If you use the heater function, sensor will be not give a response
        back. Waiting time is added to the logic to account for this situation
        """

        self._i2c.writeto(self._address, bytes([self._command]), False)
        if self._command in (0x39, 0x2F, 0x1E):
            time.sleep(1.2)
        elif self._command in (0x32, 0x24, 0x15):
            time.sleep(0.2)
        time.sleep(0.2)
        self._i2c.readfrom_into(self._address, self._data)

        temperature, temp_crc, humidity, humidity_crc = struct.unpack_from(
            ">HBHB", self._data
        )

        if temp_crc != self._crc(
                memoryview(self._data[0:2])
        ) or humidity_crc != self._crc(memoryview(self._data[3:5])):
            raise RuntimeError("Invalid CRC calculated")

        temperature = -45.0 + 175.0 * temperature / 65535.0

        humidity = -6.0 + 125.0 * humidity / 65535.0
        humidity = max(min(humidity, 100), 0)

        return temperature, humidity

    @staticmethod
    def _crc(buffer) -> int:
        """verify the crc8 checksum"""
        crc = 0xFF
        for byte in buffer:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1
        return crc & 0xFF

    @property
    def heater_power(self) -> str:
        """
        Sensor heater power
        The sensor has a heater. Three heating powers and two heating
        durations are selectable.
        The sensor executes the following procedure:
        1. The heater is enabled, and the timer starts its count-down.
        2. Measure is taken after time is up
        3. After the measurement is finished the heater is turned off.
        4. Temperature and humidity values are now available for readout.
        The maximum on-time of the heater commands is one second in order
        to prevent overheating

        +-------------------------------+---------------+
        | Mode                          | Value         |
        +===============================+===============+
        | :py:const:`sht4x.HEATER200mW` | :py:const:`0` |
        +-------------------------------+---------------+
        | :py:const:`sht4x.HEATER110mW` | :py:const:`1` |
        +-------------------------------+---------------+
        | :py:const:`sht4x.HEATER20mW`  | :py:const:`2` |
        +-------------------------------+---------------+

        """
        values = ("HEATER200mW", "HEATER110mW", "HEATER20mW")
        return values[self._heater_power]

    @heater_power.setter
    def heater_power(self, value: int) -> None:
        if value not in heater_power_values:
            raise ValueError("Value must be a valid heater power setting")
        self._heater_power = value
        self._command = wat_config[value][self._heat_time]

    @property
    def heat_time(self) -> str:
        """
        Sensor heat_time
        The sensor has a heater. Three heating powers and two heating
        durations are selectable.
        The sensor executes the following procedure:
        1. The heater is enabled, and the timer starts its count-down.
        2. Measure is taken after time is up
        3. After the measurement is finished the heater is turned off.
        4. Temperature and humidity values are now available for readout.
        The maximum on-time of the heater commands is one second in order
        to prevent overheating

        +----------------------------+---------------+
        | Mode                       | Value         |
        +============================+===============+
        | :py:const:`sht4x.TEMP_1`   | :py:const:`0` |
        +----------------------------+---------------+
        | :py:const:`sht4x.TEMP_0_1` | :py:const:`1` |
        +----------------------------+---------------+
        """
        values = ("TEMP_1", "TEMP_0_1")
        return values[self._heat_time]

    @heat_time.setter
    def heat_time(self, value: int) -> None:
        if value not in heat_time_values:
            raise ValueError("Value must be a valid heat_time setting")
        self._heat_time = value
        self._command = wat_config[self._heater_power][value]

    def reset(self):
        """
        Reset the sensor
        """
        self._i2c.writeto(self._address, bytes([_RESET]), False)
        time.sleep(0.1)

    @property
    def info(self):
        temperature_humidity = self.measurements
        if temperature_humidity:
            temperature, humidity = temperature_humidity
            return "{:3.1f}C  {:3.1f}%".format(temperature, humidity)
        else:
            return None

    def get_values(self):
        temperature_humidity = self.measurements
        print(temperature_humidity)
        if temperature_humidity is None:
            return None
        temperature, humidity = temperature_humidity
        temperature += self.offset
        self.last_values["temperature"] = temperature
        self.last_values["humidity"] = humidity
        return True

    def settings_load(self):
        settings = OrderedDict()
        try:
            with open(self.filename, "r") as f:
                settings = f.read()
                settings = json.loads(settings)
            settings["Minimum"] = int(settings["Minimum"])
            settings["Maximum"] = int(settings["Maximum"])
            settings["Offset"] = float(str(settings["Offset"]).replace(",", "."))
        except Exception as e:
            print(e)
            settings["Minimum"] = 15
            settings["Maximum"] = 30
            settings["Offset"] = 0.0
        finally:
            return settings

    def settings_save(self):
        with open(self.filename, "w") as f:
            f.write(json.dumps(self.settings))

    def get_ble_characteristics(self):
        battery = b'\x01' + struct.pack("<B", self.last_values["soc"])
        temperature = b'\x02' + struct.pack("<h", int(self.last_values["temperature"]*100))
        humidity = b'\x03' + struct.pack("<h", int(self.last_values["humidity"]*100))

        characteristics = battery + temperature + humidity
        return characteristics
