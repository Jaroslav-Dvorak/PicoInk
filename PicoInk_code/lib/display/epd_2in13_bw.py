from lib.display.ssd_1680 import SSD1680
from time import sleep_ms
import os
from nonvolatile import SEEK_END

HEIGHT = 250
WIDTH = 128
IMAGE_BYTES = WIDTH*HEIGHT//8

SEEN_HEIGHT = 250
SEEN_WIDTH = 122

LEFT = 0
RIGHT = 249
TOP = 6
BOTTOM = 127


class Epd2in13bw(SSD1680):

    def __init__(self, busy, rst, dc, cs, spi):
        super().__init__(busy, rst, dc, cs, spi, HEIGHT, WIDTH)
        self.lut_partial = [
            0x0, 0x40, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x80, 0x80, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x40, 0x40, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x80, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x14, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
            0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x0, 0x0, 0x0,
            0x22, 0x17, 0x41, 0x00, 0x32, 0x36,
        ]

        self.partial_in_use = False
        self.max_display_filesize = IMAGE_BYTES * 20
        self.filename = "display.dat"
        img = self.load_display_data(IMAGE_BYTES)
        if len(img) == IMAGE_BYTES:
            self.load_previous(img)
            self.force_full_upd = False
        else:
            self.force_full_upd = True

    def show(self, image, partial):
        self.save_display_data(image=image)
        if not partial or self.force_full_upd:
            self._show_full(image)
            self.force_full_upd = False
        else:
            self._show_partial(image)

    def _show_full(self, image):
        if self.partial_in_use:
            self.epd_hw_init()
            self.partial_in_use = False

        self.send_command(0x24)
        for j in range(self.width_end_byte, -1, -1):
            for i in range(0, self.height):
                self.send_int_data(image[i + j * self.height])
        self.load_previous(image)
        self.full_update()

    def _send_lut(self):
        self.send_command(0x32)
        self.send_collection_data(self.lut_partial[0:153])
        self.wait_busy()

        self.send_command(0x3F)
        self.send_int_data(self.lut_partial[153])
        self.send_command(0x03)                     # gate voltage
        self.send_int_data(self.lut_partial[154])
        self.send_command(0x04)                     # source voltage
        self.send_int_data(self.lut_partial[155])   # VSH
        self.send_int_data(self.lut_partial[156])   # VSH2
        self.send_int_data(self.lut_partial[157])   # VSL
        self.send_command(0x2C)                     # VCOM
        self.send_int_data(self.lut_partial[158])

    def _show_partial(self, image):
        self.reset.value(False)
        sleep_ms(1)
        self.reset.value(True)
        if not self.partial_in_use:
            self._send_lut()

            self.send_command(0x37)
            self.send_int_data(0x00)
            self.send_int_data(0x00)
            self.send_int_data(0x00)
            self.send_int_data(0x00)
            self.send_int_data(0x00)
            self.send_int_data(0x40)
            self.send_int_data(0x00)
            self.send_int_data(0x00)
            self.send_int_data(0x00)
            self.send_int_data(0x00)
            self.send_int_data(0x00)

            self.send_command(0x3C)
            self.send_int_data(0x80)

        self.send_command(0x22)
        self.send_int_data(0xC0)
        self.send_command(0x20)
        self.wait_busy()

        self._define_ram_area(0, 0, self.width - 1, self.height - 1)
        self._set_ram_pointer(0, 0)

        self.send_command(0x24)
        for j in range(self.width_end_byte, -1, -1):
            for i in range(0, self.height):
                self.send_int_data(image[i + j * self.height])

        self._partial_update()
        self.wait_busy()
        self.partial_in_use = True

    def _partial_update(self):
        self.send_command(0x22)     # Display Update Control
        self.send_int_data(0x0c)    # fast:0x0c, quality:0x0f, 0xcf
        self.send_command(0x20)     # Activate Display Update Sequence

    def load_previous(self, image):
        self.send_command(0x26)
        for j in range(self.width_end_byte, -1, -1):
            for i in range(0, self.height):
                self.send_int_data(image[i + j * self.height])

    def save_display_data(self, image):
        try:
            filesize = os.stat(self.filename)[6]
        except OSError:
            write_mode = "wb"
            self.force_full_upd = True
        else:
            if filesize < self.max_display_filesize:
                write_mode = "ab"
            else:
                write_mode = "wb"
                # self.force_full_upd = True
        with open(self.filename, write_mode) as f:
            f.write(image)

    def load_display_data(self, size):
        try:
            with open(self.filename, "rb") as f:
                f.seek(0, SEEK_END)
                # filesize = f.tell()
                f.seek(-size, SEEK_END)
                values_binary = f.read(size)
        except OSError:
            return []

        return values_binary
