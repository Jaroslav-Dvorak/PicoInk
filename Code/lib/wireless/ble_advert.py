import bluetooth
import struct
from time import sleep
from nonvolatile import Settings


ble = bluetooth.BLE()
ble.active(True)


def ble_advert(characteristics):
    name = Settings["BLE-name"].encode("ASCII")
    compl_name_flag = b'\x09'
    length_part_1 = struct.pack("<B", len(compl_name_flag + name))

    msg_part_1 = b'\x02\x01\x06' + length_part_1 + compl_name_flag + name

    bthome_uuid = b'\x16\xd2\xfc'
    devinfo_flags = struct.pack("<B", 0b_0100_0100)

    msg_part_2 = bthome_uuid + devinfo_flags + characteristics
    length_part_2 = struct.pack("<B", len(msg_part_2))

    msg_part_2 = length_part_2 + msg_part_2

    msg = msg_part_1 + msg_part_2
    ble.gap_advertise(100_000, msg)
