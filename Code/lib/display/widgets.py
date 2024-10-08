from lib.display.drawing_bw import Drawing, BLACK, WHITE
from lib.display.epd_2in13_bw import SEEN_WIDTH, SEEN_HEIGHT
from lib.templates import Gauge, Gauge_needle_end_lookup, Gauge_axis_right_lookup, Gauge_axis_left_lookup


class Widgets(Drawing):
    def __init__(self):
        super().__init__()
        self.wifi_indicator_coor = 40, 10
        self.mqtt_indicator_coor = 60, 1

    def chart(self, values, minimum, maximum, color=BLACK):
        x = 0
        y = SEEN_WIDTH-1
        w = SEEN_HEIGHT-1
        h = 0

        optimized_values = [int(((val - minimum) / (maximum - minimum)) * ((y - h) + h)) for val in values]

        thickness = 3
        for thick in range(thickness):
            self.line(x+thick, y, x+thick, h, color)  # left vertical

        spread = 1
        for index, _ in enumerate(optimized_values, start=1):
            try:
                value = optimized_values[-index]
            except IndexError:
                return
            y1 = y - value
            x1 = w - index*spread
            x2 = w - ((index*spread)+spread)
            try:
                value = optimized_values[-index - 1]
                y2 = y - value
            except IndexError:
                pass
            else:
                thickness = 2
                for thick in range(thickness):
                    self.line(x1, y1+thick, x2, y2+thick, color)

        self.fill_rect(x+3, h, 20, 12, WHITE)
        self.tiny_text(str(maximum), x+5, h, color)
        self.fill_rect(x+3, y-11, 20, 12, WHITE)
        self.tiny_text(str(minimum), x+5, y-8, color)

        return optimized_values

    def gauge(self, value, minimum, maximum):
        resolution = len(Gauge_needle_end_lookup)-1
        optimized_value = int(((value - minimum) / (maximum - minimum)) * resolution)
        if optimized_value > resolution:
            optimized_value = resolution
        if optimized_value < 0:
            optimized_value = 0

        self.image(Gauge)

        x_ax_l, y_ax_l = Gauge_axis_left_lookup[optimized_value]
        x_ax_r, y_ax_r = Gauge_axis_right_lookup[optimized_value]
        x_ax_c, y_ax_c = 125, 109

        x_end, y_end = Gauge_needle_end_lookup[optimized_value]

        for x in range(x_ax_l, x_ax_c + 3):
            self.line(x1=x, y1=y_ax_l, x2=x_end, y2=y_end)
        for y in range(y_ax_c - 3, y_ax_l):
            self.line(x1=x, y1=y, x2=x_end, y2=y_end)

        for x in range(x_ax_l, x_ax_c + 3):
            self.line(x1=x, y1=y_ax_l, x2=x_end, y2=y_end)
        for y in range(y_ax_l, y_ax_c + 3):
            self.line(x1=x, y1=y, x2=x_end, y2=y_end)

        for x in range(x_ax_c - 3, x_ax_r):
            self.line(x1=x, y1=y_ax_r, x2=x_end, y2=y_end)
        for y in range(y_ax_r, y_ax_c + 3):
            self.line(x1=x, y1=y, x2=x_end, y2=y_end)

        for x in range(x_ax_c - 3, x_ax_r):
            self.line(x1=x, y1=y_ax_r, x2=x_end, y2=y_end)
        for y in range(y_ax_c - 3, y_ax_r):
            self.line(x1=x, y1=y, x2=x_end, y2=y_end)

        # self.line(x_ax_l, y_ax_l, x_ax_r, y_ax_r, color=WHITE)

        self.line(x1=x_ax_r, y1=y_ax_r, x2=x_end, y2=y_end, color=WHITE)
        self.line(x1=x_ax_l, y1=y_ax_l, x2=x_end, y2=y_end, color=WHITE)

        self.tiny_text(str(minimum), 5, 110)
        self.tiny_text(str(maximum), 222, 110)

    def battery_indicator(self, soc, x, y, color=BLACK):
        w = 30
        h = 9
        self.rect(x, y, w, h, color)
        self.fill_rect(x-4, y+2, 3, 5, color)

        soc = int(w / 100 * soc)
        soc_x = w - soc + x

        self.fill_rect(soc_x, y, soc, h, color)

    def signal_indicator(self, rssi, x=None, y=None, color=BLACK):
        w = 3
        h = 9
        if x is None or y is None:
            x, y = self.wifi_indicator_coor
        w_space = 1
        if rssi is not None:
            num_of_filled = ((rssi+100)/7.5)
        else:
            num_of_filled = 0
            # self.line(x, y, x+(w+w_space)*4, h-y)
        for i in range(1, 5):
            _h = i*2 + 1
            _x = x + (w+w_space)*i
            _y = y - _h - 1
            if num_of_filled > i:
                self.fill_rect(_x, _y, w, _h)
            else:
                self.rect(_x, _y, w, _h)

    def qr_code(self, content, x, y, scale):
        from lib.display.uQR import QRCode
        qr = QRCode(border=0, box_size=10)
        qr.add_data(content)
        matrix = qr.get_matrix()
        for y_mat in range(len(matrix) * scale):                            # Scaling the bitmap by 2
            for x_mat in range(len(matrix[0]) * scale):                     # because my screen is tiny.
                value = not matrix[int(y_mat / scale)][int(x_mat / scale)]  # Inverting the values because
                self.pixel(x_mat+x, y_mat+y, value)

    def wifi_indicator(self, x, y, strength, color=BLACK):
        self.fill_circle(x, y, 30, color=color)

    def mqtt_indicator(self, x=None, y=None, color=BLACK):
        if x is None or y is None:
            x, y = self.mqtt_indicator_coor
        self.tiny_text("!MQTT", x, y, color)
