import usocket as socket
import network
from collections import OrderedDict
from lib.display.screens import show_settings, clear_display
from nonvolatile import Settings, settings_save
from utime import sleep_ms
from gpio_definitions import BTN_1
import machine
from sensor import sensor

AP = network.WLAN(network.AP_IF)
S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
Done = False


def start_ap(ssid):
    AP.config(security=0, ssid=ssid)
    AP.active(True)

    while not AP.active():
        pass
    ip = AP.ifconfig()[0]
    return ip


def web_page():
    forms = ""
    sensor_settings = list(sensor.settings.items())
    general_settings = list(Settings.items())
    for k, v in sensor_settings + general_settings:
        if k[0].islower():
            continue
        forms += f"""
        <form action="/get" accept-charset="UTF-8">
            {k:<10}: <input type="text" name="{k}" value="{v}">
            <input type="submit" value="Submit">
        </form><br>
        """

    html = f"""
    <!DOCTYPE HTML><html><head>
        <meta charset="utf-8" name="viewport" content="width=device-width, initial-scale=1">
      <title>WUD</title>
          </head><body style="font-family:monospace;">
            {forms}
          </body></html>
    """
    return html.encode("utf-8")


def unquote(s):
    r = str(s).split('%')
    try:
        b = r[0].encode()
        for i in range(1, len(r)) :
            try:
                b += bytes([int(r[i][:2], 16)]) + r[i][2:].encode()
            except:
                b += b'%' + r[i].encode()
        return b.decode('UTF-8')
    except:
        return str(s)


def parse_request(request):
    setting = (request[9:].split()[0].split("="))
    try:
        if Settings.get(setting[0], None) is not None:
            Settings[setting[0]] = unquote(setting[1])
        elif sensor.settings.get(setting[0], None) is not None:
            sensor.settings[setting[0]] = unquote(setting[1])
    except IndexError:
        pass
    # try:
    #     Settings[setting[0]] = unquote(setting[1])
    # except KeyError:
    #     pass
    # except IndexError:
    #     pass
    #
    # try:
    #     sensor.settings[setting[0]] = unquote(setting[1])
    # except KeyError:
    #     pass
    # except IndexError:
    #     pass


def save_and_restart(_):
    global Done
    if not Done:
        settings_save()
        sensor.settings_save()
        clear_display()
        sleep_ms(1000)
        machine.reset()
    Done = True


def start_web():
    while not BTN_1.value():
        sleep_ms(200)
    sleep_ms(2000)
    BTN_1.irq(trigger=machine.Pin.IRQ_FALLING, handler=save_and_restart)
    S.bind(('', 80))
    S.listen(5)
    scr_partial = False
    while True:
        conn, addr = S.accept()
        request = conn.recv(1024)
        request = request.decode("utf-8")
        parse_request(request)
        response = web_page()
        conn.sendall(response)
        conn.close()

        all_settings = OrderedDict()
        all_settings.update(sensor.settings)
        all_settings.update(Settings)
        show_settings(all_settings, partial=scr_partial)
        scr_partial = True
