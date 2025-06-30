import vgamepad as vg

# Button masks (based on extended bitfield for NSO GC controller)
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

# Trigger bit masks
TRIGGER_MASKS = {
    "LT": 0x000000800000,
    "RT": 0x008000000000,
}

def decode_joystick(data, label=""):
    if len(data) != 3:
        print(f"⚠️ {label} joystick: invalid data length {len(data)}")
        return 0, 0
    x = ((data[1] & 0x0F) << 8) | data[0]
    y = (data[2] << 4) | ((data[1] & 0xF0) >> 4)

    x_norm = (x - 2048) / 2048.0
    y_norm = (y - 2048) / 2048.0

    print(f"🕹️ {label} joy raw: {data.hex()} | x={x} y={y} | norm=({x_norm:.2f}, {y_norm:.2f})")

    deadzone = 0.08
    if abs(x_norm) < deadzone and abs(y_norm) < deadzone:
        return 0, 0

    x_norm = max(-1.0, min(1.0, x_norm * 1.7))
    y_norm = max(-1.0, min(1.0, y_norm * 1.7))

    return int(x_norm * 32767), int(y_norm * 32767)

async def handle_gc_notification(sender, data, gamepad):
    if len(data) < 22:
        print("⚠️ Packet too short:", len(data))
        return

    print(f"\n📥 Notification ({len(data)} bytes): {data.hex()}")

    button_bytes = data[3:10]
    state = int.from_bytes(button_bytes, byteorder='big')
    print(f"🎯 Button state raw: {button_bytes.hex()} | int: {state:#014x}")

    for mask, button in BUTTON_MASKS.items():
        if state & mask:
            print(f"🔘 Press: {button}")
            gamepad.press_button(button)
        else:
            gamepad.release_button(button)

    lt = 255 if state & TRIGGER_MASKS["LT"] else 0
    rt = 255 if state & TRIGGER_MASKS["RT"] else 0
    print(f"🔺 LT: {lt} | RT: {rt}")
    gamepad.left_trigger(lt)
    gamepad.right_trigger(rt)

    # Joystick decoding with logging
    lx, ly = decode_joystick(data[10:13], "Left")
    rx, ry = decode_joystick(data[13:16], "Right")

    gamepad.left_joystick(x_value=lx, y_value=ly)
    gamepad.right_joystick(x_value=rx, y_value=ry)

    gamepad.update()
