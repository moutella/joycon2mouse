import asyncio
from bleak import BleakScanner, BleakClient
import vgamepad as vg
import traceback

# Constants
JOYCON_MANUFACTURER_ID = 1363
JOYCON_MANUFACTURER_PREFIX = bytes([0x01, 0x00, 0x03, 0x7E])
INPUT_REPORT_UUID = "ab7de9be-89fe-49ad-828f-118f09df7fd2"

# Player config
class Player:
    def __init__(self, number, controller_type, side=None):
        self.number = number
        self.type = controller_type  # SINGLE_JOYCON, DUAL_JOYCON, PRO_CONTROLLER
        self.side = side             # LEFT or RIGHT (for single Joy-Con)
        self.clients = []           # One or two BleakClient objects
        self.gamepad = vg.VX360Gamepad()

# ========== COMMON FUNCTIONS ==========

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
    except:
        return 0, 0

async def scan_device(prompt="controller"):
    print(f"🔍 Now press a button on your {prompt}...")
    found = None

    def callback(device, adv):
        nonlocal found
        data = adv.manufacturer_data.get(JOYCON_MANUFACTURER_ID)
        if data and data.startswith(JOYCON_MANUFACTURER_PREFIX):
            if not found:
                found = device
                print(f"✅ Found {prompt} at {device.address}")

    scanner = BleakScanner(callback)
    await scanner.start()
    for _ in range(20):
        if found:
            break
        await asyncio.sleep(0.5)
    await scanner.stop()
    return found

async def connect(device):
    client = BleakClient(device.address)
    await client.connect()
    print(f"🔗 Connected to {device.address}")
    return client

# ========== NOTIFICATION HANDLERS ==========

# Each of these will get a tailored handler
async def handle_single_joycon(client, player: Player, upright: bool):
    from solo_logic import handle_single_notification
    async def cb(sender, data):
        await handle_single_notification(sender, data, player.side == "LEFT", player.gamepad, upright)
    await client.start_notify(INPUT_REPORT_UUID, cb)

async def handle_dual_joycon(left_client, right_client, player: Player):
    from duo_logic import handle_duo_notification
    async def cb_left(sender, data):
        await handle_duo_notification(sender, data, "LEFT", player.gamepad)
    async def cb_right(sender, data):
        await handle_duo_notification(sender, data, "RIGHT", player.gamepad)
    await asyncio.gather(
        left_client.start_notify(INPUT_REPORT_UUID, cb_left),
        right_client.start_notify(INPUT_REPORT_UUID, cb_right)
    )

async def handle_pro_controller(client, player: Player):
    from pro_logic import handle_pro_notification
    async def cb(sender, data):
        await handle_pro_notification(sender, data, player.gamepad)
    await client.start_notify(INPUT_REPORT_UUID, cb)

# ========== MAIN LOGIC ==========

async def setup_player(number):
    print(f"\n🎮 Setting up Player {number}")
    while True:
        choice = input("Controller Type? (1=Single Joy-Con, 2=Dual Joy-Con, 3=Pro Controller): ").strip()
        if choice == "1":
            side = input("Left or Right Joy-Con? (L/R): ").strip().upper()
            side = "LEFT" if side == "L" else "RIGHT"
            orientation = input("Orientation? (U=Upright, S=Sideways): ").strip().upper()
            upright = orientation == "U"

            device = await scan_device(f"Player {number} {side} Joy-Con")
            if not device:
                print("❌ Could not find Joy-Con.")
                return None
            client = await connect(device)

            player = Player(number, "SINGLE_JOYCON", side)
            player.clients = [client]
            await handle_single_joycon(client, player, upright)
            return player

        elif choice == "2":
            right = await scan_device(f"Player {number} RIGHT Joy-Con")
            if not right:
                return None
            right_client = await connect(right)

            left = await scan_device(f"Player {number} LEFT Joy-Con")
            if not left:
                await right_client.disconnect()
                return None
            left_client = await connect(left)

            player = Player(number, "DUAL_JOYCON")
            player.clients = [left_client, right_client]
            await handle_dual_joycon(left_client, right_client, player)
            return player

        elif choice == "3":
            device = await scan_device(f"Player {number} Pro Controller")
            if not device:
                return None
            client = await connect(device)
            player = Player(number, "PRO_CONTROLLER")
            player.clients = [client]
            await handle_pro_controller(client, player)
            return player

        else:
            print("Invalid selection. Try again.")

async def main():
    try:
        players = []
        count = int(input("How many players? ").strip())

        for i in range(1, count + 1):
            player = await setup_player(i)
            if not player:
                print("❌ Setup failed. Exiting.")
                return
            players.append(player)

        print("🎮 All players connected. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nExiting...")

    finally:
        for p in players:
            for c in p.clients:
                if c.is_connected:
                    await c.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
