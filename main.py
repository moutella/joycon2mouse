import asyncio
import queue
from threading import Thread
import tkinter as tk
import sys
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageTk
from player import Player
from user_preferences import settings, save_settings, load_settings
from utils import *
from bleak import BleakScanner, BleakClient


used_addresses = set()
command_queue = queue.Queue()

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


async def enable_mouse(client):
    ENABLE_IMU_1 = bytes([0x0c, 0x91, 0x01, 0x02, 0x00, 0x04, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00])
    ENABLE_IMU_2 = bytes([0x0c, 0x91, 0x01, 0x04, 0x00, 0x04, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00])
    await client.write_gatt_char(WRITE_COMMAND_UUID, ENABLE_IMU_1)

    await asyncio.sleep(0.5)
    await client.write_gatt_char(WRITE_COMMAND_UUID, ENABLE_IMU_2)


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

async def connect_and_setup(device, player: Player, handler_func, *handler_args):
    client = BleakClient(device.address)
    await client.connect()
    client._device = device
    await asyncio.sleep(0.5)  # Allow connection to stabilize
    await set_leds(client, player.number)
    await asyncio.sleep(0.5)  # Allow vibration to play
    await play_vibration_preset(client, 0x04)  # Play default vibration preset
    await asyncio.sleep(0.5)  # Allow vib
    await enable_mouse(client)
    if device.address not in settings["devices"]:
        command_queue.put({"command": "new_joy_window", "data": device.address, "player": player})
    else:
        print("hmmmmm???")
        print(device.address)
        print(settings["devices"][device.address]["type"])
        player.attach_joycon(settings["devices"][device.address]["type"])
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
        # side = input("Left or Right Joy-Con? (L/R): ").strip().upper()
        # side = "LEFT" if side == "L" else "RIGHT"
        # side = "RIGHT"
        # orientation = input("Orientation? (U=Upright, S=Sideways): ").strip().upper()
        upright = orientation = "U"

        device = await scan_device(f"Player {number} Joy-Con")
        if not device:
            return None
        used_addresses.add(device.address)

        player = Player(number, "SINGLE_JOYCON")
        client = await connect_and_setup(device, player, handle_single_joycon, upright)
        task = asyncio.create_task(maintain_connection_loop(client, device, player, handle_single_joycon, upright))
        player.task = task
        return player


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




# Função chamada quando clicar em "Quit"
def quit_action(icon, item):
    icon.stop()

def start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()

def tray_connect_new_controller():
    loop = asyncio.new_event_loop()
    t = Thread(target=start_background_loop, args=(loop,), daemon=True)
    t.start()
    future = asyncio.run_coroutine_threadsafe(add_player(1), loop)
    # future.add_done_callback(lambda f: self.handle_pairing_result(f.result()))

def tray_emit_sound():
    loop = asyncio.new_event_loop()
    t = Thread(target=start_background_loop, args=(loop,), daemon=True)
    t.start()
    asyncio.run_coroutine_threadsafe(emit_sound(), loop)

def on_quit(icon, item):
    import os
    os._exit(0)

# Cria o ícone
def create_icon(tk_main_process):
    # Icon
    settings = load_settings()
    image = Image.open(resource_path("assets/joycon2mouse.png"))

    # Main features
    sync_new_controller = MenuItem('Sync new Controller', tray_connect_new_controller)

    # Debug Menu
    debug_emit_sound = MenuItem('Say hi', tray_emit_sound)
    debug_tkinter = MenuItem("Joy Con View", set_joycon_type_interface)
    debug_menu = MenuItem('DEBUG', (Menu(
                    debug_emit_sound, debug_emit_sound, debug_tkinter))) 


    # Final Menu
    menu = Menu(sync_new_controller, 
                debug_menu, 
                MenuItem('Exit', on_quit))
    if settings["start_with_sync"]:
        tray_connect_new_controller()
    # set_joycon_type_interface("lala")
    return Icon("joycon2mouse", image, menu=menu)


tk_main_process = tk.Tk()
# tk_main_process.wm_attributes("-toolwindow", True)
tk_main_process.title("Welcome to JoyCon2Mouse")
tk_main_process.protocol("WM_DELETE_WINDOW", tk_main_process.withdraw)
tk_processes = [tk_main_process]
# tk_main_process.deiconify()
if settings["ignore_opening_window"]:
    tk_main_process.withdraw()


def set_joycon_type_interface(controller_id, player: Player):
    def on_select(option):
        if controller_id not in settings:
            settings["devices"][controller_id] = {
                "type": option
            }
            player.attach_joycon(option)
        else:
            settings["devices"][controller_id]["type"] = option

        save_settings(settings)
        tk_processes.remove(new_window)
        new_window.destroy()

    new_window = tk.Tk()
    tk_processes.append(new_window)
    new_window.title("New Joy-Con")
    screen_width = new_window.winfo_screenwidth()
    screen_height = new_window.winfo_screenheight()
    width = 640
    height = 300
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2) # width x height
    new_window.geometry(f'{width}x{height}+{x}+{y}')
    
    # Create images AFTER creating the window
    photo1 = tk.PhotoImage(master=new_window, file=resource_path("assets/left.png"))
    photo2 = tk.PhotoImage(master=new_window, file=resource_path("assets/right.png"))
    photo1 = photo1.subsample(4)
    photo2 = photo2.subsample(4)

    # Keep references
    new_window.photo1 = photo1
    # new_window.photo2 = photo2

    frame = tk.Frame(new_window)

    frame.pack(expand=True)
    # Create buttons
    btn1 = tk.Button(frame, image=photo1, command=lambda: on_select("left"))
    btn1.image = photo1
    btn2 = tk.Button(frame, image=photo2, command=lambda: on_select("right"))
    btn2.image = photo2
    
    tk.Label(new_window, text="Choose JoyCon type").pack(pady=20)
    
    btn1.pack(side="left", padx=(0, 5))  # Padding to the right
    btn2.pack(side="left", padx=(5, 0))  # Padding to the left



def process_queue(root):
    try:
        while True:
            command = command_queue.get_nowait()
            if command["command"] == "new_joy_window":
                set_joycon_type_interface(command["data"], command["player"])
    except queue.Empty:
        pass
    root.after(100, process_queue, root)


if __name__ == "__main__":
    icon = create_icon(tk_main_process)
    icon.run_detached()
    process_queue(tk_main_process)
    tk_main_process.mainloop()