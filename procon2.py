# FILE FOR PEOPLE WITH A PRO CONTROLLER 2. USE THIS FILE TO GIVE ME DATA ABOUT PROCON2, IT DOESNT WORK FOR NORMAL USE YET
# Hey! If you're using this, thank you so much for helping out!
# This code is basically just solo.py but it prints raw notification data and has no side/sideways checks.
# Unsure if stick data will be interpreted correctly as the bits could be in different places.
# This is where YOU come in! Boot up the script, connect your ProCon2, and move your stick around/press buttons and send me the notif data that comes out!
# I'll then update the script to adjust to that data, and it should work just fine.
# Again, thank you for checking out the project! I hope that, when all of this is said and done, it can be fleshed out to be the best it can be!
# - Frano

import asyncio
from bleak import BleakScanner, BleakClient
import vgamepad as vg
import traceback

JOYCON_MANUFACTURER_ID = 1363
JOYCON_MANUFACTURER_PREFIX = bytes([0x01, 0x00, 0x03, 0x7E])
INPUT_REPORT_UUID = "ab7de9be-89fe-49ad-828f-118f09df7fd2"

BUTTON_MASKS = {
    0x000800: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    0x000400: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    0x000200: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    0x000100: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    0x000004: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    0x000002: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    0x004000: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    0x000040: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    0x00080000: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    0x000008: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
}

TRIGGER_MASKS = {
    "LT": 0x000080,
    "RT": 0x008000,
}

gamepad = vg.VX360Gamepad()

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
    except Exception as e:
        print("⚠️ Error decoding joystick:", e)
        traceback.print_exc()
        return 0, 0

def parse_buttons(data):
    try:
        if len(data) < 7:
            return
        state = int.from_bytes(data[3:6], byteorder='big')

        for mask, button in BUTTON_MASKS.items():
            if state & mask:
                gamepad.press_button(button)
            else:
                gamepad.release_button(button)

        gamepad.left_trigger(255 if state & TRIGGER_MASKS["LT"] else 0)
        gamepad.right_trigger(255 if state & TRIGGER_MASKS["RT"] else 0)
    except Exception as e:
        print("⚠️ Error parsing buttons:", e)
        traceback.print_exc()

async def notification_handler(sender, data):
    try:
        print(f"[RAW] {data.hex()}")
        parse_buttons(data)

        # Extract the candidate stick data bytes
        left_raw = data[10:13]
        right_raw = data[13:16]

        # DEBUG: print raw stick bytes hex so we can verify
        print(f"Left stick raw bytes 10:13 = {left_raw.hex()}")
        print(f"Right stick raw bytes 13:16 = {right_raw.hex()}")

        lx, ly = decode_joystick(left_raw)
        rx, ry = decode_joystick(right_raw)

        print(f"🎯 Left Stick : x={lx}, y={ly}")
        print(f"🎯 Right Stick: x={rx}, y={ry}")

        gamepad.left_joystick(x_value=lx, y_value=ly)
        # gamepad.right_joystick(x_value=rx, y_value=ry)  # Optional: enable if right stick needed

        gamepad.update()

    except Exception as e:
        print("⚠️ Error in notification handler:", e)
        traceback.print_exc()

async def scan_for_controller():
    print("🔍 Scanning for Pro Controller 2 (5s)...")
    found = None

    def cb(device, adv):
        nonlocal found
        m = adv.manufacturer_data.get(JOYCON_MANUFACTURER_ID)
        if m and m.startswith(JOYCON_MANUFACTURER_PREFIX):
            found = device
            print(f"✅ Found: {device.address}")

    scanner = BleakScanner(cb)
    await scanner.start()
    for _ in range(10):
        if found:
            break
        await asyncio.sleep(0.5)
    await scanner.stop()
    return found

async def main():
    try:
        device = await scan_for_controller()
        if not device:
            print("❌ No matching device found.")
            return

        client = BleakClient(device.address)
        await client.connect()
        print(f"🔗 Connected to {device.address}")

        await client.start_notify(INPUT_REPORT_UUID, notification_handler)
        print("🎮 Pro Controller 2 active and logging.")
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        print("❌ Unhandled exception in main():", e)
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("❌ Top-level exception:", e)
        traceback.print_exc()

    input("Press enter to close..")
