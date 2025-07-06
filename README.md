# joycon2py

A lightweight Python script that turns the Joy-Con 2's and the Pro Controller 2 into working PC Controllers.

---

## DISCLAIMER

This project is **Windows-only**, primarily because `vgamepad` (used for virtual controller output) is exclusive to Windows.  
You're free to make your own macOS/Linux fork if you want.

Supported controllers:  
Joy-Con 2: Full support  
Pro Controller 2: Full support  
NSO GC Controller: Semi support (Joysticks confirmed to work, buttons may not be mapped/mapped correctly in code yet, requires data sent over by someone with one)  

If the program crashes, it means it couldn't connect to your joycon, often caused by:  
1. Disconnecting and connecting in a short amount of time. Fix - Wait a little before reconnecting them
2. Pairing through a button press - this never works, please use the Sync button as directed by the program
---

## DEPENDENCIES

- Python (3.7+)
- [`bleak`](https://github.com/hbldh/bleak)  
  → `pip install bleak`  
- [`vgamepad`](https://github.com/yannbouteiller/vgamepad)  
  → `pip install vgamepad`  
  → Requires [ViGEmBus drivers](https://github.com/ViGEm/ViGEmBus/releases/latest) installed

---

## How do I use it?
- Download the whole repo (green button titled code, press download zip. you can delete readme.md if you want)
- Open the main.py script (dont open the other scripts those are modules)
- Pick your amount of players
- Pick everyone's controller
- If using a singular joycon you'll be asked if its Left or Right
- If using dual joycons itll ask you to pair one joycon then the other
- If using a pro controller/gc controller it just asks you to pair it
- When its all done, you'll have SDL controllers ready for every player to use.

- If the controller disconnects, the code will (eventually) notice the disconnection, and promptly wait for you to reconnect your controller. You do this by, again, holding down your sync button.

> 💡 Note: Bit layouts differ slightly between left and right Joy-Cons, so correct side pairing is important.
> 
---

## RESEARCH

Here, I'll document some findings on Joy-Con 2 behavior (if anyone is interested)

A documented behaviour of the controllers (every supported controller so JoyCon 2s, Pro Controller 2 etc etc) is that trying to pair them a lot in a short amount of time causes them to not connect until they haven't been attempted to pair for a while. I'm not familiar with BLE but it might just be one of its quirks. So, keep this is mind when connecting your controllers (this is noted at the DISCLAIMERS section)

### 🔔 Notifications

**Example notification:**

35ae0000000000e0ff0ffff77f20e8790000000000000000000000000000005d0e000000000000000001000000000000000000000000000000000000000000


**Breakdown:**

- `35` – Header  
- `ae00` – Timestamp (seems to increment every ~minute)  
- `00000000` – Button inputs  
- `e0ff0ffff77f` – Unknown (possibly battery or sensor flags?)  
- `20e879` – Stick data  
- `0000000000000000000000000000005d0e000000000000000001000000000000000000000000000000000000000000` – Unknown (possibly IMU/battery?)  

> ⚠️ Haven't found gyro, accel, or battery data yet.  
> Writing a **LED command works**, but it causes notifications to stop.  
> Possibly because the Joy-Con expects a strict command protocol and "crashes" if something's missing or invalid.  
> We'll need to reverse this format further to find valid LED and IMU enable subcommands.
> IMU data seems to be the zeroed out bytes, possibly enabled by commands, which we have yet to figure out.

---
