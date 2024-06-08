import framebuf
from lib.display.epd_2in13_bw import HEIGHT, WIDTH, BOTTOM, TOP


WHITE = 1
BLACK = 0


class Drawing:
    def __init__(self, background=WHITE):
        self.img = bytearray((HEIGHT * WIDTH)//8)
        self.canvas = framebuf.FrameBuffer(self.img, HEIGHT, WIDTH, framebuf.MONO_VLSB)
        self.background = background
        self.clear()

    def clear(self):
        self.canvas.fill(self.background)

    def pixel(self, x, y, color=BLACK):
        y += TOP
        self.canvas.pixel(x, y, color)

    def line(self, x1, y1, x2, y2, color=BLACK):
        y1 += TOP
        y2 += TOP
        self.canvas.line(x1, y1, x2, y2, color)

    def hline(self, x, y, w, color=BLACK):
        y += TOP
        self.canvas.hline(x, y, w, color)

    def vline(self, x, y, h, color=BLACK):
        y += TOP
        self.canvas.vline(x, y, h, color)

    def rect(self, x, y, w, h, color=BLACK):
        y += TOP
        self.canvas.rect(x, y, w, h, color)

    def fill_rect(self, x, y, w, h, color=BLACK):
        y += TOP
        self.canvas.fill_rect(x, y, w, h, color)

    def circle(self, x, y, radius, color=BLACK):
        y += TOP
        f = 1 - radius
        ddf_x = 1
        ddf_y = -2 * radius
        x_r = 0
        y_r = radius
        self.canvas.pixel(x, y + radius, color)  # bottom
        self.canvas.pixel(x, y - radius, color)  # top
        self.canvas.pixel(x + radius, y, color)  # right
        self.canvas.pixel(x - radius, y, color)  # left
        while x_r < y_r:
            if f >= 0:
                y_r -= 1
                ddf_y += 2
                f += ddf_y
            x_r += 1
            ddf_x += 2
            f += ddf_x
            # angle notations are based on the unit circle and in diection of being drawn
            self.canvas.pixel(x + x_r, y + y_r, color)  # 270 to 315
            self.canvas.pixel(x - x_r, y + y_r, color)  # 270 to 255
            self.canvas.pixel(x + x_r, y - y_r, color)  # 90 to 45
            self.canvas.pixel(x - x_r, y - y_r, color)  # 90 to 135
            self.canvas.pixel(x + y_r, y + x_r, color)  # 0 to 315
            self.canvas.pixel(x - y_r, y + x_r, color)  # 180 to 225
            self.canvas.pixel(x + y_r, y - x_r, color)  # 0 to 45
            self.canvas.pixel(x - y_r, y - x_r, color)  # 180 to 135

    def fill_circle(self, x, y, radius, color=BLACK):
        y += TOP
        self.canvas.vline(x, y - radius, 2 * radius + 1, color)
        f = 1 - radius
        ddf_x = 1
        ddf_y = -2 * radius
        x_r = 0
        y_r = radius
        while x_r < y_r:
            if f >= 0:
                y_r -= 1
                ddf_y += 2
                f += ddf_y
            x_r += 1
            ddf_x += 2
            f += ddf_x
            self.canvas.vline(x + x_r, y - y_r, 2 * y_r + 1, color)
            self.canvas.vline(x + y_r, y - x_r, 2 * x_r + 1, color)
            self.canvas.vline(x - x_r, y - y_r, 2 * y_r + 1, color)
            self.canvas.vline(x - y_r, y - x_r, 2 * x_r + 1, color)

    def tiny_text(self, string, x, y, color=BLACK):
        y += TOP
        self.canvas.text(string, x, y, color)

    def large_text(self, string, x, y, color=BLACK):
        x -= 4
        from lib.display.writer import Writer
        import lib.display.bigfont as bigfont
        invert = not color
        writer_inst = Writer(self.canvas, WIDTH, HEIGHT, bigfont)
        writer_inst.fgcolor = color
        writer_inst.bgcolor = not color
        writer_inst.set_textpos(TOP, x)
        writer_inst.y_offset = y
        writer_inst.printstring(string, invert)
