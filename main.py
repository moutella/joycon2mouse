import asyncio
from bleak import BleakScanner, BleakClient
import vgamepad as vg

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
        self.clients = []            # List of BleakClient objects
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
    print(f"🔍 Now hold the sync button on your {prompt}...")
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

async def handle_dual_joycon(client, player: Player, side: str):
    from duo_logic import handle_duo_notification
    async def cb(sender, data):
        await handle_duo_notification(sender, data, side, player.gamepad)
    await client.start_notify(INPUT_REPORT_UUID, cb)

async def handle_pro_controller(client, player: Player):
    from pro_logic import handle_pro_notification
    async def cb(sender, data):
        await handle_pro_notification(sender, data, player.gamepad)
    await client.start_notify(INPUT_REPORT_UUID, cb)

async def handle_gc_controller(client, player: Player):
    from gc_logic import handle_gc_notification
    async def cb(sender, data):
        await handle_gc_notification(sender, data, player.gamepad)
    await client.start_notify(INPUT_REPORT_UUID, cb)

# ========== CONNECTION MAINTAINER ==========

async def maintain_connection(device, player, handler_func, *handler_args):
    client = None
    while True:
        try:
            if client is None or not client.is_connected:
                if client:
                    await client.disconnect()
                print(f"🔗 Connecting to {device.address}...")
                client = BleakClient(device.address)
                await client.connect()
                print(f"✅ Connected to {device.address}")

                # Track client in player.clients list (avoid duplicates)
                if client not in player.clients:
                    player.clients.append(client)

                # Start notifications with handler callback
                await handler_func(client, player, *handler_args)

            # Keep connection alive by sleeping, can add heartbeat here if needed
            await asyncio.sleep(1)

            if not client.is_connected:
                raise Exception("Connection lost")

        except Exception as e:
            print(f"⚠️ Connection lost or error: {e}")
            print("⏳ Waiting for controller to reconnect... (hold down sync button)")

            # Disconnect cleanly if still connected
            if client and client.is_connected:
                await client.disconnect()
            client = None

            # Remove disconnected client from player.clients
            player.clients = [c for c in player.clients if c.is_connected]

            # Wait before retrying connection or rescanning
            await asyncio.sleep(5)

# ========== MAIN LOGIC ==========

async def setup_player(number):
    print(f"\n🎮 Setting up Player {number}")
    while True:
        choice = input("Controller Type? (1=Single Joy-Con, 2=Dual Joy-Con, 3=Pro Controller, 4=NSO GameCube): ").strip()
        if choice == "1":
            side = input("Left or Right Joy-Con? (L/R): ").strip().upper()
            side = "LEFT" if side == "L" else "RIGHT"
            orientation = input("Orientation? (U=Upright, S=Sideways): ").strip().upper()
            upright = orientation == "U"

            device = await scan_device(f"Player {number} {side} Joy-Con")
            if not device:
                print("❌ Could not find Joy-Con.")
                return None

            player = Player(number, "SINGLE_JOYCON", side)
            player.clients = []

            # Launch maintain_connection in background
            asyncio.create_task(maintain_connection(device, player, handle_single_joycon, upright))
            return player

        elif choice == "2":
            right_device = await scan_device(f"Player {number} RIGHT Joy-Con")
            if not right_device:
                print("❌ Could not find RIGHT Joy-Con.")
                return None
            left_device = await scan_device(f"Player {number} LEFT Joy-Con")
            if not left_device:
                print("❌ Could not find LEFT Joy-Con.")
                return None

            player = Player(number, "DUAL_JOYCON")
            player.clients = []

            # Launch maintain_connection tasks for both sides
            asyncio.create_task(maintain_connection(right_device, player, handle_dual_joycon, "RIGHT"))
            asyncio.create_task(maintain_connection(left_device, player, handle_dual_joycon, "LEFT"))
            return player

        elif choice == "3":
            device = await scan_device(f"Player {number} Pro Controller")
            if not device:
                print("❌ Could not find Pro Controller.")
                return None
            player = Player(number, "PRO_CONTROLLER")
            player.clients = []
            asyncio.create_task(maintain_connection(device, player, handle_pro_controller))
            return player

        elif choice == "4":
            device = await scan_device(f"Player {number} GameCube Controller")
            if not device:
                print("❌ Could not find GameCube Controller.")
                return None
            player = Player(number, "GC_CONTROLLER")
            player.clients = []
            asyncio.create_task(maintain_connection(device, player, handle_gc_controller))
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

        print("🎮 All players connected (or trying to reconnect). Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nExiting...")

    finally:
        # Clean up all clients
        for p in players:
            for c in p.clients:
                if c.is_connected:
                    await c.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
