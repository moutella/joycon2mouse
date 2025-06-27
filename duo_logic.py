import vgamepad as vg

BUTTONS = {
    "RIGHT": {
        "A":     (0x000400, vg.XUSB_BUTTON.XUSB_GAMEPAD_A),
        "B":     (0x000800, vg.XUSB_BUTTON.XUSB_GAMEPAD_B),
        "X":     (0x000100, vg.XUSB_BUTTON.XUSB_GAMEPAD_X),
        "Y":     (0x000200, vg.XUSB_BUTTON.XUSB_GAMEPAD_Y),
        "PLUS":  (0x000002, vg.XUSB_BUTTON.XUSB_GAMEPAD_START),
        "STICK": (0x000004, vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB),
        "HOME": (0x001000, vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE)
    },
    "LEFT": {
        "UP":     (0x000002, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP),
        "DOWN":   (0x000001, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN),
        "LEFT":   (0x000008, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT),
        "RIGHT":  (0x000004, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT),
        "MINUS":  (0x000100, vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK),
        "STICK":  (0x000800, vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB),
        # "CAPTURE": (0x002000, vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE) commented out, not enough buttons for this
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

    # Shoulder + Trigger
    if side == "LEFT":
        gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER) if state & 0x000040 else gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        gamepad.left_trigger(255 if state & 0x000080 else 0)
        stick = data[10:13]
        x, y = decode_joystick(stick)
        gamepad.left_joystick(x_value=x, y_value=y)
    else:
        gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER) if state & 0x004000 else gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
        gamepad.right_trigger(255 if state & 0x008000 else 0)
        stick = data[13:16]
        x, y = decode_joystick(stick)
        gamepad.right_joystick(x_value=x, y_value=y)

    # Digital buttons
    for name, (mask, btn) in BUTTONS[side].items():
        if state & mask:
            gamepad.press_button(btn)
        else:
            gamepad.release_button(btn)

    gamepad.update()
