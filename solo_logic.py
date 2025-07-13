import asyncio
import pyautogui
from joycon import JoyCon

pyautogui.FAILSAFE = False          # keep the corner-abort feature
pyautogui.PAUSE   = 0              # disable the global 100 ms pause
pyautogui.MINIMUM_DURATION = 0     # no forced smoothing

# from mouse_simulator import *

# Button masks

def decode_gyro(data: bytes):
    if len(data) < 0x3C:
        return None

    def to_signed_16(b1, b2):
        return int.from_bytes(bytes([b1, b2]), byteorder='little', signed=True)

    gyro_x_raw = to_signed_16(data[0x36], data[0x37])
    gyro_y_raw = to_signed_16(data[0x38], data[0x39])
    gyro_z_raw = to_signed_16(data[0x3A], data[0x3B])

    scale = 360 / 48000

    gyro_x = gyro_x_raw * scale
    gyro_y = gyro_y_raw * scale
    gyro_z = gyro_z_raw * scale

    return gyro_x, gyro_y, gyro_z

def decode_accel(data: bytes):
    if len(data) < 0x36:  # accel bytes end at 0x35 (0x30..0x35)
        return None

    def to_signed_16(b1, b2):
        return int.from_bytes(bytes([b1, b2]), byteorder='little', signed=True)

    accel_x_raw = to_signed_16(data[0x30], data[0x31])
    accel_y_raw = to_signed_16(data[0x32], data[0x33])
    accel_z_raw = to_signed_16(data[0x34], data[0x35])

    scale = 1 / 4096  # 4096 = 1G

    accel_x = accel_x_raw * scale
    accel_y = accel_y_raw * scale
    accel_z = accel_z_raw * scale

    return accel_x, accel_y, accel_z
# BC CB 00 00 10 00 00 E0 FF 0F FF F7 7F DD 07 7E A4 00 74 01 77 11 77 0C 00 00 00 00 00 00 00 4D 0E 00 00 00 00 00 00 00 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
# SR


async def handle_single_notification(sender, data, is_left, gamepad: JoyCon, upright):
    # 57 26 00 00 00 00 00 E0 FF 0F FF F7 7F F6 C7 7D 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 5C 0E 00 00 00 00 00 00 00 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    hex_str = ' '.join(f'{b:02X}' for b in data)
    # print(hex_str[48:75])
    # print(hex_str)
    side = "LEFT" if is_left else "RIGHT"
    offset = 4 if is_left else 3
    
    gamepad.process_mouse(data)
    gamepad.process_buttons(data)
    gamepad.process_sticks(data)
    # === BUTTONS ===
   

    # === STICK ===

    # if (x, y) != gamepad._last_joystick:
    #     gamepad.left_joystick(x_value=x, y_value=y)
    #     gamepad._last_joystick = (x, y)
    #     changed = True

    # # Only update if something changed
    # if changed:
    #     gamepad.update()
