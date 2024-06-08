from nonvolatile import Settings, settings_save, settings_load
settings_load()
wifi_active = Settings["WiFi-SSID"]
if wifi_active:
    from lib.wireless.sta import STA, wait_for_wifi_connection, wifi_connect
    wifi_connect()
ble_active = Settings["BLE-name"]
if ble_active:
    from lib.wireless.ble_advert import ble_advert, ble

from time import sleep_ms
from gpio_definitions import BTN_1, BTN_2, BTN_3, GREEN_LED, DONE_PIN
from measurement import batt_voltage, voltage_to_soc
from lib.display import screens
from sensor import sensor


if __name__ == '__main__':
    battery_voltage = batt_voltage()
    if battery_voltage < 2.8:
        DONE_PIN.value(1)
    bat_soc = voltage_to_soc(battery_voltage)

    device_run = True
    full_refresh = False
    if not BTN_1.value():
        from modes.mode_setup import start_setup
        start_setup("HBD_SETUP", battery_voltage)

    elif not BTN_2.value():
        import modes.mode_testing as testing
        screens.clear_display()
        if testing.sensor_scan():
            testing.ble_try_advertising(bat_soc)
            if testing.check_settings():
                if testing.check_wifi():
                    sleep_ms(100)
                    if testing.check_mqtt():
                        sleep_ms(100)
                        if testing.try_ha_discovery():
                            testing.show_success()
        del testing
        while BTN_1.value() and BTN_2.value() and BTN_3.value():
            sleep_ms(100)
        full_refresh = True

    elif not BTN_3.value():
        Settings["widget"] += 1
        if Settings["widget"] > 1:
            Settings["widget"] = 0
        settings_save()
        sleep_ms(1000)
        full_refresh = True

    if device_run:
        # mqtt_payload = {}
        from modes.mode_regular import load_show_save
        while True:
            load_show_save(full_refresh, bat_soc, sensor)
            sensor.last_values["soc"] = bat_soc
            if wifi_active:
                rssi = wait_for_wifi_connection()
                if rssi:
                    from lib.wireless.ha import send_state, connect_mqtt, MQTT
                    if connect_mqtt():
                        GREEN_LED.value(1)
                        sensor.last_values["signal"] = rssi
                        send_state(**sensor.last_values)
                        MQTT.wait_msg()
                        MQTT.disconnect()
                        sleep_ms(500)
                    # screens.widgets.rect()
                    screens.widgets.signal_indicator(rssi, 40, 10)
                    screens.eink.show(screens.widgets.img, partial=True)
                STA.disconnect()

            if ble_active:
                ble_advert(sensor.get_ble_characteristics())
                sleep_ms(500)
                ble.gap_advertise(None)

            if wifi_active:
                sleep_ms(1000)

            GREEN_LED.value(0)
            screens.eink.deep_sleep()
            sleep_ms(100)
            DONE_PIN.value(1)
            sleep_ms(10_000)

            if wifi_active:
                wifi_active = wifi_connect()

            full_refresh = False
