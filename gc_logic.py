# gc_logic.py

import traceback

async def handle_gc_notification(sender, data, gamepad):
    try:
        print(f"[NSO GameCube] RAW notification from {sender}: {data.hex()}")
    except Exception as e:
        print("⚠️ Error in GC notification handler:", e)
        traceback.print_exc()
