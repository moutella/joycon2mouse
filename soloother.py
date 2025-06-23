# THIS FILE IS FOR: Solo Joycon, anything that isn't windows
import asyncio
import time
import threading
from bleak import BleakScanner, BleakClient
from pynput.keyboard import Controller as KeyboardController, Key, Listener as KeyboardListener
from pynput.mouse import Controller as MouseController

print("🟢 Script started")

# BLE Constants
JOYCON_MANUFACTURER_ID = 1363
JOYCON_MANUFACTURER_PREFIX = bytes([0x01, 0x00, 0x03, 0x7E])
INPUT_REPORT_UUID = "ab7de9be-89fe-49ad-828f-118f09df7fd2"

# Button masks (Right Joy-Con)
RIGHT_BUTTON_A = 0x000800
RIGHT_BUTTON_B = 0x000400
RIGHT_BUTTON_X = 0x000200
RIGHT_BUTTON_Y = 0x000100
RIGHT_BUTTON_PLUS = 0x000004
RIGHT_BUTTON_R = 0x000002
RIGHT_BUTTON_ZR = 0x000001
RIGHT_BUTTON_STICK = 0x000008

# Button masks (Left Joy-Con)
LEFT_BUTTON_UP = 0x000002
LEFT_BUTTON_DOWN = 0x000004
LEFT_BUTTON_LEFT = 0x000008
LEFT_BUTTON_RIGHT = 0x000001
LEFT_BUTTON_MINUS = 0x000100
LEFT_BUTTON_L = 0x000040
LEFT_BUTTON_ZL = 0x000001
LEFT_BUTTON_STICK = 0x000800

# Input controllers
keyboard = KeyboardController()
mouse = MouseController()

# Key mapping
key_map = {
    "UP": Key.up, "DOWN": Key.down,
    "LEFT": Key.left, "RIGHT": Key.right,
    "A": 'z', "B": 'x', "X": 'a', "Y": 's',
    "PLUS": Key.enter, "MINUS": Key.esc,
    "L": 'q', "R": 'w'
}

pressed_state = set()
joystick_vector = [0.0, 0.0]
joystick_lock = threading.Lock()

# Toggle for mouse movement (starts disabled)
mouse_enabled = False
mouse_enabled_lock = threading.Lock()


def parse_buttons(data, is_left):
    if len(data) < 7:
        return set()
    button_data = data[4:7] if is_left else data[3:6]
    button_state = (button_data[0] << 16) | (button_data[1] << 8) | button_data[2]
    pressed = set()

    if is_left:
        if button_state & LEFT_BUTTON_UP: pressed.add("UP")
        if button_state & LEFT_BUTTON_DOWN: pressed.add("DOWN")
        if button_state & LEFT_BUTTON_LEFT: pressed.add("LEFT")
        if button_state & LEFT_BUTTON_RIGHT: pressed.add("RIGHT")
        if button_state & LEFT_BUTTON_MINUS: pressed.add("MINUS")
        if button_state & LEFT_BUTTON_L: pressed.add("L")
        if button_state & LEFT_BUTTON_STICK: pressed.add("STICK")
    else:
        if button_state & RIGHT_BUTTON_A: pressed.add("A")
        if button_state & RIGHT_BUTTON_B: pressed.add("B")
        if button_state & RIGHT_BUTTON_X: pressed.add("X")
        if button_state & RIGHT_BUTTON_Y: pressed.add("Y")
        if button_state & RIGHT_BUTTON_PLUS: pressed.add("PLUS")
        if button_state & RIGHT_BUTTON_R: pressed.add("R")
        if button_state & RIGHT_BUTTON_STICK: pressed.add("STICK")

    return pressed


def decode_joystick(data, is_left):
    if len(data) != 3:
        return 0.0, 0.0
    x = ((data[1] & 0x0F) << 8) | data[0]
    y = (data[2] << 4) | ((data[1] & 0xF0) >> 4)
    x_norm = (x - 2048) / 2048.0
    y_norm = (y - 2048) / 2048.0

    deadzone = 0.08
    if abs(x_norm) < deadzone: x_norm = 0
    if abs(y_norm) < deadzone: y_norm = 0

    # No magnitude clamp here — use raw values scaled directly

    return x_norm, y_norm


def update_keyboard_and_mouse(is_left, pressed_buttons, x, y):
    global pressed_state

    # Handle keyboard keys pressed/released
    for key in list(pressed_state):
        if key not in pressed_buttons and key in key_map:
            keyboard.release(key_map[key])
            pressed_state.remove(key)

    for key in pressed_buttons:
        if key not in pressed_state and key in key_map:
            keyboard.press(key_map[key])
            pressed_state.add(key)

    # Update joystick vector for mouse movement
    with joystick_lock:
        joystick_vector[0] = x
        joystick_vector[1] = y


def on_key_press(key):
    global mouse_enabled
    try:
        if key == Key.f6:
            with mouse_enabled_lock:
                mouse_enabled = not mouse_enabled
                status = "ENABLED" if mouse_enabled else "DISABLED"
                print(f"🔔 Mouse movement toggled {status}")
    except Exception as e:
        print(f"⚠️ Exception in key handler: {e}")


def joystick_mouse_loop():
    rate = 1 / 120.0  # 120Hz update

    screen_min_x, screen_max_x = 0, 1920
    screen_min_y, screen_max_y = 0, 1080
    center_x, center_y = 960, 540

    acc_dx, acc_dy = 0.0, 0.0
    last_active = time.time()

    # Initialize screen size and center on right half of screen
    try:
        from screeninfo import get_monitors
        primary_mon = get_monitors()[0]
        screen_min_x, screen_min_y = primary_mon.x, primary_mon.y
        screen_max_x = primary_mon.width + primary_mon.x
        screen_max_y = primary_mon.height + primary_mon.y
        center_x = screen_min_x + (screen_max_x - screen_min_x) * 3 // 4
        center_y = (screen_max_y + screen_min_y) // 2

        # Move mouse to right half center at start
        mouse.position = (center_x, center_y)
    except Exception as e:
        print("⚠️ Could not get screen info or set initial position:", e)

    while True:
        start_time = time.time()

        with joystick_lock:
            x, y = joystick_vector

        with mouse_enabled_lock:
            enabled = mouse_enabled

        if not enabled:
            time.sleep(rate)
            continue

        # If joystick near center, move mouse back to right half center smoothly
        center_threshold = 0.05
        return_speed = 0.5

        is_centered = (abs(x) < center_threshold and abs(y) < center_threshold)

        if is_centered:
            if time.time() - last_active > 0.1:
                current_x, current_y = mouse.position
                dx = center_x - current_x
                dy = center_y - current_y

                if abs(dx) < 1 and abs(dy) < 1:
                    mouse.position = (center_x, center_y)
                    acc_dx, acc_dy = 0.0, 0.0
                else:
                    move_x = dx * return_speed
                    move_y = dy * return_speed
                    mouse.move(int(move_x), int(move_y))
        else:
            last_active = time.time()

            # Move mouse proportional to raw joystick input, scaled by frame time and a large multiplier
            # To match joystick raw data speed, multiply by a big constant:
            speed_multiplier = 3000  # Tune this up or down to your liking

            move_x = x * speed_multiplier * rate
            move_y = -y * speed_multiplier * rate  # Y inverted for mouse coords

            current_x, current_y = mouse.position
            new_x = current_x + move_x
            new_y = current_y + move_y

            # Clamp mouse within screen bounds
            if new_x < screen_min_x:
                move_x = screen_min_x - current_x
            elif new_x > screen_max_x:
                move_x = screen_max_x - current_x

            if new_y < screen_min_y:
                move_y = screen_min_y - current_y
            elif new_y > screen_max_y:
                move_y = screen_max_y - current_y

            acc_dx += move_x
            acc_dy += move_y

            move_x_int = int(acc_dx)
            move_y_int = int(acc_dy)

            if move_x_int != 0 or move_y_int != 0:
                mouse.move(move_x_int, move_y_int)
                acc_dx -= move_x_int
                acc_dy -= move_y_int

        elapsed = time.time() - start_time
        if elapsed < rate:
            time.sleep(rate - elapsed)


async def notification_handler(sender, data, is_left):
    try:
        buttons = parse_buttons(data, is_left)
        joystick_data = data[10:13] if is_left else data[13:16]
        x, y = decode_joystick(joystick_data, is_left)
        update_keyboard_and_mouse(is_left, buttons, x, y)
    except Exception as e:
        print("❌ Exception in notification_handler:", e)


async def scan_for_joycons():
    print("🔍 Scanning for Joy-Cons...")
    joycon_devices = []

    def detection_callback(device, advertisement_data):
        manufacturer_data = advertisement_data.manufacturer_data
        if JOYCON_MANUFACTURER_ID in manufacturer_data:
            data = manufacturer_data[JOYCON_MANUFACTURER_ID]
            if data.startswith(JOYCON_MANUFACTURER_PREFIX):
                if device not in joycon_devices:
                    print(f"✅ Found Joy-Con: {device.address}")
                    joycon_devices.append(device)

    scanner = BleakScanner(detection_callback)
    await scanner.start()
    await asyncio.sleep(5)  # adjust scan time as needed
    await scanner.stop()

    if not joycon_devices:
        print("❌ No Joy-Con found.")
        return None

    # Prompt user for side
    while True:
        side = input("Is this the Left or Right Joy-Con? (L/R): ").strip().upper()
        if side in ("L", "R"):
            is_left = (side == "L")
            joycon_type = "Left" if is_left else "Right"
            print(f"Selected {joycon_type} Joy-Con.")
            return joycon_devices[0], is_left
        else:
            print("Invalid input. Please enter 'L' or 'R'.")


async def connect_to_joycon(device_info):
    device, is_left = device_info
    joycon_type = "Left" if is_left else "Right"
    async with BleakClient(device.address) as client:
        print(f"✅ Connected to {joycon_type} Joy-Con ({device.address})")
        await client.start_notify(INPUT_REPORT_UUID, lambda s, d: asyncio.create_task(notification_handler(s, d, is_left)))
        while True:
            await asyncio.sleep(1)


async def main():
    joycon = await scan_for_joycons()
    if joycon:
        await connect_to_joycon(joycon)
    else:
        print("🛑 Exiting. No Joy-Con found.")


if __name__ == "__main__":
    # Start mouse control thread
    threading.Thread(target=joystick_mouse_loop, daemon=True).start()

    # Start keyboard listener thread to toggle mouse movement with F6
    listener = KeyboardListener(on_press=on_key_press)
    listener.daemon = True
    listener.start()

    print("🔄 Running asyncio loop")
    asyncio.run(main())
