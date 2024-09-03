from lib.wireless.ap import start_ap, start_web
from lib.display import screens


def start_setup(ap_ssid, batt_voltage):
    ip = start_ap(ap_ssid)
    screens.show_overview(batt_voltage, ip, ap_ssid)
    start_web()
