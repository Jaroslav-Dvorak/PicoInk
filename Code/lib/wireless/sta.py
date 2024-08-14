from time import sleep_ms, time
import network
from nonvolatile import Settings

STA = network.WLAN(network.STA_IF)


def wifi_connect():
    STA.active(True)
    STA.config(pm=0xa11140)  # Diable powersave mode
    if Settings["WiFi-IP"] != "DHCP":
        ip, cidr = Settings["WiFi-IP"].split("/")
        cidr = int(cidr)
        mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
        netmask = (str((0xff000000 & mask) >> 24) + '.' +
                   str((0x00ff0000 & mask) >> 16) + '.' +
                   str((0x0000ff00 & mask) >> 8) + '.' +
                   str((0x000000ff & mask)))
        STA.ifconfig((ip, netmask, '0.0.0.0', '0.0.0.0'))
    if Settings["WiFi-passw"]:
        STA.connect(Settings["WiFi-SSID"], Settings["WiFi-passw"])
    else:
        STA.config(security=0)
        STA.connect(Settings["WiFi-SSID"])


def wait_for_wifi_connection():
    start_time = time()
    try_time_s = 10
    while STA.status() != network.STAT_GOT_IP:
        sleep_ms(100)
        if time() > start_time + try_time_s:
            STA.disconnect()
            return False
    else:
        sleep_ms(200)
        rssi = STA.status("rssi")
        return rssi

# def wait_for_wifi_connection():
#     max_s_wait = 5
#     while STA.status() != network.STAT_GOT_IP:
#         sleep_ms(1000)
#         if max_s_wait < 0:
#             print('wireless connection failed')
#             return False
#         max_s_wait -= 1
#     else:
#         print('connected')
#         status = STA.ifconfig()
#         print('ip = ' + status[0])
#         print(STA.status("rssi"))
#         return STA.status("rssi")


# def disconnect():
#     try:
#         MQTT.disconnect()
#         STA.disconnect()
#         return True
#     except Exception as e:
#         print(e)
#         return False
