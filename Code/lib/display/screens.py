import machine
import os
import gc
from lib.display.widgets import Widgets
from lib.display.epd_2in13_bw import Epd2in13bw
from gpio_definitions import BUSY_PIN, RST_PIN, DC_PIN, CS_PIN, SPI_DISPLAY

widgets = Widgets()
eink = Epd2in13bw(BUSY_PIN, RST_PIN, DC_PIN, CS_PIN, SPI_DISPLAY)


def show_chart(values, minimum, maximum, batt_soc, full_refresh=False):

    if len(values) > 250:
        values.pop(0)
    widgets.clear()
    opt_values = widgets.chart(values, minimum, maximum)

    if len(opt_values)>62 and max(opt_values[40:62]) > 110:
        widgets.wifi_indicator_coor = 40, 123
    else:
        widgets.wifi_indicator_coor = 40, 10

    if len(opt_values)>101 and max(opt_values[60:101]) > 110:
        print(opt_values[60:101])
        widgets.mqtt_indicator_coor = 60, 114
    else:
        widgets.mqtt_indicator_coor = 60, 1

    if len(opt_values)>182 and max(opt_values[145:182]) > 110:
        widgets.battery_indicator(batt_soc, 150, 112)
    else:
        widgets.battery_indicator(batt_soc, 150, 0)

    if len(opt_values)>249 and max(opt_values[218:]) > 110:
        widgets.tiny_text(str(values[-1]), 218, 114)
    else:
        widgets.tiny_text(str(values[-1]), 218, 0)

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
    batt_coor = 215, 5
    widgets.wifi_indicator_coor = 0, 14
    widgets.mqtt_indicator_coor = 20, 5

    curr_val = round(curr_val, 1)
    half = (minimum + maximum) / 2
    if curr_val < half:
        val_coor = 150, 110
    else:
        val_coor = 70, 110

    widgets.clear()
    widgets.gauge(curr_val, minimum, maximum)

    widgets.tiny_text(str(curr_val), *val_coor)

    widgets.battery_indicator(battery_soc, *batt_coor)
    eink.show(widgets.img, partial=not full_refresh)


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
        if "passw" in k.lower() and v:
            v = "******"
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
