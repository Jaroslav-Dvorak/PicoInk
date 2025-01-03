from measurement import batt_voltage, voltage_to_soc

battery_voltage = batt_voltage()
if battery_voltage < 2.6:                                   # turn off immediatelly to prevent draining battery
    from machine import Pin
    Pin(9, Pin.OUT).value(1)


if battery_voltage < 2.7:                                 # show battery dead screen then turn off
    from gpio_definitions import DONE_PIN, RED_LED
    from lib.display import screens
    from lib.templates import Low_batt_image
    from time import sleep_ms

    screens.widgets.clear()
    screens.widgets.image(Low_batt_image)
    screens.eink.show(screens.widgets.img, partial=False)
    sleep_ms(100)
    RED_LED.value(1)
    screens.eink.deep_sleep()
    sleep_ms(100)
    RED_LED.value(0)
    DONE_PIN.value(1)
    sleep_ms(1_000)
    screens.eink.epd_hw_init()


from gpio_definitions import BTN_1, BTN_2, BTN_3, GREEN_LED, DONE_PIN, RED_LED
from time import sleep_ms
if not BTN_1.value() and not BTN_2.value():
    count_down = 5
    while not BTN_1.value() and not BTN_2.value():
        print(count_down)
        count_down -= 1
        sleep_ms(1000)
        if count_down < 0:
            from lib.display import screens
            import os
            from machine import reset
            screens.widgets.tiny_text("FACTORY RESET?", 80, 50)
            screens.widgets.tiny_text("YES", 75, 110)
            screens.widgets.tiny_text("NO", 185, 110)
            screens.eink.show(screens.widgets.img, partial=False)
            def factory_reset():
                def delete_files(path):
                    try:
                        for entry in os.ilistdir(path):
                            entry_name = entry[0]
                            full_path = path + '/' + entry_name
                            try:
                                if os.stat(full_path)[0] & 0x4000:  # 0x4000 is flag for directory
                                    delete_files(full_path)  # Rekurzivly call this function
                                elif entry_name.endswith('.json') or entry_name.endswith('.dat'):
                                    os.remove(full_path)
                                    print("Deleted:", full_path)
                            except OSError as e:
                                print("Delete error {}: {}".format(full_path, e))
                    except OSError as e:
                        print("Reading error {}: {}".format(path, e))
                delete_files("/")

            buttons_released = False
            while True:
                if BTN_1.value() and BTN_2.value():
                    buttons_released = True
                t = 0
                if buttons_released:
                    while not BTN_1.value():
                        if t > 10:
                            factory_reset()
                            sleep_ms(100)
                            reset()
                        t += 1
                        sleep_ms(10)

                    if not BTN_2.value():
                        reset()


# Start Wireless ASAP
from nonvolatile import Settings, settings_save, settings_load
settings_load()
wifi_active = Settings["WiFi-SSID"]
if wifi_active:
    from lib.wireless.sta import STA, wait_for_wifi_connection, wifi_connect
    wifi_connect()
ble_active = Settings["BLE-name"]
if ble_active:
    from lib.wireless.ble_advert import ble_advert, ble


from lib.display import screens
from sensor import sensor

if __name__ == '__main__':
    device_run = True
    full_refresh = False

    bat_soc = voltage_to_soc(battery_voltage)

    if not BTN_1.value():
        from modes.mode_setup import start_setup
        start_setup("PICOINK", battery_voltage)

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
        if Settings["widget"] > 2:
            Settings["widget"] = 0
        settings_save()
        sleep_ms(1000)
        full_refresh = True

    if device_run:
        from modes.mode_regular import load_show_save
        while True:
            DONE_PIN.value(0)
            rssi = False
            mqtt_ok = False
            sensor_ok = load_show_save(full_refresh, bat_soc, sensor)
            sensor.last_values["soc"] = bat_soc
            if wifi_active:
                if sensor_ok:
                    rssi = wait_for_wifi_connection()
                else:
                    STA.disconnect()
                    rssi = None
                if rssi:
                    screens.widgets.signal_indicator(rssi)
                    screens.eink.show(screens.widgets.img, partial=True)
                    from lib.wireless.ha import send_state, connect_mqtt, MQTT
                    if connect_mqtt():
                        sensor.last_values["signal"] = rssi
                        if not send_state(**sensor.last_values):
                            screens.widgets.mqtt_indicator()
                            screens.eink.show(screens.widgets.img, partial=True)
                        MQTT.wait_msg()
                        MQTT.disconnect()
                        sleep_ms(200)
                        mqtt_ok = True
                    else:
                        screens.widgets.mqtt_indicator()
                        screens.eink.show(screens.widgets.img, partial=True)
                STA.disconnect()

            if ble_active and sensor_ok:
                ble_advert(sensor.get_ble_characteristics())
                sleep_ms(500)
                ble.gap_advertise(None)

            if wifi_active:
                sleep_ms(1000)

            if sensor_ok and bat_soc > 10 and ((rssi and mqtt_ok) or not wifi_active):
                GREEN_LED.value(1)
            else:
                RED_LED.value(1)

            screens.eink.deep_sleep()
            sleep_ms(100)
            GREEN_LED.value(0)
            RED_LED.value(0)
            DONE_PIN.value(1)
            sleep_ms(10_000)

            if wifi_active:
                wifi_connect()
                # wifi_active = wifi_connect()

            full_refresh = False
