from collections import OrderedDict
import rp2
from rp2 import PIO, asm_pio
from machine import Pin
from time import sleep_ms
import json
import struct

'''
 *
 *
 * The MIT License (MIT)
 *
 * Copyright (c) 2021 Daniel Perron
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
'''


@asm_pio(set_init=(PIO.OUT_HIGH), autopush=True, push_thresh=8)
def DHT22_PIO():
    # clock set at 500Khz  Cycle is 2us
    # drive output low for at least 20ms
    set(y, 1)  # 0
    pull()  # 1
    mov(x, osr)  # 2
    set(pindirs, 1)  # 3 set pin to output
    set(pins, 0)  # 4 set pin low
    label('waitx')
    jmp(x_dec, 'waitx')  # 5 decrement x reg every 32 cycles
    set(pindirs, 0)  # 6 set pin to input
    # STATE A. Wait for high at least 80us. max should be  very short
    set(x, 31)  # 7
    label('loopA')
    jmp(pin, 'got_B')  # 8
    jmp(x_dec, 'loopA')  # 9
    label('Error')
    in_(y, 1)  # 10
    jmp('Error')  # 11  Infinity loop error

    # STATE B. Get HIGH pulse. max should be 40us
    label('got_B')
    set(x, 31)  # 12
    label('loop_B')
    jmp(x_dec, 'check_B')  # 13
    jmp('Error')  # 14
    label('check_B')
    jmp(pin, 'loop_B')  # 15

    # STATE C. Get LOW pulse. max should be 80us
    set(x, 31)  # 16
    label('loop_C')
    jmp(pin, 'got_D')  # 17
    jmp(x_dec, 'loop_C')  # 18
    jmp('Error')  # 19

    # STATE D. Get HIGH pulse. max should be 80us
    label('got_D')
    set(x, 31)  # 20
    label('loop_D')
    jmp(x_dec, 'check_D')  # 21
    jmp('Error')  # 22
    label('check_D')
    jmp(pin, 'loop_D')  # 23

    # STATE E. Get Low pulse delay. should be around 50us
    set(x, 31)  # 24
    label('loop_E')
    jmp(pin, 'got_F')  # 25
    jmp(x_dec, 'loop_E')  # 26
    jmp('Error')  # 27

    # STATE F.
    # wait 40 us
    label('got_F')
    nop()[20]  # 28
    in_(pins, 1)  # 29
    # now wait for low pulse
    set(x, 31)  # 30
    jmp('loop_D')  # 31


class PicoDHT22:

    def __init__(self, dataPin, filename, powerPin=None, dht11=False, smID=1):
        self.dataPin = dataPin
        self.powerPin = powerPin
        self.dht11 = dht11
        self.smID = smID
        # self.dataPin.init(Pin.IN, Pin.PULL_UP)
        if self.powerPin is not None:
            self.powerPin.init(Pin.OUT)
            self.powerPin.value(0)
        self.sm = rp2.StateMachine(self.smID)

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

    def read_array(self):
        if self.powerPin is not None:
            self.powerPin.value(1)
            sleep_ms(800)
        sleep_ms(200)
        # start state machine
        self.sm.init(DHT22_PIO, freq=500000,
                     set_base=self.dataPin,
                     in_base=self.dataPin,
                     jmp_pin=self.dataPin)
        # sleep_ms(300)
        if self.dht11:
            self.sm.put(10000)
        else:
            self.sm.put(1000)
            self.sm.put(1000)
        self.sm.active(1)
        value = []
        for i in range(5):
            value.append(self.sm.get())
        self.sm.active(0)
        if self.powerPin is not None:
            self.powerPin.value(0)
        return value

    def read(self):
        while True:
            value = self.read_array()
            sumV = 0
            for i in range(4):
                sumV += value[i]
            if (sumV & 0xff) == value[4]:
                if self.dht11:
                    humidity = value[0] & 0x7f
                    temperature = value[2]
                else:
                    humidity = ((value[0] << 8) + value[1]) / 10.0
                    temperature = (((value[2] & 0x7f) << 8) + value[3]) / 10.0
                if (value[2] & 0x80) == 0x80:
                    temperature = -temperature
                return temperature, humidity
            # else:
            #     continue
        return None

    @property
    def info(self):
        temperature_humidity = self.read()
        if temperature_humidity:
            temperature, humidity = temperature_humidity
            return "{:3.1f}C  {:3.1f}%".format(temperature, humidity)
        else:
            return None

    def get_values(self):
        temperature_humidity = self.read()
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
