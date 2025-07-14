from functools import partial
from utils import *
import uvicorn
import asyncio

import rumps
from bleak import BleakScanner, BleakClient
from joycon import JoyCon
# import vgamepad as vg
import time

from fastapi import FastAPI


used_addresses = set()

import gc

global cliente
cliente = None
class Player:
    def __init__(self, number, controller_type, side=None, task=None):
        self.number = number
        self.type = controller_type
        self.side = side
        self.clients = []
        # Explicit garbage collection to prevent reuse issues
        gc.collect()
        self.gamepad = JoyCon()  # Initialize JoyCon instance
    
    async def disconnect(self):
        for client in self.clients:
            if client.is_connected:
                await client.disconnect()
        self.clients.clear()
        # Explicit garbage collection to prevent reuse issues
        await self.task.cancel()
        gc.collect()

players : list[Player] = []


async def scan_device(prompt="controller"):
    print(f"\n🔍 Searching for your {prompt} (press sync)...")
    found_devices = []
    device_event = asyncio.Event()

    def callback(device, adv):
        if device.address in used_addresses:
            return
        data = adv.manufacturer_data.get(JOYCON_MANUFACTURER_ID)
        if data and data.startswith(JOYCON_MANUFACTURER_PREFIX):
            if not any(d.address == device.address for d in found_devices):
                found_devices.append(device)
                print(f"  Found {device.name or 'Unknown'} ({device.address})")
                device_event.set()

    scanner = BleakScanner(callback)
    await scanner.start()

    selected_device = None
    try:
        while True:
            await device_event.wait()
            device_event.clear()
            if found_devices:
                selected_device = found_devices[0]
                break
    finally:
        await scanner.stop()

    if selected_device:
        print(f"🎮 Selected {selected_device.name or 'Unknown'} ({selected_device.address})")
    else:
        print("❌ No device found.")

    return selected_device

async def write_command(client, command_id, subcommand_id, buffer):
    # Pad buffer to 8 bytes minimum because some buffer lengths seems to crash
    buffer = buffer.ljust(8, b'\0')
    await client.write_gatt_char(WRITE_COMMAND_UUID, command_id.to_bytes() + b"\x91\x01" + subcommand_id.to_bytes() + b"\x00" + len(buffer).to_bytes() + b"\x00\x00" + buffer)

async def play_vibration_preset(client, preset_id):
    await write_command(client, COMMAND_VIBRATION, SUBCOMMAND_PLAY_VIBRATION_PRESET, preset_id.to_bytes())


async def disable_imu(client):
    ENABLE_IMU_1 = bytes([0x0c, 0x91, 0x01, 0x03, 0x00, 0x04, 0x00, 0x00, 0x2f, 0x00, 0x00, 0x00])
    ENABLE_IMU_2 = bytes([0x0c, 0x91, 0x01, 0x06, 0x00, 0x00, 0x00, 0x00, 0x2f, 0x00, 0x00, 0x00])
    await client.write_gatt_char(WRITE_COMMAND_UUID, ENABLE_IMU_1)

    await asyncio.sleep(0.5)
    await client.write_gatt_char(WRITE_COMMAND_UUID, ENABLE_IMU_2)

async def enable_imu(client):
    ENABLE_IMU_1 = bytes([0x0c, 0x91, 0x01, 0x02, 0x00, 0x04, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00])
    ENABLE_IMU_2 = bytes([0x0c, 0x91, 0x01, 0x04, 0x00, 0x04, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00])
    await client.write_gatt_char(WRITE_COMMAND_UUID, ENABLE_IMU_1)

    await asyncio.sleep(0.5)
    await client.write_gatt_char(WRITE_COMMAND_UUID, ENABLE_IMU_2)


async def enable_feature(client, feature_id):
    features = {
        "Unknown01":    0x01,
        "Unknown02":    0x02,
        "Motion":       0x04,
        "Unknown08":    0x08,
        "Mouse":        0x10,
        "Current":      0x20,
        "Unknown40":    0x40,
        "Magnetometer": 0x80,
    }
    ENABLE_IMU_1 = bytes([0x0c, 0x91, 0x01, 0x02, 0x00, features[feature_id], 0x00, 0x00, 0x2f, 0x00, 0x00, 0x00])
    ENABLE_IMU_2 = bytes([0x0c, 0x91, 0x01, 0x04, 0x00, features[feature_id], 0x00, 0x00, 0x2f, 0x00, 0x00, 0x00])
    await client.write_gatt_char(WRITE_COMMAND_UUID, ENABLE_IMU_1)

    await asyncio.sleep(0.5)
    await client.write_gatt_char(WRITE_COMMAND_UUID, ENABLE_IMU_2)

async def enable_mouse(client):
    # 0x0c = Comando de feature
    # 0x91 = "Enviado do console"
    # 0x01 = "BLE?" verificar.
    # 0x02 = "Inicializar feature"
    # 0x04 = "Habilitar feature."

    # features:
    # 0x04 = "Motion"
    # 0x08 = mouse?
    ENABLE_MOUSE_1 = bytes([0x0c, 0x91, 0x01, 0x02, 0x00, 0x08, 0x00, 0x00, 0x2f, 0x00, 0x00, 0x00])
    ENABLE_MOUSE_2 = bytes([0x0c, 0x91, 0x01, 0x04, 0x00, 0x08, 0x00, 0x00, 0x2f, 0x00, 0x00, 0x00])

    await client.write_gatt_char(WRITE_COMMAND_UUID, ENABLE_MOUSE_1)
    await asyncio.sleep(0.5)
    await client.write_gatt_char(WRITE_COMMAND_UUID, ENABLE_MOUSE_2)

async def set_leds(client, player_number):
    #Repoduce switch led patterns for up to 8 players https://en-americas-support.nintendo.com/app/answers/detail/a_id/22424
    led_pattern_by_played_id = {
        1: b'\x01',
        2: b'\x03',
        3: b'\x07',
        4: b'\x0F',
        5: b'\x09',
        6: b'\x05',
        7: b'\x0D',
        8: b'\x06',
    }

    if player_number > 8:
        player_number = 8

    print(led_pattern_by_played_id[player_number])

    await write_command(client, COMMAND_LEDS, SUBCOMMAND_SET_PLAYER_LEDS, led_pattern_by_played_id[player_number])

async def connect_and_setup(device, player, handler_func, *handler_args):
    client = BleakClient(device.address)
    await client.connect()
    client._device = device
    await asyncio.sleep(0.5)  # Allow connection to stabilize
    await set_leds(client, player.number)
    await asyncio.sleep(0.5)  # Allow vibration to play
    await play_vibration_preset(client, 0x04)  # Play default vibration preset
    await asyncio.sleep(0.5)  # Allow vib
    await enable_imu(client)
    # await enable_mouse(client)
    # await play_vibration_preset(client, 0x01)  # Play default vibration preset
    # await asyncio.sleep(0.5)  # Allow vibration to play
    # await play_vibration_preset(client, 0x02)  # Play default vibration preset
    # await asyncio.sleep(0.5)  # Allow vibration to play
    # await play_vibration_preset(client, 0x03)  # Play default vibration preset
    global cliente
    cliente = client
    print(cliente)
    print("cheguei aqui")
    await handler_func(client, player, *handler_args)
    player.clients.append(client)
    print(f"✅ Connected to {device.address}")
    return client

async def maintain_connection_loop(client, device, player, handler_func, *handler_args):
    while True:
        try:
            if not client.is_connected:
                await client.connect()
                await handler_func(client, player, *handler_args)
                print(f"🔄 Reconnected to {device.address}")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"⚠️ Connection lost or error: {e}")
            if client.is_connected:
                await client.disconnect()
            await asyncio.sleep(5)

async def handle_single_joycon(client, player: Player, upright: bool):
    from solo_logic import handle_single_notification
    async def cb(sender, data):
        await handle_single_notification(sender, data, player.side == "LEFT", player.gamepad, upright)
    await client.start_notify(INPUT_REPORT_UUID, cb)

async def setup_player(number):
    print(f"\n🎮 Setting up Player {number}")
    while True:
        choice = "1" #input("Controller Type? (1=Single Joy-Con, 2=Dual Joy-Con, 3=Pro Controller, 4=NSO GameCube): ").strip()
        if choice == "1":
            # side = input("Left or Right Joy-Con? (L/R): ").strip().upper()
            # side = "LEFT" if side == "L" else "RIGHT"
            side = "RIGHT"
            # orientation = input("Orientation? (U=Upright, S=Sideways): ").strip().upper()
            upright = orientation = "U"

            device = await scan_device(f"Player {number} {side} Joy-Con")
            if not device:
                return None
            used_addresses.add(device.address)

            player = Player(number, "SINGLE_JOYCON", side)
            client = await connect_and_setup(device, player, handle_single_joycon, upright)
            task = asyncio.create_task(maintain_connection_loop(client, device, player, handle_single_joycon, upright))
            player.task = task
            return player

        else:
            print("❌ Invalid choice.")

async def add_player(number):
    global players
    player = await setup_player(number)
    if not player:
        print("❌ Setup failed. Exiting.")
        return False
    players.append(player)
    return number

async def remove_player(player):
    print("hmmm")
    player -= 1
    global players
    await players[player].disconnect()
    print("testre")
    # await players[player].clients[0].disconnect()
    # del players[player]
    # print(f"❌ Player {player.number} removed.")

async def emit_sound():
    global players
    for player in players:
        for client in player.clients:
            await play_vibration_preset(client, 0x04) 

async def main():
    try:
        global players
        count = 0 #int(input("How many players? ").strip())
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

            # NEW: Explicitly remove virtual gamepad
            if hasattr(p, "gamepad") and p.gamepad:
                try:
                    p.gamepad.reset()
                    del p.gamepad
                except Exception as e:
                    print(f"Error removing gamepad for player {p.number}: {e}")




async def pillow():
    import rumps

    from threading import Thread

    def start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        loop.run_forever()

    class MyApp(rumps.App):
        def __init__(self):
            super().__init__("MyApp", icon="assets/joycon2mouse.png")  # icon must be PNG
            self.menu = ["JoyCon2Mouse"]

        def notification(self, title, subtitle, message):
            rumps.notification(title, subtitle, message)
        
        @rumps.clicked("Sync controller")
        def sync(self, _):
            # rumps.alert("Hello from the menu bar!")
            loop = asyncio.new_event_loop()
            t = Thread(target=start_background_loop, args=(loop,), daemon=True)
            t.start()
            future = asyncio.run_coroutine_threadsafe(add_player(1), loop)
            future.add_done_callback(lambda f: self.handle_pairing_result(f.result()))
            # resultado = resultado.result()  # Wait for the coroutine to finish
            # if resultado:
            #     rumps.notification("JoyCon Connected", "", "You may use your mouse now.")
            
        def handle_pairing_result(self, pairing_result):
            if pairing_result:
                rumps.notification("JoyCon Connected", "", "You may use your mouse now.")
                #TODO: Add disconnect option
                # self.menu.add(rumps.MenuItem(f"Disconnect controller {pairing_result}", callback=partial(self.disconnect_controller, pairing_result)))
            else:
                rumps.notification("JoyCon Connection Failed", "", "Please try again.")

        def disconnect_controller(self, number, sender):
            loop = asyncio.new_event_loop()
            t = Thread(target=start_background_loop, args=(loop,), daemon=True)
            t.start()
            future = asyncio.run_coroutine_threadsafe(remove_player(number), loop)
            # future.add_done_callback(lambda f: handle_pairing_result(self, f.result()))

        @rumps.clicked("Say hi")
        def sayhi(self, _):
            loop = asyncio.new_event_loop()
            t = Thread(target=start_background_loop, args=(loop,), daemon=True)
            t.start()
            future = asyncio.run_coroutine_threadsafe(emit_sound(), loop)
            # future.add_done_callback(lambda f: handle_pairing_result(self, f.result()))

    if __name__ == "__main__":
        MyApp().run()

async def mainapi():
    await asyncio.gather(pillow())  # Run both main and FastAPI concurrently
    #, run_fastapi()

if __name__ == "__main__":
    asyncio.run(mainapi())
    print("hmm")
    



app = FastAPI()
@app.get("/sons")
async def read_root(som_id: str = "1"):
    global players
    if cliente is None:
        return {"players": players}  
    # play_vibration_preset(cliente, 0x04)
    # print()
    sons = {
        "1": 0x01,
        "2": 0x02,
        "3": 0x03,
        "4": 0x04,
        "5": 0x05,
        "6": 0x06,
        "7": 0x07,
        "8": 0x08,
    }
    await play_vibration_preset(players[0].clients[0], sons[som_id])
    return {"my_var": len(players)}


@app.get("/imu")
async def imu(som_id: str = "1"):
    global players
    if cliente is None:
        return {"players": players}  
    await enable_imu(players[0].clients[0])
    return {"my_var": len(players)}


@app.get("/imu_disable")
async def desativar_imu(som_id: str = "1"):
    global players
    if cliente is None:
        return {"players": players}  
    await disable_imu(players[0].clients[0])
    return {"my_var": len(players)}


@app.get("/mouse")
async def mouse(som_id: str = "1"):
    global players
    if cliente is None:
        return {"players": players}  
    await enable_mouse(players[0].clients[0])
    return {"my_var": len(players)}



@app.get("/feature")
async def mouse(feature: str = "Motion"):
    global players
    if cliente is None:
        return {"players": players}  
    await enable_feature(players[0].clients[0], feature)
    return {"my_var": len(players)}

async def run_fastapi():
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
