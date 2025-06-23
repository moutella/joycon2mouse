# joycon2py

A lightweight Python script that turns the Joy-Con 2's into working PC controllers.

Joy-Con 2's (Switch 2) currently do not work natively on PC. This project aims to fix that.

---

## DISCLAIMERS 
Hey! Noticing some people are actually checking out the repo. Please bear with me while I work on ironing out bugs!!
Also, if you have the Pro Controller 2, please use procon2.py to give me data from it! That way, I can actually make a working file for the ProCon2. Thanks alot!

---

This project is **Windows-only**, primarily because `vgamepad` (used for virtual controller output) is exclusive to Windows.  
You're free to make your own macOS/Linux fork if you want.

Is only compatible with JoyCon 2 so far. When data from procon2.py gets given and I fix the file, it'll support the ProCon2, given it works similar to the JoyCon2s.

---

## DEPENDENCIES

- Python (3.7+)
- [`bleak`](https://github.com/hbldh/bleak)  
  → `pip install bleak`  
- [`vgamepad`](https://github.com/yannbouteiller/vgamepad)  
  → `pip install vgamepad`  
  → Requires [ViGEmBus drivers](https://github.com/ViGEm/ViGEmBus/releases/latest) installed

  ## How do I use it?

### 🔹 SOLO Mode:

- IMPORTANT: It'll assume you're using it sideways. Use it in that orientation (or edit the code to not, if you want.)

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

## How does it work?

1. The program scans for Joy-Cons.
2. Once found, it connects via BLE and listens for input notifications.
3. These inputs are parsed and translated into controller actions using `vgamepad`.

---


---

## RESEARCH

Here, I'll document some findings on Joy-Con 2 behavior.

Something I've documented just in general is something I call BLE DEADMODE. It's where if you keep constantly trying to use the program/connect the joycons a ton, the joycons eventually can't connect unless you let them idle for a bit. This is probably because the bluetooth stuff has to cool down sometimes. So, make sure you're not trying to use the program like twice per second or something

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

## Can I edit the code?

Absolutely!  
Make any changes you like, or submit a pull request if you think it's worth sharing.

---

## TODO

- [ ] Add multiplayer mode, connecting and making two controllers in the same file (right now opening the script twice and pairing dif joycon in each one does this, but i think the rework will be a bit cleaner)

---
