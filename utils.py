
import sys
from os import path
import platform

# Constants
JOYCON_MANUFACTURER_ID = 1363
JOYCON_MANUFACTURER_PREFIX = bytes([0x01, 0x00, 0x03, 0x7E])

# BLE GATT Characteristics UUID
INPUT_REPORT_UUID = "ab7de9be-89fe-49ad-828f-118f09df7fd2"
WRITE_COMMAND_UUID = "649d4ac9-8eb7-4e6c-af44-1ea54fe5f005"

# COMMANDS
COMMAND_LEDS = 0x09
COMMAND_VIBRATION = 0x0A

# SUBCOMMANDS
SUBCOMMAND_SET_PLAYER_LEDS = 0x07
SUBCOMMAND_PLAY_VIBRATION_PRESET = 0x02


def decode_joystick(data):
    try:
        if len(data) != 3:
            return 0, 0
        x = ((data[1] & 0x0F) << 8) | data[0]
        y = (data[2] << 4) | ((data[1] & 0xF0) >> 4)
        x = (x - 2048) / 2048.0
        y = (y - 2048) / 2048.0
        deadzone = 0.08
        if abs(x) < deadzone and abs(y) < deadzone:
            return 0, 0
        x = max(-1.0, min(1.0, x * 1.7))
        y = max(-1.0, min(1.0, y * 1.7))
        return int(x * 32767), int(y * 32767)
    except:
        return 0, 0
    

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    system = platform.system()
    if system == "Windows":
        base_path = getattr(sys, '_MEIPASS', path.dirname(path.abspath(__file__)))
        return path.join(base_path, relative_path)
    else:
        return relative_path
