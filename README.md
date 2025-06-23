# joycon2py
A light Python script that turns the Joy Con 2's into working PC controllers.

Joy Con 2's (Switch 2) currently do not work natively on PC. This project aims to fix that.

# DISCLAIMER
This project will primarily focus on Windows (and is windows only), mostly because vgamepad is Windows exclusive. You are free to make your own MacOS/Linux version of the script however. 

# RESEARCH
Here, i'll document some of my findings for JoyCon 2's.
- Notifications
Example notification: 35ae0000000000e0ff0ffff77f20e8790000000000000000000000000000005d0e000000000000000001000000000000000000000000000000000000000000
35: Header
a3 00: Timestamp (00 increments upward when a minute passes i think)
00000000: Button inputs
e0ff0ffff77: ?
20e879 - stick data
0000000000000000000000000000005d0e000000000000000001000000000000000000000000000000000000000000: ?
Haven't found gyro/accel/battery data in here yet. Writing a LED command DOES work but notifications stop coming in. Unknown why this happens. I think its because it expects super specific command data and crashes if it doesnt get the stuff it wants, so we'll need to figure out what it wants for working LEDs and a possible IMU enable command if we need one for gyro/accel.


# DEPENDENCIES
- python (duh)  
- bleak (`pip install bleak`)  
- vgamepad (`pip install vgamepad`) (requires installation of ViGEmBus drivers, found here: https://github.com/ViGEm/ViGEmBus/releases/latest)  

# How does it work?
Starting up the program, it'll look for JoyCons. If it finds one, it'll connect to it and start looking for input notifications, through which we obtain input data from the JoyCon.  
It mainly uses bleak for this BLE stuff.  
We use vgamepad for neatly packaging it into a controller.  

# How do I use it?
- SOLO:
- Open the program up  
- Put the JoyCon you wanna add into sync mode (small button on the colored bit) 
- It'll ask you what side JoyCon it is (bits tend to be shifted on different sides so do this so your data gets sent right)  
- It'll start parsing every input from the JoyCon into an SDL XBox 360 Controller through vgamepad.  
- DUAL:
- Open the program up
- It'll ask you to put a specific side joycon into pairing (make sure you pair the correct side, as like i said bits are in different areas for diff sides)
- Once it has paired to both joycons, it'll start sending all of their inputs into a singular controller

# Can I edit the code?
Sure! Make any changes you want. Maybe make a pull request out of it..

# TODO
- Add Sideways mode to SOLO code
- Add multiplayer support? Running the script twice but pairing a diff joycon should do this but i might add it as a SOLO setting
