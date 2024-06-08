import json
from collections import OrderedDict

SEEK_END = 2


def num_to_byte(num, minimum, maximum):
    num = max(minimum, min(num, maximum))
    byte = int(((num - minimum) / (maximum - minimum)) * 256)
    byte = max(0, min(byte, 255))
    return byte
def byte_to_num(byte, minimum, maximum):
    byte = max(0, min(byte, 255))
    num = minimum + (byte / 255) * (maximum - minimum)
    return num


def get_last_values(num_of_vals, filename, max_filesize=1024 * 100):
    try:
        with open(filename, "rb") as f:
            f.seek(0, SEEK_END)
            filesize = f.tell()
            if filesize < num_of_vals:
                f.seek(-filesize, SEEK_END)
                values_binary = f.read(filesize)
            else:
                f.seek(-num_of_vals, SEEK_END)
                values_binary = f.read(num_of_vals)
            values = [vb for vb in values_binary]
    except OSError:
        return 0, []

    if filesize > max_filesize:
        with open(filename, "wb") as f:
            f.write(values_binary)
    return filesize, values


def save_value(value, filename):
    val_unsigned = value
    val_binary = val_unsigned.to_bytes(1, "big")
    try:
        with open(filename, "ab") as f:
            f.write(val_binary)
    except OSError:
        with open(filename, "wb") as f:
            f.write(val_binary)


Settings = OrderedDict()
Settings["WiFi-SSID"] = ""
Settings["WiFi-passw"] = ""
Settings["WiFi-IP"] = "DHCP"
Settings["MQTT-brokr"] = ""
Settings["MQTT-user"] = ""
Settings["MQTT-passw"] = ""
Settings["MQTT-name"] = ""
Settings["BLE-name"] = ""
Settings["widget"] = 0


def settings_load():
    try:
        with open("settings.json", "r") as f:
            loaded_settings = f.read()
            loaded_settings = json.loads(loaded_settings)
    except Exception as e:
        print(e)
        return
    else:
        unwanted_keys = set(loaded_settings) - set(Settings)
        for k in unwanted_keys:
            loaded_settings.pop(k, None)
        Settings.update(loaded_settings)


def settings_save():
    with open("settings.json", "w") as f:
        print(Settings)
        f.write(json.dumps(Settings))
