# joycon2py

A lightweight Python script that turns the Joy-Con 2's into working PC controllers.

Joy-Con 2's (Switch 2) currently do not work natively on PC. This project aims to fix that.

---

## DISCLAIMER

This project is **Windows-only**, primarily because `vgamepad` (used for virtual controller output) is exclusive to Windows.  
You're free to make your own macOS/Linux fork if you want.

---

## RESEARCH

Here, I'll document some findings on Joy-Con 2 behavior.

Something I've documented just in general is something I call BLE DEADMODE. It's where if you keep constantly trying to use the program, the joycons eventually can't connect unless you let them idle for a bit. This is probably because the bluetooth stuff has to cool down sometimes. So, make sure you're not trying to use the program like twice per second or something

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

---

## DEPENDENCIES

- Python (3.7+)
- [`bleak`](https://github.com/hbldh/bleak)  
  → `pip install bleak`  
- [`vgamepad`](https://github.com/yannbouteiller/vgamepad)  
  → `pip install vgamepad`  
  → Requires [ViGEmBus drivers](https://github.com/ViGEm/ViGEmBus/releases/latest) installed

---

## How does it work?

1. The program scans for Joy-Cons.
2. Once found, it connects via BLE and listens for input notifications.
3. These inputs are parsed and translated into controller actions using `vgamepad`.

---

## How do I use it?

### 🔹 SOLO Mode:

- Open the script.
- Put the Joy-Con in sync mode (small black button on the edge).
- When prompted, enter whether it’s a left or right Joy-Con.
- The script will parse and translate input to a virtual Xbox 360 controller.

### 🔸 DUAL Mode:

- Open the script.
- Follow the prompts to pair **each Joy-Con one by one** (left then right).
- The script merges both Joy-Cons into **one** unified controller.

> 💡 Note: Bit layouts differ slightly between left and right Joy-Cons, so correct side pairing is important.

---

## Can I edit the code?

Absolutely!  
Make any changes you like, or submit a pull request if you think it's worth sharing.

---

## TODO

- [ ] Add sideways mode for SOLO Joy-Con use  
- [ ] Add true multiplayer support (currently, you can run two instances of the script for two separate Joy-Cons)

---
