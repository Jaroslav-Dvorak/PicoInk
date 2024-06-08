from time import sleep_ms


class SSD1680:
    def __init__(self, busy, rst, dc, cs, spi, height, width):
        self.busy = busy
        self.reset = rst
        self.dc = dc
        self.cs = cs
        self.spi = spi

        self.height = height
        self.width = width
        self.height_end_bit = height - 1
        self.width_end_byte = (width // 8) - 1

        self.epd_hw_init()

    def spi_write(self, value):
        self.spi.write(bytearray(value))

    def send_command(self, command):
        self.cs.value(False)
        self.dc.value(False)
        self.spi_write([command])
        self.cs.value(True)

    def send_int_data(self, data):
        self.cs.value(False)
        self.dc.value(True)
        self.spi_write([data])
        self.cs.value(True)

    def send_collection_data(self, data):
        self.cs.value(False)
        self.dc.value(True)
        self.spi_write(data)
        self.cs.value(True)

    def wait_busy(self):
        while self.busy.value():
            sleep_ms(3)

    def sw_reset(self):
        self.send_command(0x12)
        self.wait_busy()

    def hw_reset(self):
        self.reset.value(True)
        sleep_ms(20)
        self.reset.value(False)
        sleep_ms(2)
        self.reset.value(True)
        sleep_ms(20)
        self.wait_busy()

    def epd_hw_init(self):
        self.hw_reset()
        self.sw_reset()

        # Driver output control
        self.send_command(0x01)
        self.send_int_data((self.height-1) & 0xFF)
        self.send_int_data((self.height-1 >> 8) & 0xFF)
        self.send_int_data(0x00)

        # data entry mode
        self.send_command(0x11)
        self.send_int_data(0b00000111)

        self._define_ram_area(0, 0, self.width-1, self.height-1)
        self._set_ram_pointer(0, 0)

        # BorderWaveform
        self.send_command(0x3C)
        self.send_int_data(0b000001_01)  # 00 - black, 01 - white, 10 and 11 - red

        # Display update control
        self.send_command(0x21)
        self.send_int_data(0x00)
        self.send_int_data(0x80)

        # Read built - in temperature sensor
        self.send_command(0x18)
        self.send_int_data(0x80)

        self.wait_busy()

    def _define_ram_area(self, x_start, y_start, x_end, y_end):
        self.send_command(0x44)
        self.send_int_data((x_start >> 3) & 0xFF)
        self.send_int_data((x_end >> 3) & 0xFF)

        self.send_command(0x45)
        self.send_int_data(y_start & 0xFF)
        self.send_int_data((y_start >> 8) & 0xFF)
        self.send_int_data(y_end & 0xFF)
        self.send_int_data((y_end >> 8) & 0xFF)

    def _set_ram_pointer(self, x_start, y_start):
        self.send_command(0x4E)
        self.send_int_data(x_start & 0xFF)

        self.send_command(0x4F)
        self.send_int_data(y_start & 0xFF)
        self.send_int_data((y_start >> 8) & 0xFF)

    def deep_sleep(self):
        self.send_command(0x10)  # enter deep sleep
        self.send_int_data(0x01)
        sleep_ms(100)

    def full_update(self):
        # Display Update Control
        self.send_command(0x22)
        self.send_int_data(0xF7)
        # Activate Display Update Sequence
        self.send_command(0x20)
        self.wait_busy()
