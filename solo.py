# THIS FILE IS FOR: Solo JoyCon
import asyncio
from bleak import BleakScanner, BleakClient
import vgamepad as vg

JOYCON_MANUFACTURER_ID = 1363
JOYCON_MANUFACTURER_PREFIX = bytes([0x01, 0x00, 0x03, 0x7E])
INPUT_REPORT_UUID = "ab7de9be-89fe-49ad-828f-118f09df7fd2"

SL_MASK = 0x002000  # SL button mask on right Joy-Con
SR_MASK = 0x001000  # SR button mask on right Joy-Con
LEFT_SL_MASK = 0x000020
LEFT_SR_MASK = 0x000010

# Masks
MASKS = {
    "RIGHT": {
        "A":    (0x000800, vg.XUSB_BUTTON.XUSB_GAMEPAD_B),
        "B":    (0x000400, vg.XUSB_BUTTON.XUSB_GAMEPAD_Y),
        "X":    (0x000200, vg.XUSB_BUTTON.XUSB_GAMEPAD_A),
        "Y":    (0x000100, vg.XUSB_BUTTON.XUSB_GAMEPAD_X),
        "PLUS": (0x000004, vg.XUSB_BUTTON.XUSB_GAMEPAD_START),
        "R":    (0x004000, vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER),
        "RT":   0x008000,
        "STICK":(0x000004, vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
    },
    "LEFT": {
        "UP":     (0x000002, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT),
        "DOWN":   (0x000004, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT),
        "LEFT":   (0x000008, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN),
        "RIGHT":  (0x000001, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP),
        "MINUS":  (0x000100, vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK),
        "L":      (0x000040, vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER),
        "LT":     0x000080,
        "STICK":  (0x000008, vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)
    }
}

gamepad = vg.VX360Gamepad()

def decode_joystick(data, is_left, is_sideways=True):
    if len(data) != 3:
        return 0, 0
    x = ((data[1] & 0x0F) << 8) | data[0]
    y = (data[2] << 4) | ((data[1] & 0xF0) >> 4)
    x = (x - 2048) / 2048.0
    y = (y - 2048) / 2048.0
    # Always sideways transformation
    if is_sideways:
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

def parse_buttons(data, side, is_sideways=True):
    offset = 4 if side == "LEFT" else 3
    if len(data) < offset + 3:
        return
    state = int.from_bytes(data[offset:offset+3], byteorder='big')

    if side == "LEFT":
        # Left shoulder button
        gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER) if state & MASKS["LEFT"]["L"][0] else gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        gamepad.left_trigger(255 if state & MASKS["LEFT"]["LT"] else 0)

        # SL → left shoulder
        if state & LEFT_SL_MASK:
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        else:
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)

        # SR → right shoulder
        if state & LEFT_SR_MASK:
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
        else:
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)

    else:
        # Right Joy-Con shoulders and triggers
        gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER) if state & MASKS["RIGHT"]["R"][0] else gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
        gamepad.right_trigger(255 if state & MASKS["RIGHT"]["RT"] else 0)

        # SL → left shoulder (right Joy-Con)
        if state & SL_MASK:
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        else:
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)

        # SR → right shoulder (right Joy-Con)
        if state & SR_MASK:
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
        else:
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)

    # Regular buttons
    for name, val in MASKS[side].items():
        if name in ["L", "R", "LT", "RT"]:
            continue
        mask, vg_btn = val
        if state & mask:
            gamepad.press_button(vg_btn)
        else:
            gamepad.release_button(vg_btn)

async def notification_handler(sender, data, is_left):
    side = "LEFT" if is_left else "RIGHT"
    print(f"[{side}] Raw: {data.hex()}")  # <-- This line prints the raw notification
    parse_buttons(data, side, is_sideways=True)
    stick = data[10:13] if is_left else data[13:16]
    x, y = decode_joystick(stick, is_left, is_sideways=True)
    gamepad.left_joystick(x_value=x, y_value=y)  # always left stick
    gamepad.update()

async def scan_for_joycon():
    print("🔍 Scanning for Joy-Con (5s)...")
    found = None
    found_printed = False  # track if we've printed found message

    def cb(device, adv):
        nonlocal found, found_printed
        m = adv.manufacturer_data.get(JOYCON_MANUFACTURER_ID)
        if m and m.startswith(JOYCON_MANUFACTURER_PREFIX):
            if not found:
                found = device
            if not found_printed:
                print(f"✅ Found Joy-Con: {device.address}")
                found_printed = True

    scanner = BleakScanner(cb)
    await scanner.start()
    for _ in range(10):
        if found:
            break
        await asyncio.sleep(0.5)
    await scanner.stop()
    return found

async def main():
    device = await scan_for_joycon()
    if not device:
        print("❌ No Joy-Con found.")
        return
    client = BleakClient(device.address)
    await client.connect()
    print(f"🔗 Connected to Joy-Con at {device.address}")

    is_left = input("Is this Joy-Con Left or Right? (L/R): ").strip().upper() == "L"
    # Removed sideways input — always sideways
    is_sideways = True

    def cb(sender, data):
        asyncio.create_task(notification_handler(sender, data, is_left))
    await client.start_notify(INPUT_REPORT_UUID, cb)

    print("🎮 Joy-Con is now active.")
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
