# THIS FILE IS FOR: Solo JoyCon, WINDOWS ONLY
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


def decode_joystick(data, is_left=True):
    if len(data) != 3:
        raise ValueError("Joystick data must be 3 bytes long")

    # Check for left Joy-Con specific joystick data pattern (10:13)
    if is_left and data[0] == 0x10 and data[1] == 0x13:
        # Swap the bytes to get correct joystick data
        data = bytes([data[1], data[0], data[2]])

    x = ((data[1] & 0x0F) << 8) | data[0]
    y = (data[2] << 4) | ((data[1] & 0xF0) >> 4)

    # Convert to normalized values (-1.0 to 1.0)
    x_normalized = (x - 2048) / 2048.0
    y_normalized = (y - 2048) / 2048.0

    # Apply minimal deadzone (raw feel)
    deadzone = 0.08  # Small deadzone for responsiveness
    if abs(x_normalized) < deadzone and abs(y_normalized) < deadzone:
        return 0, 0

    # Add extra range by applying a small multiplier (1.1 = 10% extra)
    extra_range = 1.70
    x_normalized = max(-1.0, min(1.0, x_normalized * extra_range))
    y_normalized = max(-1.0, min(1.0, y_normalized * extra_range))

    # Scale directly to gamepad range with no artificial limits
    x_scaled = int(x_normalized * 32767)
    y_scaled = int(y_normalized * 32767)  # Invert Y axis

    return x_scaled, y_scaled

def parse_buttons(data, is_left):
    """Parse button data from bytes 3-6 (right) or 4-7 (left)"""
    if len(data) < 7:
        return set()

    if is_left:
        # Left Joy-Con: bytes 4-7
        button_data = data[4:7]
    else:
        # Right Joy-Con: bytes 3-6
        button_data = data[3:6]

    # Combine the 3 bytes into a single 24-bit value
    button_state = (button_data[0] << 16) | (button_data[1] << 8) | button_data[2]

    pressed_buttons = set()

    if is_left:
        # Check Left Joy-Con buttons
        if button_state & LEFT_BUTTON_UP:
            pressed_buttons.add("UP")
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
        else:
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)

        if button_state & LEFT_BUTTON_DOWN:
            pressed_buttons.add("DOWN")
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
        else:
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)

        if button_state & LEFT_BUTTON_LEFT:
            pressed_buttons.add("LEFT")
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
        else:
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)

        if button_state & LEFT_BUTTON_RIGHT:
            pressed_buttons.add("RIGHT")
            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
        else:
            gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)

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
        # Check Right Joy-Con buttons
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


async def notification_handler(sender, data, is_left):
    try:
        # Parse buttons first
        pressed_buttons = parse_buttons(data, is_left)
        if pressed_buttons:
            print(f"Pressed buttons: {pressed_buttons}")

        # Get joystick data
        if is_left:
            joystick_data = data[10:13]
        else:
            joystick_data = data[13:16]

        x, y = decode_joystick(joystick_data, is_left)

        # Send completely raw values to gamepad
        gamepad.left_joystick(x_value=x, y_value=y)
        gamepad.update()

        # Debug output showing raw values

    except Exception as e:
        print(f"Error processing data: {e}")



async def connect_to_joycon(device_info):
    device, joycon_type = device_info
    is_left = joycon_type == "Left"

    async with BleakClient(device.address) as client:
        print(f"Connected to {joycon_type} Joy-Con at {device.address}")

        def callback(sender, data):
            asyncio.create_task(
                notification_handler(sender, data, is_left)
            )

        await client.start_notify(INPUT_REPORT_UUID, callback)

        print("Listening for notifications...")
        while True:
            await asyncio.sleep(1)



async def main():
    joycons = await scan_for_joycons()
    if not joycons:
        print("No Joy-Con devices found.")
        return

    first_device = joycons[0]
    print(f"Auto-connecting to first found Joy-Con: {first_device.address}")

    joycon_type = None
    while joycon_type not in ("Left", "Right"):
        side_input = input("Is this Joy-Con Left or Right? (Enter 'L' or 'R'): ").strip().upper()
        if side_input == "L":
            joycon_type = "Left"
        elif side_input == "R":
            joycon_type = "Right"
        else:
            print("Invalid input. Please type 'L' or 'R'.")

    device_info = (first_device, joycon_type)
    await connect_to_joycon(device_info)

if __name__ == "__main__":
    asyncio.run(main())
