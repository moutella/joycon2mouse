import vgamepad as vg

BUTTONS = {
    "RIGHT": {
        "A":     (0x000400, vg.XUSB_BUTTON.XUSB_GAMEPAD_A),
        "B":     (0x000800, vg.XUSB_BUTTON.XUSB_GAMEPAD_B),
        "X":     (0x000100, vg.XUSB_BUTTON.XUSB_GAMEPAD_X),
        "Y":     (0x000200, vg.XUSB_BUTTON.XUSB_GAMEPAD_Y),
        "PLUS":  (0x000002, vg.XUSB_BUTTON.XUSB_GAMEPAD_START),
        "STICK": (0x000004, vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB),
    },
    "LEFT": {
        "UP":     (0x000002, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP),
        "DOWN":   (0x000001, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN),
        "LEFT":   (0x000008, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT),
        "RIGHT":  (0x000004, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT),
        "MINUS":  (0x000100, vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK),
        "STICK":  (0x000800, vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB),
    }
}

def decode_joystick(data):
    x = ((data[1] & 0x0F) << 8) | data[0]
    y = (data[2] << 4) | ((data[1] & 0xF0) >> 4)
    x = max(-1.0, min(1.0, (x - 2048) / 2048.0 * 1.7))
    y = max(-1.0, min(1.0, (y - 2048) / 2048.0 * 1.7))
    return int(x * 32767), int(y * 32767)

async def handle_duo_notification(sender, data, side, gamepad):
    offset = 4 if side == "LEFT" else 3
    state = int.from_bytes(data[offset:offset+3], 'big')
    changed = False

    # Init previous state if not present
    if not hasattr(gamepad, "_last_inputs"):
        gamepad._last_inputs = {
            "buttons": {},
            "left_trigger": -1,
            "right_trigger": -1,
            "left_joystick": (None, None),
            "right_joystick": (None, None),
            "left_shoulder": None,
            "right_shoulder": None,
        }

    last = gamepad._last_inputs

    # Shoulder + Trigger + Stick
    if side == "LEFT":
        # Shoulder
        press = bool(state & 0x000040)
        if press != last["left_shoulder"]:
            if press:
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
            last["left_shoulder"] = press
            changed = True

        # Trigger
        trigger_val = 255 if state & 0x000080 else 0
        if trigger_val != last["left_trigger"]:
            gamepad.left_trigger(trigger_val)
            last["left_trigger"] = trigger_val
            changed = True

        # Joystick
        stick = data[10:13]
        x, y = decode_joystick(stick)
        if (x, y) != last["left_joystick"]:
            gamepad.left_joystick(x_value=x, y_value=y)
            last["left_joystick"] = (x, y)
            changed = True

    else:  # RIGHT
        press = bool(state & 0x004000)
        if press != last["right_shoulder"]:
            if press:
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
            last["right_shoulder"] = press
            changed = True

        trigger_val = 255 if state & 0x008000 else 0
        if trigger_val != last["right_trigger"]:
            gamepad.right_trigger(trigger_val)
            last["right_trigger"] = trigger_val
            changed = True

        stick = data[13:16]
        x, y = decode_joystick(stick)
        if (x, y) != last["right_joystick"]:
            gamepad.right_joystick(x_value=x, y_value=y)
            last["right_joystick"] = (x, y)
            changed = True

    # Digital Buttons
    for name, (mask, btn) in BUTTONS[side].items():
        pressed = bool(state & mask)
        if last["buttons"].get(btn) != pressed:
            if pressed:
                gamepad.press_button(btn)
            else:
                gamepad.release_button(btn)
            last["buttons"][btn] = pressed
            changed = True

    if changed:
        gamepad.update()
