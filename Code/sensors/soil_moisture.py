from collections import OrderedDict
import json
import struct


class SoilMoisture:
    def __init__(self, adc, filename):
        self.adc = adc

        self.displ_min = 0
        self.displ_max = 100

        self.filename = filename
        self.settings = self.settings_load()
        self.displ_min = 0
        self.displ_max = 100

        self.units_classes = {"moisture": ("%", "moisture")}
        self.last_values = {}

    def _measure(self):
        num_of_measurements = 1000
        n = 0
        measured = 0
        while n < num_of_measurements:
            measured += self.adc.read_u16()
            n += 1
        value = (measured / num_of_measurements)
        return 65535-int(value)

    def cont_measure(self):
        while True:
            print(self._to_percentage(self._measure()))

    def _to_percentage(self, val):
        minimum, maximum = int(self.displ_min), int(self.displ_max)
        val = max(minimum, min(val, maximum))
        val -= minimum
        diff = maximum - minimum
        val /= diff
        return int(val*100)

    @property
    def info(self):
        return "value:" + str(self._measure())

    def get_values(self):
        self.last_values = {"moisture": self._to_percentage(self._measure())}
        return True

    def settings_load(self):
        settings = OrderedDict()
        try:
            with open(self.filename, "r") as f:
                settings = f.read()
                settings = json.loads(settings)
        except Exception as e:
            print(e)
            settings["Minimum"] = self.settings["Minimum"]
            settings["Maximum"] = self.settings["Maximum"]
        finally:
            return settings

    def settings_save(self):
        with open(self.filename, "w") as f:
            f.write(json.dumps(self.settings))

    def get_ble_characteristics(self):
        battery = b'\x01' + struct.pack("<B", self.last_values["soc"])
        moisture = b'\x14' + struct.pack("<h", int(self.last_values["moisture"]*100))

        characteristics = battery + moisture
        return characteristics
