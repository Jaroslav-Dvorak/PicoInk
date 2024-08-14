from utime import sleep_ms, time
from lib.display.screens import text_row
from lib.wireless.ha import MQTT, send_discovery
from lib.wireless.sta import STA, wifi_connect
from lib.wireless.ble_advert import ble_advert
from sensor import sensor

from nonvolatile import Settings, settings_save
import network


WIFI_STATUS = {
    network.STAT_IDLE: "IDLE",
    network.STAT_CONNECTING: "CONNECTING",
    network.STAT_WRONG_PASSWORD: "WRONG_PASSWORD",
    network.STAT_NO_AP_FOUND: "NO_AP_FOUND",
    network.STAT_CONNECT_FAIL: "CONNECT_FAIL",
    2: "OBTAINING_IP",
    network.STAT_GOT_IP: "GOT_IP"
}

MQTT_ERRS = {
    1: "ECONCLOSE",
    2: "EREADLEN",
    3: "EWRITELEN",
    4: "ESTRTOLONG",
    6: "ERESPONSE",
    7: "EKEEPALIVE",
    8: "ENOCON",

    20: "ECONUNKNOWN",
    21: "ECONPROTOCOL",
    22: "ECONREJECT",
    23: "ECONUNAVAIBLE",
    24: "ECONCREDENTIALS",
    25: "ECONAUTH",
    28: "ECONNOT",
    29: "ECONLENGTH",
    30: "ECONTIMEOUT",

    40: "ESUBACKUNKNOWN",
    41: "ESUBACKFAIL"
}

Continue_message = "Press any button..."


def sensor_scan():
    if sensor.info:
        text_row(f"Sensor found: {sensor.info}", 1)
        sleep_ms(1000)
        return True
    else:
        text_row("Sensor not found", 1)


def ble_try_advertising(batt_soc):
    ble_name = Settings["BLE-name"]
    if ble_name:
        sensor.get_values()
        sensor.last_values["soc"] = batt_soc
        ble_advert(sensor.get_ble_characteristics())
        text_row("BLE started advertising.", 2)
    else:
        text_row("BLE is not set.", 2)


def check_settings():
    ssid = Settings["WiFi-SSID"]
    mqtt = Settings["MQTT-brokr"]
    if not ssid:
        text_row("WiFi is not set.", 3)
        text_row(Continue_message, 4)
        return False
    if not mqtt:
        text_row("MQTT is not set.", 3)
        text_row(Continue_message, 4)
        return False
    return True


def check_wifi():
    wifi_connect()
    text_row(f"Connecting to {Settings['WiFi-SSID']}", 3)
    start_time = time()
    try_time_s = 10
    while STA.status() != network.STAT_GOT_IP:
        status = WIFI_STATUS.get(STA.status(), "UNKNOWN STATUS")
        text_row(status, 4)
        sleep_ms(10)
        if time() > start_time+try_time_s:
            text_row("Wifi connection failed,", 5)
            text_row(Continue_message, 6)
            STA.disconnect()
            return False
    else:
        status = WIFI_STATUS.get(STA.status(), "UNKNOWN STATUS")
        text_row(status, 4)
        rssi = STA.status("rssi")
        text_row(f"WiFi connected, rssi:{rssi}dBm", 5)
    return True


def check_mqtt():
    text_row(f"MQTT connecting {MQTT.server}", 6)
    try:
        MQTT.connect()
        text_row("MQTT connected", 7)
    except Exception as e:
        text_row(str(e), 7)
        text_row(Continue_message, 8)
        return False
    else:
        return True


def try_ha_discovery():
    try:
        for name, (unit, devclass) in sensor.units_classes.items():
            send_discovery(name=name, unit=unit, device_class=devclass)

        send_discovery(name="soc", unit="%", device_class="battery")
        send_discovery(name="signal", unit="dBm", device_class="signal_strength")
        text_row("MQTT HA discovery published", 8)
    except Exception as e:
        if str(e).isdigit():
            e = int(str(e))
            e = MQTT_ERRS.get(e, "UNKNOWN ERROR")
            text_row(e, 8)
            text_row(Continue_message, 9)
        else:
            print(e)
        return False
    else:
        return True


def show_success():
    text_row("Everything OK :-)", 9)
    text_row(Continue_message, 10)
