import vgamepad as vg

# Button masks
SL_MASK = 0x002000
SR_MASK = 0x001000
LEFT_SL_MASK = 0x000020
LEFT_SR_MASK = 0x000010

MASKS = {
    "RIGHT": {
        "A":    (0x000400, vg.XUSB_BUTTON.XUSB_GAMEPAD_B),
        "B":    (0x000800, vg.XUSB_BUTTON.XUSB_GAMEPAD_Y),
        "X":    (0x000100, vg.XUSB_BUTTON.XUSB_GAMEPAD_A),
        "Y":    (0x000200, vg.XUSB_BUTTON.XUSB_GAMEPAD_X),
        "PLUS": (0x000002, vg.XUSB_BUTTON.XUSB_GAMEPAD_START),
        "R":    (0x004000, vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER),
        "RT":   0x008000,
        "STICK":(0x000004, vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
    },
    "LEFT": {
        "UP":     (0x000002, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT),
        "DOWN":   (0x000001, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT),
        "LEFT":   (0x000008, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN),
        "RIGHT":  (0x000004, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP),
        "MINUS":  (0x000100, vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK),
        "L":      (0x000040, vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER),
        "LT":     0x000080,
        "STICK":  (0x000800, vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)
    }
}

def decode_joystick(data, is_left):
    if len(data) != 3:
        return 0, 0
    x = ((data[1] & 0x0F) << 8) | data[0]
    y = (data[2] << 4) | ((data[1] & 0xF0) >> 4)
    x = (x - 2048) / 2048.0
    y = (y - 2048) / 2048.0
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

async def handle_single_notification(sender, data, is_left, gamepad):
    side = "LEFT" if is_left else "RIGHT"
    offset = 4 if is_left else 3
    state = int.from_bytes(data[offset:offset+3], 'big')

    # Triggers
    if is_left:
        gamepad.left_trigger(255 if state & MASKS["LEFT"]["LT"] else 0)
    else:
        gamepad.right_trigger(255 if state & MASKS["RIGHT"]["RT"] else 0)

    # SL / SR as shoulders
    if is_left:
        gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER) if state & LEFT_SL_MASK else gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER) if state & LEFT_SR_MASK else gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
    else:
        gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER) if state & SL_MASK else gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER) if state & SR_MASK else gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)

    # Buttons
    for name, val in MASKS[side].items():
        if name in ["L", "R", "LT", "RT"]:
            continue
        mask, vg_btn = val
        if state & mask:
            gamepad.press_button(vg_btn)
        else:
            gamepad.release_button(vg_btn)

    # Stick
    stick = data[10:13] if is_left else data[13:16]
    x, y = decode_joystick(stick, is_left)
    gamepad.left_joystick(x_value=x, y_value=y)
    gamepad.update()
