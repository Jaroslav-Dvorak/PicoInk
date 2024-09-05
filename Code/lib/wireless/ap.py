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
from lib.wireless.http_utils import parse_query_bytes, make_response


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


def forms_generator():
    forms_sensor = '<div class="form-group">\n'
    for k, v in sensor.settings.items():
        if k[0].islower():
            continue
        form_type = "text"
        if k == "Offset":
            form_type = '"number" step="0.1"'
        elif k == "Minimum":
            form_type = '"number"'
        elif k == "Maximum":
            form_type = '"number"'

        forms_sensor += f"""
        <form method="post" action="/" accept-charset="UTF-8">
            <label for="{k}">{k}:</label>
            <div style="display: flex;">
                <input type={form_type} name="{k}" value="{v}" required>
                <input type="submit" value="WRITE">
            </div>
        </form>
        """
    forms_sensor += "</div>\n"
    forms_general = '<div class="form-group">\n'

    for k, v in Settings.items():
        if k[0].islower():
            continue
        form_type = "text"
        pattern = ".*"
        title = ""
        if k == "WiFi-SSID":
            pattern = r'^(?!\s)([\x20-\x7E]{0,32})(?<!\s)$'
            title = "No start/end spaces, max. 32 characters."
        elif k == "WiFi-passw":
            form_type = "password"
            pattern = r'^(|[\x20-\x7E]{8,63})$'
            title = "8-63 characters"
        elif k == "WiFi-IP":
            pattern = r'^$|^((?!0\.0\.0\.0)(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]?|[1-9])(\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]?|0)){3})\/([1-9]|[1-2][0-9]|3[0-2])$'
            title = "CIDR format. Example: 192.168.0.32/24 OR 10.0.0.154/8"
        elif k == "MQTT-brokr":
            pattern = r'^$|^(([01]?[0-9]?[0-9]|2([0-4][0-9]|5[0-5]))\.){3}([01]?[0-9]?[0-9]|2([0-4][0-9]|5[0-5]))$|^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])(\.([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]))*$'
            title = "IP address or DNS name. Example: 192.168.0.1 OR broker.pubmosq.com"
        elif k == "MQTT-user":
            pattern = r'^[a-zA-Z0-9._-]{0,64}$'
            title = "Max. 64 non-special characters."
        elif k == "MQTT-passw":
            form_type = "password"
            pattern = r'^[\x20-\x7E]{0,64}$'
            title = "Max. 64 characters."
        elif k == "MQTT-name":
            pattern = r'^[\x20-\x7E]{0,64}$'
            title = "Max. 64 characters."
        elif k == "BLE-name":
            pattern = r'^[\x20-\x7E]{0,11}$'
            title = "Max. 11 characters."

        forms_general += f"""
        <form method="post" action="/" accept-charset="UTF-8">
            <label for="{k}">{k}:</label>
            <div style="display: flex;">
                <input type="{form_type}" name="{k}" value="{v}" pattern="{pattern}" title="{title}">
                <input type="submit" value="WRITE">
            </div>
        </form>
        """
    forms_general += "</div>\n"

    forms = forms_sensor+forms_general
    with open("html.html", "w") as f:
        f.write(forms)
    return forms


def web_page():
    forms = forms_generator()
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
        <br>
        <br>
        <br>
            <form method="post" action="/" accept-charset="UTF-8">
                <input type="text" id="save_form" name="save_form" value="save_form" style=display:None>
                <input type="submit" value="SAVE AND RESTART" style="height: 4rem;">
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

