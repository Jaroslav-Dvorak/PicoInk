from gpio_definitions import BATT_ADC, TEMPER_ADC


def measure_analog(pin):
    num_of_measurements = 1000
    n = 0
    measured = 0
    while n < num_of_measurements:
        measured += pin.read_u16()
        n += 1
    voltage = (measured / num_of_measurements) * (3.3 / 65535)
    return voltage


def batt_voltage():
    return round(measure_analog(BATT_ADC)*2 + 0.465, 2)
def voltage_to_soc(voltage):
    max_batt_volt = 4.20
    min_batt_volt = 2.80
    soc = int(((voltage - min_batt_volt) / (max_batt_volt - min_batt_volt)) * 100)
    soc = max(0, min(soc, 100))
    return soc


def onboard_temperature():
    temper_onboard_voltage = measure_analog(TEMPER_ADC)
    temperature = (27 - (temper_onboard_voltage - 0.706) / 0.001721)
    temperature = round(temperature, 1)
    return temperature


# def measure_dallas():
#     ds_sensor = DS18X20(OneWire(DALLAS))
#     rom = Settings["dallas_sens"]
#     rom = bytes.fromhex(rom)
#     try:
#         ds_sensor.convert_temp()
#         sleep_ms(750)
#         temp = ds_sensor.read_temp(rom)
#     except Exception as e:
#         print(e)
#         return False
#     else:
#         return round(temp, 1)
#
#
# def measure_scd4x():
#     scd4x = SCD4X(I2C)
#     scd4x.measure_single_shot()
#     return scd4x.co2
