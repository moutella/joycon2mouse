# THIS FILE IS FOR: Solo JoyCon
import asyncio
from bleak import BleakScanner, BleakClient
import binascii
import struct
import collections
import vgamepad as vg

# Constants
JOYCON_MANUFACTURER_ID = 1363
JOYCON_MANUFACTURER_PREFIX = bytes([0x01, 0x00, 0x03, 0x7E])
INPUT_REPORT_UUID = "ab7de9be-89fe-49ad-828f-118f09df7fd2"

# Button masks for Right Joy-Con
RIGHT_BUTTON_A = 0x000800
RIGHT_BUTTON_B = 0x000400
RIGHT_BUTTON_X = 0x000200
RIGHT_BUTTON_Y = 0x000100
RIGHT_BUTTON_PLUS = 0x000004
RIGHT_BUTTON_R = 0x000002
RIGHT_BUTTON_ZR = 0x000001
RIGHT_BUTTON_STICK = 0x000008

# Button masks for Left Joy-Con
LEFT_BUTTON_UP = 0x000002
LEFT_BUTTON_DOWN = 0x000004
LEFT_BUTTON_LEFT = 0x000008
LEFT_BUTTON_RIGHT = 0x000001
LEFT_BUTTON_MINUS = 0x000100
LEFT_BUTTON_L = 0x000040
LEFT_BUTTON_ZL = 0x000001
LEFT_BUTTON_STICK = 0x000800

# Virtual Gamepad
gamepad = vg.VX360Gamepad()



class JoystickFilter:
    def __init__(self, deadzone=0.08, smoothing_factor=0.2):  # Reduced smoothing
        self.deadzone = deadzone
        self.smoothing_factor = smoothing_factor
        self.last_output = 0.0

    def process(self, raw_value):
        # Very light smoothing only
        filtered_value = (self.smoothing_factor * raw_value +
                        (1 - self.smoothing_factor) * self.last_output)
        self.last_output = filtered_value
        return filtered_value


async def scan_for_joycons():
    print("Scanning for Joy-Cons...")

    joycon_devices = []

    def detection_callback(device, advertisement_data):
        manufacturer_data = advertisement_data.manufacturer_data
        if JOYCON_MANUFACTURER_ID in manufacturer_data:
            data = manufacturer_data[JOYCON_MANUFACTURER_ID]
            if data.startswith(JOYCON_MANUFACTURER_PREFIX):
                if device not in joycon_devices:
                    print(f"Found Joy-Con: {device.address}")
                    joycon_devices.append(device)

    scanner = BleakScanner(detection_callback)
    await scanner.start()
    await asyncio.sleep(5)  # scan duration, adjust as needed
    await scanner.stop()

    return joycon_devices


def decode_joystick(data, is_left=True, is_sideways=False):
    if len(data) != 3:
        raise ValueError("Joystick data must be 3 bytes long")

    x = ((data[1] & 0x0F) << 8) | data[0]
    y = (data[2] << 4) | ((data[1] & 0xF0) >> 4)

    x_normalized = (x - 2048) / 2048.0
    y_normalized = (y - 2048) / 2048.0

    # Swap and/or invert based on sideways layout
    if is_sideways:
        if is_left:
            x_normalized, y_normalized = -y_normalized, x_normalized
        else:
            x_normalized, y_normalized = y_normalized, -x_normalized

    deadzone = 0.08
    if abs(x_normalized) < deadzone and abs(y_normalized) < deadzone:
        return 0, 0

    extra_range = 1.70
    x_normalized = max(-1.0, min(1.0, x_normalized * extra_range))
    y_normalized = max(-1.0, min(1.0, y_normalized * extra_range))

    x_scaled = int(x_normalized * 32767)
    y_scaled = int(y_normalized * 32767)

    return x_scaled, y_scaled

def parse_buttons(data, is_left, is_sideways=False):
    if len(data) < 7:
        return set()

    button_data = data[4:7] if is_left else data[3:6]
    button_state = (button_data[0] << 16) | (button_data[1] << 8) | button_data[2]

    pressed_buttons = set()

    if is_sideways:
        if is_left:
            # Sideways LEFT Joy-Con: D-Pad → ABXY (rotated)
            if button_state & LEFT_BUTTON_DOWN:
                pressed_buttons.add("A")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)

            if button_state & LEFT_BUTTON_LEFT:
                pressed_buttons.add("B")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)

            if button_state & LEFT_BUTTON_RIGHT:
                pressed_buttons.add("X")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X)

            if button_state & LEFT_BUTTON_UP:
                pressed_buttons.add("Y")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)

            if button_state & LEFT_BUTTON_L:
                pressed_buttons.add("L")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)

            if button_state & LEFT_BUTTON_STICK:
                pressed_buttons.add("STICK")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)

        else:
            # Sideways RIGHT Joy-Con: ABXY → rotated ABXY
            if button_state & RIGHT_BUTTON_X:
                pressed_buttons.add("A")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)

            if button_state & RIGHT_BUTTON_A:
                pressed_buttons.add("B")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)

            if button_state & RIGHT_BUTTON_Y:
                pressed_buttons.add("X")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X)

            if button_state & RIGHT_BUTTON_B:
                pressed_buttons.add("Y")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)

            if button_state & RIGHT_BUTTON_R:
                pressed_buttons.add("R")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)

            if button_state & RIGHT_BUTTON_STICK:
                pressed_buttons.add("STICK")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)

    else:
        if is_left:
            # Upright LEFT Joy-Con: D-Pad → ABXY
            if button_state & LEFT_BUTTON_RIGHT:
                pressed_buttons.add("B")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)

            if button_state & LEFT_BUTTON_DOWN:
                pressed_buttons.add("A")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)

            if button_state & LEFT_BUTTON_LEFT:
                pressed_buttons.add("Y")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)

            if button_state & LEFT_BUTTON_UP:
                pressed_buttons.add("X")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X)

            if button_state & LEFT_BUTTON_MINUS:
                pressed_buttons.add("MINUS")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)

            if button_state & LEFT_BUTTON_L:
                pressed_buttons.add("L")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)

            if button_state & LEFT_BUTTON_STICK:
                pressed_buttons.add("STICK")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)

        else:
            # Upright RIGHT Joy-Con: ABXY → ABXY
            if button_state & RIGHT_BUTTON_A:
                pressed_buttons.add("A")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)

            if button_state & RIGHT_BUTTON_B:
                pressed_buttons.add("B")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B)

            if button_state & RIGHT_BUTTON_X:
                pressed_buttons.add("X")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X)

            if button_state & RIGHT_BUTTON_Y:
                pressed_buttons.add("Y")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)

            if button_state & RIGHT_BUTTON_PLUS:
                pressed_buttons.add("PLUS")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_START)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_START)

            if button_state & RIGHT_BUTTON_R:
                pressed_buttons.add("R")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)

            if button_state & RIGHT_BUTTON_STICK:
                pressed_buttons.add("STICK")
                gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)
            else:
                gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)

    return pressed_buttons


async def notification_handler(sender, data, is_left, is_sideways):
    try:
        pressed_buttons = parse_buttons(data, is_left, is_sideways)
        if pressed_buttons:
            print(f"Pressed buttons: {pressed_buttons}")

        # Get joystick data
        joystick_data = data[10:13] if is_left else data[13:16]
        x, y = decode_joystick(joystick_data, is_left, is_sideways)

        # Send joystick input based on orientation
        if is_sideways:
            # Use left joystick for sideways mode too
            gamepad.left_joystick(x_value=x, y_value=y)
        else:
            gamepad.left_joystick(x_value=x, y_value=y)

        gamepad.update()

    except Exception as e:
        print(f"Error processing data: {e}")



async def connect_to_joycon(device):
    print(f"Connecting to Joy-Con at {device.address}...")
    client = BleakClient(device.address)
    await client.connect()
    print(f"✅ Connected to Joy-Con: {device.address}")
    return client

async def main():
    joycons = await scan_for_joycons()
    if not joycons:
        print("No Joy-Con devices found.")
        return

    first_device = joycons[0]
    print(f"Auto-connecting to first found Joy-Con: {first_device.address}")

    client = await connect_to_joycon(first_device)

    # Ask for Left/Right
    joycon_type = None
    while joycon_type not in ("Left", "Right"):
        side_input = input("Is this Joy-Con Left or Right? (Enter 'L' or 'R'): ").strip().upper()
        if side_input == "L":
            joycon_type = "Left"
        elif side_input == "R":
            joycon_type = "Right"
        else:
            print("Invalid input. Please type 'L' or 'R'.")

    # Ask if Joy-Con is upright or sideways
    sideways_mode = None
    while sideways_mode not in ("Upright", "Sideways"):
        orient = input("Are you using this Joy-Con Upright or Sideways? (Enter 'U' or 'S'): ").strip().upper()
        if orient == "U":
            sideways_mode = "Upright"
        elif orient == "S":
            sideways_mode = "Sideways"
        else:
            print("Invalid input. Please type 'U' or 'S'.")

    is_left = (joycon_type == "Left")
    is_sideways = (sideways_mode == "Sideways")

    def callback(sender, data):
        asyncio.create_task(notification_handler(sender, data, is_left, is_sideways))

    await client.start_notify(INPUT_REPORT_UUID, callback)

    print("🎮 Listening for notifications...")
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("❌ Exiting.")
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
