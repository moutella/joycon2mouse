# This file is for: DUO JoyCons
import asyncio
from bleak import BleakScanner, BleakClient
import vgamepad as vg

# Constants
JOYCON_MANUFACTURER_ID = 1363
JOYCON_MANUFACTURER_PREFIX = bytes([0x01, 0x00, 0x03, 0x7E])
INPUT_REPORT_UUID = "ab7de9be-89fe-49ad-828f-118f09df7fd2"

# Button masks
BUTTONS = {
    "RIGHT": {
        "A":     (0x000800, vg.XUSB_BUTTON.XUSB_GAMEPAD_A),
        "B":     (0x000400, vg.XUSB_BUTTON.XUSB_GAMEPAD_B),
        "X":     (0x000200, vg.XUSB_BUTTON.XUSB_GAMEPAD_X),
        "Y":     (0x000100, vg.XUSB_BUTTON.XUSB_GAMEPAD_Y),
        "PLUS":  (0x000002, vg.XUSB_BUTTON.XUSB_GAMEPAD_START),
        "STICK": (0x000008, vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB),
        # Don't include "R" (shoulder) or trigger in this dictionary anymore
    },
    "LEFT": {
        "UP":     (0x000002, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP),
        "DOWN":   (0x000004, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN),
        "LEFT":   (0x000008, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT),
        "RIGHT":  (0x000001, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT),
        "MINUS":  (0x000100, vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK),
        "STICK":  (0x000800, vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB),
        # Don't include "L" (shoulder) or trigger here either
    }
}


gamepad = vg.VX360Gamepad()

def decode_joystick(data):
    if len(data) != 3:
        raise ValueError("Joystick data must be 3 bytes")
    x = ((data[1] & 0x0F) << 8) | data[0]
    y = (data[2] << 4) | ((data[1] & 0xF0) >> 4)
    x = max(-1.0, min(1.0, (x - 2048) / 2048.0 * 1.7))
    y = max(-1.0, min(1.0, (y - 2048) / 2048.0 * 1.7))
    x_scaled = int(x * 32767)
    y_scaled = int(y * 32767)
    return x_scaled, y_scaled

def parse_buttons(data, side):
    offset = 4 if side == "LEFT" else 3
    if len(data) < offset + 3:
        return
    state = int.from_bytes(data[offset:offset+3], byteorder='big')

    # Shoulders
    if side == "LEFT":
        gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER) if state & 0x000040 else gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
    if side == "RIGHT":
        gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER) if state & 0x004000 else gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)

    # Triggers (simulate analog with 255/0)
    if side == "LEFT":
        gamepad.left_trigger(255 if state & 0x000080 else 0)
    if side == "RIGHT":
        gamepad.right_trigger(255 if state & 0x008000 else 0)

    # All other digital buttons
    for name, (mask, vg_button) in BUTTONS[side].items():
        if name in ["L", "R"]:  # skip shoulders (already handled)
            continue
        if state & mask:
            gamepad.press_button(vg_button)
        else:
            gamepad.release_button(vg_button)

async def handle_notifications(client, side):
    async def callback(sender, data):
        try:
            parse_buttons(data, side)
            if side == "LEFT":
                stick = data[10:13]
                x, y = decode_joystick(stick)
                gamepad.left_joystick(x_value=x, y_value=y)
            else:
                stick = data[13:16]
                x, y = decode_joystick(stick)
                gamepad.right_joystick(x_value=x, y_value=y)
            gamepad.update()
        except Exception as e:
            print(f"[{side}] Error: {e}")
    await client.start_notify(INPUT_REPORT_UUID, callback)

async def scan_for_joycon(prompt):
    print(f"\n🔍 Now press a button on your {prompt} Joy-Con...")
    found = None

    def detection_callback(device, adv):
        data = adv.manufacturer_data.get(JOYCON_MANUFACTURER_ID)
        if data and data.startswith(JOYCON_MANUFACTURER_PREFIX):
            nonlocal found
            if not found:
                print(f"✅ Found {prompt} Joy-Con: {device.address}")
                found = device

    scanner = BleakScanner(detection_callback)
    await scanner.start()
    for _ in range(30):
        if found:
            break
        await asyncio.sleep(0.5)
    await scanner.stop()
    return found

async def main():
    print("🎮 Starting Dual Joy-Con Controller Setup")

    # Scan and connect to Right Joy-Con
    right = await scan_for_joycon("RIGHT")
    if not right:
        print("❌ Right Joy-Con not found.")
        return
    client_r = BleakClient(right.address)
    await client_r.connect()
    print(f"🔗 Connected to RIGHT Joy-Con at {right.address}")
    await handle_notifications(client_r, "RIGHT")

    # Scan and connect to Left Joy-Con
    left = await scan_for_joycon("LEFT")
    if not left:
        print("❌ Left Joy-Con not found.")
        return
    client_l = BleakClient(left.address)
    await client_l.connect()
    print(f"🔗 Connected to LEFT Joy-Con at {left.address}")
    await handle_notifications(client_l, "LEFT")

    print("🎮 Joy-Cons are now active. Press buttons or move sticks.")

    # Keep the loop alive
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
