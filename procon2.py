# This file is for: Pro Controller 2.
# This file is a WIP as I don't have a ProCon2 myself and have to ask people for the data to update the code. Some buttons may not work.

import asyncio
from bleak import BleakScanner, BleakClient
import vgamepad as vg
import traceback

JOYCON_MANUFACTURER_ID = 1363
JOYCON_MANUFACTURER_PREFIX = bytes([0x01, 0x00, 0x03, 0x7E])
INPUT_REPORT_UUID = "ab7de9be-89fe-49ad-828f-118f09df7fd2"

BUTTON_MASKS = {
    # Original Joy-Con buttons (unpadded)
    0x000800: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    0x000400: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    0x000200: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    0x000100: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    0x000004: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,  # PLUS
    0x000002: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,   # MINUS

    # Shoulders
    0x004000: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    0x000040: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,

    # Stick clicks
    # 0x080000: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    # 0x000008: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB, Conflict, commenting them out for now
    
    0x020000: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    0x040000: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
    0x010000: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    0x080000: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,

    0x1000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,         # Home
    0x2000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,          # Capture
    0x0100000: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,          # Minus remap
    0x4000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,         # C button remap

    # Optional GL / GR
    0x020000: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,  # GL (overlaps UP)
    0x010000: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER, # GR (overlaps DOWN)
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
        if len(data) < 17:
            return

        # Read 6-byte button region starting at offset 6
        button_region = data[3:12]
        state = int.from_bytes(button_region, byteorder='big')

        print(f"🔍 Button region bytes [6:12]: {button_region.hex()} (bitmask: 0x{state:012x})")

        for mask, button in BUTTON_MASKS.items():
            if button in ("LT_ANALOG", "RT_ANALOG"):
                continue
            if state & mask:
                gamepad.press_button(button)
            else:
                gamepad.release_button(button)

        # Analog triggers (assumed locations)
        left_trigger_val = data[12]
        right_trigger_val = data[16]

        print(f"🎚 Triggers - LT: {left_trigger_val}, RT: {right_trigger_val}")

        gamepad.left_trigger(left_trigger_val)
        gamepad.right_trigger(right_trigger_val)

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
        gamepad.right_joystick(x_value=rx, y_value=ry)

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
            await asyncio.sleep(0.005)

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
