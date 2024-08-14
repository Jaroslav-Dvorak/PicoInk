import time
import struct
from collections import OrderedDict
from micropython import const

SCD4X_DEFAULT_ADDR = 0x62
_SCD4X_REINIT = const(0x3646)
_SCD4X_FACTORYRESET = const(0x3632)
_SCD4X_FORCEDRECAL = const(0x362F)
_SCD4X_SELFTEST = const(0x3639)
_SCD4X_DATAREADY = const(0xE4B8)
_SCD4X_STOPPERIODICMEASUREMENT = const(0x3F86)
_SCD4X_STARTPERIODICMEASUREMENT = const(0x21B1)
_SCD4X_STARTLOWPOWERPERIODICMEASUREMENT = const(0x21AC)
_SCD4X_READMEASUREMENT = const(0xEC05)
_SCD4X_SERIALNUMBER = const(0x3682)
_SCD4X_GETTEMPOFFSET = const(0x2318)
_SCD4X_SETTEMPOFFSET = const(0x241D)
_SCD4X_GETALTITUDE = const(0x2322)
_SCD4X_SETALTITUDE = const(0x2427)
_SCD4X_SETPRESSURE = const(0xE000)
_SCD4X_PERSISTSETTINGS = const(0x3615)
_SCD4X_GETASCE = const(0x2313)
_SCD4X_SETASCE = const(0x2416)
_SCD4X_MEASURESINGLESHOT = const(0x219D)
_SCD4X_MEASURESINGLESHOTRHTONLY = const(0x2196)


class SCD4X:
    """
    Based on https://github.com/adafruit/Adafruit_CircuitPython_SCD4X
    Copyright (c) 2021 ladyada for Adafruit Industries
    MIT License
    """
    def __init__(self, i2c_bus, address=SCD4X_DEFAULT_ADDR):
        self.i2c = i2c_bus
        self.address = address
        self._buffer = bytearray(18)
        self._cmd = bytearray(2)
        self._crc_buffer = bytearray(2)

        # cached readings
        self._temperature = None
        self._relative_humidity = None
        self._co2 = None

        self._settings = {"Altitude": None, "Tmp-offset": None}
        self.displ_min = 400
        self.displ_max = 5000

        self.units_classes = {"co2": ("ppm", "carbon_dioxide"),
                              "temperature": ("°C", "temperature"),
                              "humidity": ("%", "humidity"),
                              }
        self.last_values = {}

        self.stop_periodic_measurement()

    @property
    def co2(self):
        """Returns the CO2 concentration in PPM (parts per million)
        .. note::
            Between measurements, the most recent reading will be cached and returned.
        """
        if self.data_ready:
            self._read_data()
        return self._co2

    @property
    def temperature(self):
        """Returns the current temperature in degrees Celsius
        .. note::
            Between measurements, the most recent reading will be cached and returned.
        """
        if self.data_ready:
            self._read_data()
        return self._temperature

    @property
    def relative_humidity(self):
        """Returns the current relative humidity in %rH.
        .. note::
            Between measurements, the most recent reading will be cached and returned.
        """
        if self.data_ready:
            self._read_data()
        return self._relative_humidity

    def _read_data(self):
        """Reads the temp/hum/co2 from the sensor and caches it"""
        self._send_command(_SCD4X_READMEASUREMENT, cmd_delay=0.001)
        self._read_reply(self._buffer, 9)
        self._co2 = (self._buffer[0] << 8) | self._buffer[1]
        temp = (self._buffer[3] << 8) | self._buffer[4]
        self._temperature = -45 + 175 * (temp / 2 ** 16)
        humi = (self._buffer[6] << 8) | self._buffer[7]
        self._relative_humidity = 100 * (humi / 2 ** 16)

    @property
    def data_ready(self):
        """Check the sensor to see if new data is available"""
        self._send_command(_SCD4X_DATAREADY, cmd_delay=0.001)
        self._read_reply(self._buffer, 3)
        return not ((self._buffer[0] & 0x03 == 0) and (self._buffer[1] == 0))

    def measure_single_shot(self):
        """On-demand measurement of CO2 concentration, relative humidity, and
        temperature for SCD41 only"""
        self._send_command(_SCD4X_MEASURESINGLESHOT, cmd_delay=5)

    def stop_periodic_measurement(self):
        """Stop measurement mode"""
        self._send_command(_SCD4X_STOPPERIODICMEASUREMENT, cmd_delay=0.5)

    def _send_command(self, cmd, cmd_delay=0.0):
        self._cmd[0] = (cmd >> 8) & 0xFF
        self._cmd[1] = cmd & 0xFF
        self.i2c.writeto(self.address, self._cmd)
        time.sleep(cmd_delay)

    def _read_reply(self, buff, num):
        self.i2c.readfrom_into(self.address, buff, num)
        self._check_buffer_crc(self._buffer[0:num])

    @property
    def serial_number(self):
        """Request a 6-tuple containing the unique serial number for this sensor"""
        self._send_command(_SCD4X_SERIALNUMBER, cmd_delay=0.001)
        self._read_reply(self._buffer, 9)
        return (
            self._buffer[0],
            self._buffer[1],
            self._buffer[3],
            self._buffer[4],
            self._buffer[6],
            self._buffer[7],
        )

    def persist_settings(self) -> None:
        """Save temperature offset, altitude offset, and selfcal enable settings to EEPROM"""
        self._send_command(_SCD4X_PERSISTSETTINGS, cmd_delay=0.8)

    @property
    def temperature_offset(self) -> float:
        """Specifies the offset to be added to the reported measurements to account for a bias in
        the measured signal. Value is in degrees Celsius with a resolution of 0.01 degrees and a
        maximum value of 374 C

        ... note::
            This value will NOT be saved and will be reset on boot unless saved with
            persist_settings().
        """
        self._send_command(_SCD4X_GETTEMPOFFSET, cmd_delay=0.001)
        self._read_reply(self._buffer, 3)
        temp = (self._buffer[0] << 8) | self._buffer[1]
        return 175.0 * temp / ((2**16)-1)

    @temperature_offset.setter
    def temperature_offset(self, offset) -> None:
        if offset > 374:
            raise AttributeError(
                "Offset value must be less tha4n or equal to 37 degrees Celsius"
            )
        temp = int(offset * ((2**16)-1) / 175)
        self._set_command_value(_SCD4X_SETTEMPOFFSET, temp)

    @property
    def altitude(self) -> int:
        """Specifies the altitude at the measurement location in meters above sea level. Setting
        this value adjusts the CO2 measurement calculations to account for the air pressure's effect
        on readings.

        .. note::
            This value will NOT be saved and will be reset on boot unless saved with
            persist_settings().
        """
        self._send_command(_SCD4X_GETALTITUDE, cmd_delay=0.001)
        self._read_reply(self._buffer, 3)
        return (self._buffer[0] << 8) | self._buffer[1]

    @altitude.setter
    def altitude(self, height: int) -> None:
        if height > 65535:
            raise AttributeError("Height must be less than or equal to 65535 meters")
        self._set_command_value(_SCD4X_SETALTITUDE, height)

    def _set_command_value(self, cmd, value, cmd_delay=0):
        self._buffer[0] = (cmd >> 8) & 0xFF
        self._buffer[1] = cmd & 0xFF
        self._crc_buffer[0] = self._buffer[2] = (value >> 8) & 0xFF
        self._crc_buffer[1] = self._buffer[3] = value & 0xFF
        self._buffer[4] = self._crc8(self._crc_buffer)
        self.i2c.writeto(self.address, self._buffer)
        time.sleep(cmd_delay)

    def _check_buffer_crc(self, buf):
        for i in range(0, len(buf), 3):
            self._crc_buffer[0] = buf[i]
            self._crc_buffer[1] = buf[i + 1]
            if self._crc8(self._crc_buffer) != buf[i + 2]:
                raise RuntimeError("CRC check failed while reading data")
        return True

    @staticmethod
    def _crc8(buffer):
        crc = 0xFF
        for byte in buffer:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1
        return crc & 0xFF  # return the bottom 8 bits

    @property
    def info(self):
        serial_number = [str(sn) for sn in self.serial_number]
        if not all(not v for v in serial_number):
            return "".join(serial_number)
        else:
            return False

    def get_values(self):
        self.measure_single_shot()
        self.last_values = OrderedDict()
        self.last_values["co2"] = self.co2
        self.last_values["temperature"] = self.temperature
        self.last_values["humidity"] = self.relative_humidity
        return True

    @property
    def settings(self):
        if self._settings["Altitude"] is None:
            self._settings["Altitude"] = str(self.altitude)
        if self._settings["Tmp-offset"] is None:
            self._settings["Tmp-offset"] = str(-self.temperature_offset)
        return self._settings

    def settings_save(self):
        self.altitude = int(self.settings["Altitude"])
        self.temperature_offset = -float(self.settings["Tmp-offset"].replace(",", "."))
        self.persist_settings()

    def get_ble_characteristics(self):
        battery = b'\x01' + struct.pack("<B", self.last_values["soc"])
        temperature = b'\x02' + struct.pack("<h", int(self.last_values["temperature"]*100))
        humidity = b'\x03' + struct.pack("<h", int(self.last_values["humidity"]*100))
        co2 = b'\x12' + struct.pack("<h", self.last_values["co2"])

        characteristics = battery + temperature + humidity + co2

        return characteristics
