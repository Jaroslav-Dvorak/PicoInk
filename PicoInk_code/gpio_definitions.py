from machine import Pin, ADC, SPI
from machine import Pin, ADC, SPI


# display WeAct
# 1 Busy    purple
# 2 Res     orange
# 3 D/C     white
# 4 CS      blue
# 5 SCL     green
# 6 SDA     yellow
# 7 GND     black
# 8 VCC     red
BUSY_PIN = Pin(10, Pin.IN, Pin.PULL_UP)
RST_PIN = Pin(11, Pin.OUT)
DC_PIN = Pin(12, Pin.OUT)
CS_PIN = Pin(13, Pin.OUT)
SCL_PIN = Pin(14)  # SCL=SCK
SDA_PIN = Pin(15)  # SDA=MOSI
SPI_NUM = 1
SPI_DISPLAY = SPI(SPI_NUM, baudrate=1_000_000, sck=SCL_PIN, mosi=SDA_PIN)
# DEFAULT SPI DECLARATION:
# SPI0 - sck=Pin(18), mosi=Pin(19), miso=Pin(16)
# SPI1 - sck=Pin(10), mosi=Pin(11), miso=Pin(8)

# tp5110
# DONE_PIN = Pin(0, Pin.OUT)
DONE_PIN = Pin(9, Pin.OUT)

# analog
BATT_ADC = ADC(28)
TEMPER_ADC = ADC(4)

# leds
ONBOARD_LED = Pin('LED', Pin.OUT)
GREEN_LED = Pin(22, Pin.OUT)

# buttons
BTN_1 = Pin(19, Pin.IN, Pin.PULL_UP)
BTN_2 = Pin(18, Pin.IN, Pin.PULL_UP)
BTN_3 = Pin(16, Pin.IN, Pin.PULL_UP)
