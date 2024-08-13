import usocket as socket
import network
from collections import OrderedDict
from lib.display.screens import show_settings, clear_display
from nonvolatile import Settings, settings_save
from utime import sleep_ms
from gpio_definitions import BTN_1
import machine
from sensor import sensor
from lib.templates import websetup_style, byebye_style
from lib.wireless.micropyserver import MicroPyServer

AP = network.WLAN(network.AP_IF)
# S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server = MicroPyServer()

Done = False
SCR_partial = False


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
        if "passw" in k.lower():
            form_type = "password"
        else:
            form_type = "text"

        forms += f"""
        <form action="/get" accept-charset="UTF-8">
            <div class="form-group">
                <label for="{k}">{k}:</label>
                <input type={form_type} id="{k}" name="{k}" value="{v}">
            </div>
            <input type="submit" value="OK">
        </form>
        <br>
        """

    html = f"""
    <!DOCTYPE HTML>
    <html>
    <head>
        <meta charset="utf-8" name="viewport" content="width=device-width, initial-scale=0.5, maximum-scale=5">
        <title>Picoink</title>
        <style>
            {websetup_style}
        </style>
    </head>
    <body>
        <div class="container">
            {forms}
            <form action="/get" accept-charset="UTF-8">
                <div class="form-group">
                    <input type="text" id="save_form" name="save_form" value="save_form" style=display:None>
                </div>
                    <input type="submit" value="SAVE AND RESTART">
            </form>
        </div>
    </body>
    </html>
    """
    return html


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


def byebye_page():
    byebye = f"""
    <!DOCTYPE HTML>
<html>
<head>
    <meta charset="utf-8" name="viewport" content="width=device-width, initial-scale=1">
    <title>Picoink</title>
    <style>
        {byebye_style}
    </style>
</head>
<body>
    <div class="container">
        <p>Everything is set.</p>
        <p>Device is rebooting.</p>
        <p>Close the page please.</p>
    </div>
</body>
</html>
    """
    return byebye


def parse_request(request: str):
    # print(request)
    if request.startswith("GET /get?"):
        try:
            setting = (request[9:].split()[0].split("="))
            # print(setting[0], ": ", setting[1])
            if Settings.get(setting[0], None) is not None:
                Settings[setting[0]] = unquote(setting[1])
            elif sensor.settings.get(setting[0], None) is not None:
                sensor.settings[setting[0]] = unquote(setting[1])
            elif setting[0] == "save_form":
                return False

        except IndexError:
            print("Index error")

    return True


def save_and_restart(_):
    global Done
    if not Done:
        Done = True
        settings_save()
        sensor.settings_save()
        clear_display()
        AP.active(False)
        sleep_ms(1000)
        machine.reset()


def server_response(request):
    global SCR_partial

    server_in_progress = parse_request(request)
    if server_in_progress:
        response = web_page()
    else:
        response = byebye_page()
    server.send(response)

    if not server_in_progress:
        save_and_restart(None)

    all_settings = OrderedDict()
    all_settings.update(sensor.settings)
    all_settings.update(Settings)
    show_settings(all_settings, partial=SCR_partial)
    SCR_partial = True


def start_server():
    while not BTN_1.value():
        sleep_ms(200)
    sleep_ms(2000)
    BTN_1.irq(trigger=machine.Pin.IRQ_FALLING, handler=save_and_restart)
    server.add_route("/", server_response)
    server.on_not_found(server_response)
    server.start()


# def start_web():
#     while not BTN_1.value():
#         sleep_ms(200)
#     sleep_ms(2000)
#     BTN_1.irq(trigger=machine.Pin.IRQ_FALLING, handler=save_and_restart)
#     S.bind(('', 80))
#     S.listen(5)
#     scr_partial = False
#     while True:
#         conn, addr = S.accept()
#         request = conn.recv(2048)
#         request = request.decode("utf-8")
#         server_in_progress = parse_request(request)
#         if server_in_progress:
#             response = web_page()
#         else:
#             response = byebye_page()
#         conn.sendall(response)
#         conn.close()
#
#         if not server_in_progress:
#             save_and_restart(None)
#
#         all_settings = OrderedDict()
#         all_settings.update(sensor.settings)
#         all_settings.update(Settings)
#         show_settings(all_settings, partial=scr_partial)
#         scr_partial = True
