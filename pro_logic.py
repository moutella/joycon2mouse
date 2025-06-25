import vgamepad as vg

BUTTON_MASKS = {
    0x000800000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    0x000400000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    0x000200000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    0x000100000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    0x004000000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    0x000000400000: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    0x000000020000: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    0x000000040000: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
    0x000000010000: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    0x000000080000: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    0x000010000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
    0x000001000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    0x000002000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    0x000004000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    0x000008000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
}
TRIGGER_MASKS = {
    "LT": 0x000000800000,
    "RT": 0x008000000000,
}

def decode_joystick(data):
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

async def handle_pro_notification(sender, data, gamepad):
    if len(data) < 17:
        return
    state = int.from_bytes(data[3:9], byteorder='big')
    for mask, button in BUTTON_MASKS.items():
        gamepad.press_button(button) if state & mask else gamepad.release_button(button)
    gamepad.left_trigger(255 if state & TRIGGER_MASKS["LT"] else 0)
    gamepad.right_trigger(255 if state & TRIGGER_MASKS["RT"] else 0)
    lx, ly = decode_joystick(data[10:13])
    rx, ry = decode_joystick(data[13:16])
    gamepad.left_joystick(x_value=lx, y_value=ly)
    gamepad.right_joystick(x_value=rx, y_value=ry)
    gamepad.update()
