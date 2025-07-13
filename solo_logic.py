import asyncio
import pyautogui

pyautogui.FAILSAFE = True          # keep the corner-abort feature
pyautogui.PAUSE   = 0              # disable the global 100 ms pause
pyautogui.MINIMUM_DURATION = 0     # no forced smoothing

# from mouse_simulator import *

# Button masks
SL_MASK = 0x002000
SR_MASK = 0x001000
LEFT_SL_MASK = 0x000020
LEFT_SR_MASK = 0x000010

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


last_mouse_pos = (None, None)
def decode_mouse(data: bytes):
    global last_mouse_pos
    if len(data) < 0x3c:
        return None
    mouse_data = data[0x10:0x18]
    mouse_hex_str = ' '.join(f'{b:02X}' for b in mouse_data)
    # print(hex_str[48:75])
    # print(mouse_hex_str)


    def to_signed_16(b1, b2):
        return int.from_bytes(bytes([b1, b2]), byteorder='little', signed=True)
    

    mouse_x_raw = to_signed_16(mouse_data[0x00], mouse_data[0x01]) 
    mouse_y_raw = to_signed_16(mouse_data[0x02], mouse_data[0x03])
    if last_mouse_pos[0] is not None:
        mouse_x_delta = mouse_x_raw - last_mouse_pos[0]
        mouse_y_delta = mouse_y_raw - last_mouse_pos[1]
            # posicao_atual = pyautogui.position()
            # posicao_futura = (posicao_atual[0] - mouse_x_delta, posicao_atual[1] - mouse_y_delta)
            # pyautogui.moveTo(posicao_futura)
        pyautogui.moveRel(mouse_x_delta, mouse_y_delta, duration=0)
        last_mouse_pos = (mouse_x_raw, mouse_y_raw)
    else:
        last_mouse_pos = (mouse_x_raw, mouse_y_raw)
    # print(mouse_x_raw, mouse_y_raw)
    # if abs(mouse_x) < 5:
    #     mouse_x = 0
    # if abs(mouse_y) < 5:
    #     mouse_y = 0

    # return mouse_x, mouse_y

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
UPRIGHT_MASKS = {
    "RIGHT": {
        "A":    (0x000800, "XUSB_BUTTON.XUSB_GAMEPAD_A"),
        "B":    (0x000400, "XUSB_BUTTON.XUSB_GAMEPAD_B"),
        "X":    (0x000200, "XUSB_BUTTON.XUSB_GAMEPAD_X"),
        "Y":    (0x000100, "XUSB_BUTTON.XUSB_GAMEPAD_Y"),
        "PLUS": (0x000002, "XUSB_BUTTON.XUSB_GAMEPAD_START"),
        "STICK":(0x000004, "XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB"),
    },
    "LEFT": {
        "UP":     (0x000002, "XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP"),
        "DOWN":   (0x000001, "XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN"),
        "LEFT":   (0x000008, "XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT"),
        "RIGHT":  (0x000004, "XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT"),
        "MINUS":  (0x000100, "XUSB_BUTTON.XUSB_GAMEPAD_BACK"),
        "STICK":  (0x000800, "XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB"),
    }
}
def decode_joystick(data, is_left, upright):
    if len(data) != 3:
        return 0, 0
    x = ((data[1] & 0x0F) << 8) | data[0]
    y = (data[2] << 4) | ((data[1] & 0xF0) >> 4)
    x = (x - 2048) / 2048.0
    y = (y - 2048) / 2048.0

    # ✅ Correct orientation handling
    if upright:
        # Leave x/y alone for both sides
        pass
    else:
        # Sideways orientation compensation
        if is_left:
            x, y = -y, x
        else:
            x, y = y, -x

    deadzone = 0.08
    if abs(x) < deadzone and abs(y) < deadzone:
        return 0, 0
    x = max(-1.0, min(1.0, x * 1.7))
    y = max(-1.0, min(1.0, y * 1.7))
    return int(x * 32767), int(y * 32767)

async def handle_single_notification(sender, data, is_left, gamepad, upright):
    # print(data)
    # Convert data to readable hex string, separated every 2 characters
    # example 
    # 57 26 00 00 00 00 00 E0 FF 0F FF F7 7F F6 C7 7D 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 5C 0E 00 00 00 00 00 00 00 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    # hex_str = ' '.join(f'{b:02X}' for b in data)
    # print(hex_str[48:75])
    # print(hex_str)
    side = "LEFT" if is_left else "RIGHT"
    offset = 4 if is_left else 3
    state = int.from_bytes(data[offset:offset+3], 'big')

    # # Initialize state storage if missing
    # if not hasattr(gamepad, "_last_buttons_state"):
    #     gamepad._last_buttons_state = 0
    # if not hasattr(gamepad, "_last_left_trigger"):
    #     gamepad._last_left_trigger = 0
    # if not hasattr(gamepad, "_last_right_trigger"):
    #     gamepad._last_right_trigger = 0
    # if not hasattr(gamepad, "_last_joystick"):
    #     gamepad._last_joystick = (0, 0)

    changed = False

    mouse = decode_mouse(data)
    if mouse is not None:
        pass

    # Decode and print gyro values
    # gyro = decode_gyro(data)
    # if gyro is not None:
    #     gyro_x, gyro_y, gyro_z = gyro

    # accel = decode_accel(data)
    # if accel is not None:
    #     accel_x, accel_y, accel_z = accel

    # === TRIGGERS & SHOULDERS ===
    # Upright config triggers/shoulders
    # if upright:
    #     new_left_trigger = 255 if state & 0x000080 else 0
    #     new_right_trigger = 255 if state & 0x008000 else 0
    #     new_left_shoulder = bool(state & 0x000040)
    #     new_right_shoulder = bool(state & 0x004000)
    # else:
    #     new_left_trigger = 255 if state & MASKS["LEFT"]["LT"] else 0
    #     new_right_trigger = 255 if state & MASKS["RIGHT"]["RT"] else 0
    #     new_left_shoulder = bool(state & (0x000020 if is_left else 0x002000))
    #     new_right_shoulder = bool(state & (0x000010 if is_left else 0x001000))

    # Update triggers
    # if new_left_trigger != gamepad._last_left_trigger:
    #     gamepad.left_trigger(new_left_trigger)
    #     gamepad._last_left_trigger = new_left_trigger
    #     changed = True

    # if new_right_trigger != gamepad._last_right_trigger:
    #     gamepad.right_trigger(new_right_trigger)
    #     gamepad._last_right_trigger = new_right_trigger
    #     changed = True


    # === BUTTONS ===
    button_map = UPRIGHT_MASKS[side]
    for name, val in button_map.items():
        if name in ["L", "R", "LT", "RT"]:
            continue  # Already handled above
        mask, vg_btn = val
        pressed = bool(state & mask)
        # last_pressed = getattr(gamepad, f"_last_btn_{vg_btn}", None)
        last_pressed = gamepad["last_pressed"] if "last_pressed" in gamepad else None
        if pressed != last_pressed:
            if pressed:
                if name == "A":
                    print("clicou")
                    pyautogui.click()
                if name == "B":
                    pyautogui.click(button='right')
                # print(f"pressed {name}")
            else:
                pass
                # print("Sem botão")
            gamepad["last_pressed"] = pressed
            changed = True

    # === STICK ===
    stick = data[10:13] if is_left else data[13:16]
    x, y = decode_joystick(stick, is_left, upright)

    # if (x, y) != gamepad._last_joystick:
    #     gamepad.left_joystick(x_value=x, y_value=y)
    #     gamepad._last_joystick = (x, y)
    #     changed = True

    # # Only update if something changed
    # if changed:
    #     gamepad.update()
