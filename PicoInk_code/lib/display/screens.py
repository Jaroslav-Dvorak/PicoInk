import machine
import os
import gc
from lib.display.widgets import Widgets
from lib.display.epd_2in13_bw import Epd2in13bw
from lib.display.templates import Gauge, Gauge_needle_end_lookup, Gauge_axis_right_lookup, Gauge_axis_left_lookup
from gpio_definitions import BUSY_PIN, RST_PIN, DC_PIN, CS_PIN, SPI_DISPLAY

widgets = Widgets()
eink = Epd2in13bw(BUSY_PIN, RST_PIN, DC_PIN, CS_PIN, SPI_DISPLAY)


def show_chart(values, minimum, maximum, batt_soc, full_refresh=False):
    batt_coor = 150, 0
    if len(values) > 250:
        values.pop(0)
    widgets.clear()
    widgets.chart(values, minimum, maximum)
    widgets.battery_indicator(batt_soc, *batt_coor)

    eink.show(widgets.img, partial=not full_refresh)


def show_big_val(curr_val, battery_soc, full_refresh=False):
    value_coor = 5, 25
    batt_coor = 210, 0
    widgets.clear()
    curr_val = round(curr_val, 1)
    widgets.large_text(str(curr_val), *value_coor)
    widgets.battery_indicator(battery_soc, *batt_coor)
    eink.show(widgets.img, partial=not full_refresh)


def show_gauge(curr_val, minimum, maximum, battery_soc, full_refresh=False):
    batt_coor = 210, 0
    curr_val = round(curr_val, 1)
    if curr_val > maximum:
        curr_val = maximum
    if curr_val < minimum:
        curr_val = minimum
    optimized_value = int(((curr_val - minimum) / (maximum - minimum)) * 159)

    widgets.clear()
    widgets.image(Gauge)

    widgets.tiny_text(str(curr_val), 150, 110)
    widgets.tiny_text(str(minimum), 5, 110)
    widgets.tiny_text(str(maximum), 222, 110)

    x_ax_l, y_ax_l = Gauge_axis_left_lookup[optimized_value]
    x_ax_r, y_ax_r = Gauge_axis_right_lookup[optimized_value]
    x_ax_c, y_ax_c = 125, 109

    x_end, y_end = Gauge_needle_end_lookup[optimized_value]

    widgets.line(x1=x_ax_r, y1=y_ax_r, x2=x_end, y2=y_end)
    widgets.line(x1=x_ax_l, y1=y_ax_l, x2=x_end, y2=y_end)

    for x in range(x_ax_l, x_ax_c+3):
        widgets.line(x1=x, y1=y_ax_l, x2=x_end, y2=y_end)
    for y in range(y_ax_c-3, y_ax_l):
        widgets.line(x1=x, y1=y, x2=x_end, y2=y_end)

    for x in range(x_ax_l, x_ax_c+3):
        widgets.line(x1=x, y1=y_ax_l, x2=x_end, y2=y_end)
    for y in range(y_ax_l, y_ax_c+3):
        widgets.line(x1=x, y1=y, x2=x_end, y2=y_end)

    for x in range(x_ax_c-3, x_ax_r):
        widgets.line(x1=x, y1=y_ax_r, x2=x_end, y2=y_end)
    for y in range(y_ax_r, y_ax_c+3):
        widgets.line(x1=x, y1=y, x2=x_end, y2=y_end)

    for x in range(x_ax_c-3, x_ax_r):
        widgets.line(x1=x, y1=y_ax_r, x2=x_end, y2=y_end)
    for y in range(y_ax_c-3, y_ax_r):
        widgets.line(x1=x, y1=y, x2=x_end, y2=y_end)

    widgets.battery_indicator(battery_soc, *batt_coor)
    eink.show(widgets.img, partial=True)


def show_overview(batt_voltage, ip, ap_ssid):
    widgets.clear()
    s = os.statvfs('/')
    memory_alloc = f"RAM alloc:      {gc.mem_alloc()//1024} kB "
    memory_free =  f"RAM free:       {gc.mem_free()//1024} kB"
    storage =      f"Free storage:   {s[0] * s[3] // 1024} kB"
    cpu =          f"CPU Freq:       {machine.freq() // 1000000} MHz"
    batt_voltage = f"Batt voltage:   {batt_voltage} V"
    ip_form =      f"IP:             {ip}"
    ap_ssid =      f"AP SSID:        {ap_ssid}"

    widgets.tiny_text(memory_alloc, 0, 0)
    widgets.tiny_text(memory_free, 0, 10)
    widgets.tiny_text(storage, 0, 20)
    widgets.tiny_text(cpu, 0, 30)
    widgets.tiny_text(batt_voltage, 0, 40)
    widgets.tiny_text(ip_form, 0, 50)
    widgets.tiny_text(ap_ssid, 0, 60)

    widgets.tiny_text("SETUP", 20, 85)
    widgets.tiny_text("PAGE:", 20, 95)
    web_page = "http://"+str(ip)+":80"
    widgets.qr_code(web_page, 70, 70, 2)
    widgets.tiny_text("1)Connect to AP", 130, 80)
    widgets.tiny_text("2)Scan the QR", 130, 90)
    widgets.tiny_text("3)Fill the form", 130, 100)
    eink.show(widgets.img, partial=False)


def show_qr_code(content, x, y, size):
    widgets.clear()
    widgets.qr_code(content, x, y, size)
    eink.show(widgets.img, partial=False)


def show_settings(settings, partial):
    widgets.clear()
    i = 0
    for k, v in settings.items():
        if k[0].islower():
            continue
        text = f"{k:<10}: {v}"
        widgets.tiny_text(text, 0, i*10)
        i += 1
    eink.show(widgets.img, partial=partial)


def text_row(text, row):
    row = (row-1)*10
    widgets.fill_rect(x=0, y=row, w=eink.height, h=8, color=1)
    widgets.tiny_text(text, 0, row)
    eink.show(widgets.img, partial=True)


def clear_display():
    widgets.clear()
    eink.show(widgets.img, partial=False)
