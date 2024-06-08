# 1-Wire driver for MicroPython
# MIT license; Copyright (c) 2016 Damien P. George
# DS18x20 temperature sensor driver for MicroPython.
# MIT license; Copyright (c) 2016 Damien P. George

from time import sleep_ms
from micropython import const
from collections import OrderedDict
import json
import struct
import _onewire as _ow


class OneWireError(Exception):
    pass


class OneWire:
    SEARCH_ROM = 0xF0
    MATCH_ROM = 0x55
    SKIP_ROM = 0xCC

    def __init__(self, pin):
        self.pin = pin
        self.pin.init(pin.OPEN_DRAIN, pin.PULL_UP)

    def reset(self, required=False):
        reset = _ow.reset(self.pin)
        if required and not reset:
            raise OneWireError
        return reset

    def readbit(self):
        return _ow.readbit(self.pin)

    def readbyte(self):
        return _ow.readbyte(self.pin)

    def readinto(self, buf):
        for i in range(len(buf)):
            buf[i] = _ow.readbyte(self.pin)

    def writebit(self, value):
        return _ow.writebit(self.pin, value)

    def writebyte(self, value):
        return _ow.writebyte(self.pin, value)

    def write(self, buf):
        for b in buf:
            _ow.writebyte(self.pin, b)

    def select_rom(self, rom):
        self.reset()
        self.writebyte(self.MATCH_ROM)
        self.write(rom)

    def scan(self):
        devices = []
        diff = 65
        rom = False
        for i in range(0xFF):
            rom, diff = self._search_rom(rom, diff)
            if rom:
                devices += [rom]
            if diff == 0:
                break
        return devices

    def _search_rom(self, l_rom, diff):
        if not self.reset():
            return None, 0
        self.writebyte(self.SEARCH_ROM)
        if not l_rom:
            l_rom = bytearray(8)
        rom = bytearray(8)
        next_diff = 0
        i = 64
        for byte in range(8):
            r_b = 0
            for bit in range(8):
                b = self.readbit()
                if self.readbit():
                    if b:  # there are no devices or there is an error on the bus
                        return None, 0
                else:
                    if not b:  # collision, two devices with different bit meaning
                        if diff > i or ((l_rom[byte] & (1 << bit)) and diff != i):
                            b = 1
                            next_diff = i
                self.writebit(b)
                if b:
                    r_b |= 1 << bit
                i -= 1
            rom[byte] = r_b
        return rom, next_diff

    def crc8(self, data):
        return _ow.crc8(data)


_CONVERT = const(0x44)
_RD_SCRATCH = const(0xBE)
_WR_SCRATCH = const(0x4E)


class DS18X20:
    def __init__(self, pin, filename):
        self.ow = OneWire(pin)
        self.buf = bytearray(9)

        self.filename = filename
        self.settings = self.settings_load()
        self.displ_min = self.settings["Minimum"]
        self.displ_max = self.settings["Maximum"]
        self.offset = self.settings["Offset"]

        self.units_classes = {"temperature": ("°C", "temperature")}

        self.last_values = {}

    def scan(self):
        return [rom for rom in self.ow.scan() if rom[0] in (0x10, 0x22, 0x28)]

    def convert_temp(self):
        self.ow.reset(True)
        self.ow.writebyte(self.ow.SKIP_ROM)
        self.ow.writebyte(_CONVERT)

    def read_scratch(self, rom):
        self.ow.reset(True)
        self.ow.select_rom(rom)
        self.ow.writebyte(_RD_SCRATCH)
        self.ow.readinto(self.buf)
        if self.ow.crc8(self.buf):
            raise Exception("CRC error")
        return self.buf

    def write_scratch(self, rom, buf):
        self.ow.reset(True)
        self.ow.select_rom(rom)
        self.ow.writebyte(_WR_SCRATCH)
        self.ow.write(buf)

    def read_temp(self, rom):
        buf = self.read_scratch(rom)
        if rom[0] == 0x10:
            if buf[1]:
                t = buf[0] >> 1 | 0x80
                t = -((~t + 1) & 0xFF)
            else:
                t = buf[0] >> 1
            return t - 0.25 + (buf[7] - buf[6]) / buf[7]
        else:
            t = buf[1] << 8 | buf[0]
            if t & 0x8000:  # sign bit set
                t = -((t ^ 0xFFFF) + 1)
            return t / 16

    def get_rom(self):
        tries = 0
        while tries < 100:
            tries += 1
            roms = self.scan()
            if len(roms) > 0:
                rom = ''.join([byte.to_bytes(1, 'big').hex() for byte in roms[0]])
                return rom
        return None

    @property
    def info(self):
        return self.get_rom()

    def get_values(self):
        if self.settings["rom"] is None:
            self.settings["rom"] = self.get_rom()
            self.settings_save()
        self.convert_temp()
        sleep_ms(750)
        rom = bytes.fromhex(self.settings["rom"])
        temperature = self.read_temp(rom)
        temperature += self.offset
        self.last_values = {"temperature": temperature}
        return int(temperature) != -127

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
            settings["Minimum"] = 0
            settings["Maximum"] = 60
            settings["rom"] = None
            settings["Offset"] = 0.0
        finally:
            return settings

    def settings_save(self):
        with open(self.filename, "w") as f:
            f.write(json.dumps(self.settings))

    def get_ble_characteristics(self):
        battery = b'\x01' + struct.pack("<B", self.last_values["soc"])
        temperature = b'\x02' + struct.pack("<h", int(self.last_values["temperature"]*100))

        characteristics = battery + temperature

        return characteristics
