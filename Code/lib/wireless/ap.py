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
from lib.wireless.http_utils import unquote, parse_query_bytes, make_response


AP = network.WLAN(network.AP_IF)
S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
S.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
S.bind(('', 80))
S.listen(1)

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
                <label for="{k}">{k}:</label>
                <input type={form_type} id="{k}" name="{k}" value="{v}" onchange="this.form.submit();">
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
        <form method="post" action="/" accept-charset="UTF-8">
            <div class="form-group">
                {forms}
            </div>
            <input type="submit" value="OK">
        </form>
        <br>
            <form method="post" action="/" accept-charset="UTF-8">
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


def parse_request(request: dict):

    for k, v in request.items():
        if Settings.get(k) is not None:
            Settings[k] = v
        if sensor.settings.get(k) is not None:
            sensor.settings[k] = v

    if request.get("save_form"):
        return False

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


def start_web():
    global SCR_partial

    while not BTN_1.value():
        sleep_ms(200)
    sleep_ms(2000)
    BTN_1.irq(trigger=machine.Pin.IRQ_FALLING, handler=save_and_restart)

    while True:
        server_in_progress = True
        conn, addr = S.accept()

        request = bytes()
        while True:
            chunk = conn.recv(4096)
            request += chunk
            if b'\r\n\r\n' in request:
                break
            if not request:
                conn.close()
                conn, addr = S.accept()

        header, body = request.split(b'\r\n\r\n')
        print(header)

        if header.startswith(b'POST'):
            content_length_pos = header.find(b'Content-Length')
            chunk_size = 4096
            if content_length_pos != -1:
                content_length = header[content_length_pos:].split(b'\r\n')[0]
                content_length = int(content_length.split(b':')[1])
                content_length -= len(body)
            else:
                content_length = chunk_size

            while content_length > 0:
                body += conn.recv(chunk_size)
                content_length -= chunk_size


            parameters = parse_query_bytes(body)
            for k, v in parameters.items():
                print(k, v, sep=": ")

            server_in_progress = parse_request(parameters)

        if server_in_progress:
            response = make_response(web_page())
        else:
            response = make_response(byebye_page())

        all_settings = OrderedDict()
        all_settings.update(sensor.settings)
        all_settings.update(Settings)
        show_settings(all_settings, partial=SCR_partial)
        SCR_partial = True

        conn.send(response.encode())
        conn.close()

        if not server_in_progress:
            save_and_restart(None)

