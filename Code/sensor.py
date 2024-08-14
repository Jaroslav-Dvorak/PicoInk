
# _____________________DS18X20_____________________________________________________

from sensors.ds18x20 import DS18X20
from machine import Pin
# sensor = DS18X20(Pin(19), filename="sensors/ds18x20_1.json")
sensor = DS18X20(Pin(0), filename="sensors/ds18x20_1.json")

# _____________________SCD4X_____________________________________________________

# from machine import I2C, Pin
# from sensors.scd4x import SCD4X
#
# Pin(8, Pin.OUT).value(1)
# Pin(9, Pin.OUT).value(0)
#
# I2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=400_000)
# sensor = SCD4X(I2c)

# _______________________SOIL MOISTURE_________________________________________)

# from machine import ADC
# from sensors.soil_moisture import SoilMoisture
#
# adc = ADC(26)
# sensor = SoilMoisture(adc, "sensors/moisture_1.json")

# _____________________DHT22_____________________________________________________
#
# from machine import Pin
# from sensors.dht22 import PicoDHT22
# from time import sleep_ms
#
#
# Pin(9, Pin.OUT).value(True)
# Pin(6, Pin.OUT).value(False)
# dht_data = Pin(8, Pin.IN, Pin.PULL_UP)
# sleep_ms(1100)
# sensor = PicoDHT22(dataPin=dht_data, filename="sensors/dht22_1.json")

# _____________________SHT4X_____________________________________________________
#
# from machine import I2C, Pin
# from sensors.sht4x import SHT4X
#
# Pin(8, Pin.OUT).value(0)
# Pin(9, Pin.OUT).value(9)
#
# I2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=400_000)
# sensor = SHT4X(I2c, filename="sensors/sht41.json")
