# This file is for: Pro Controller 2.
# Special thanks to Zarexel for sending over ProCon2 data and getting this to work!

# THIS FILE IS INTENDED FOR TESTING STUFF. DO NOT USE FOR RIGHT NOW.

import asyncio
from bleak import BleakScanner, BleakClient
import vgamepad as vg
import traceback

JOYCON_MANUFACTURER_ID = 1363
JOYCON_MANUFACTURER_PREFIX = bytes([0x01, 0x00, 0x03, 0x7E])
INPUT_REPORT_UUID = "ab7de9be-89fe-49ad-828f-118f09df7fd2"

BUTTON_MASKS = {
    # Original Joy-Con buttons (padded)
   0x000800000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    0x000400000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    0x000200000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    0x000100000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,

    # Joy-Con Shoulders
    0x004000000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    0x000000400000: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,

    # Joy-Con D-Pad
    0x000000020000: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    0x000000040000: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
    0x000000010000: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    0x000000080000: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,

    # Joy-Con misc
    0x000010000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,         # Home
    0x000001000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,          # Capture
    0x000002000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,          # Start
    0x000004000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,          # RIGHT STICK BUTTON
    0x000008000000: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,          # LEFT STICK BUTTON
}
TRIGGER_MASKS = {
    "LT": 0x000000800000,
    "RT": 0x008000000000,
}

gamepad = vg.VX360Gamepad()

IMU_COMMAND_0x02 = bytearray([
    0x0c, 0x91, 0x00, 0x02, 0x00, 0x04,
    0x00, 0x00, 0x27,
    0x00, 0x00, 0x00
])

SET_PLAYER_LED = bytearray([
    0x09, 0x91, 0x00, 0x07, 0x00, 0x08,
    0x00, 0x00,
    0x01,  # LED bitfield - adjust as needed
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
])

async def write_commands_to_all_writable(client):
    print("✉️ Writing IMU and LED commands to all writable characteristics...")
    for service in client.services:
        for char in service.characteristics:
            if "write" in char.properties or "write_without_response" in char.properties:
                try:
                    print(f"  Writing to characteristic {char.uuid} (properties: {char.properties})")
                    await client.write_gatt_char(char.uuid, IMU_COMMAND_0x02, response=True)
                    await asyncio.sleep(0.1)  # slight delay to avoid flooding
                    await client.write_gatt_char(char.uuid, SET_PLAYER_LED, response=True)
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"    ⚠️ Failed to write to {char.uuid}: {e}")

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

        button_region = data[3:9]
        state = int.from_bytes(button_region, byteorder='big')

        print(f"🔍 Button region bytes [3:9]: {button_region.hex()} (bitmask: 0x{state:012x})")

        for mask, button in BUTTON_MASKS.items():
            if state & mask:
                gamepad.press_button(button)
            else:
                gamepad.release_button(button)

        # Digital triggers as bitmask flags (full press = 255, released = 0)
        left_trigger_val = 255 if (state & TRIGGER_MASKS["LT"]) else 0
        right_trigger_val = 255 if (state & TRIGGER_MASKS["RT"]) else 0

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

        # Discover services and characteristics
        await client.get_services()

        # Write commands to every writable characteristic
        await write_commands_to_all_writable(client)

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
