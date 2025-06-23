# joycon2py
A light Python script that turns the Joy Con 2's into working PC controllers.

# What is this?
JoyCon2Py - a project aimed at giving the Joy Con 2's life on the PC (ig while we wait for official nintendo support, if ever)

# How does it work?
Starting up the program, it'll look for JoyCons. If it finds one, it'll connect to it and start looking for input notifications, through which we obtain input data from the JoyCon. 
It mainly uses bleak for this BLE stuff.
On Windows, we use vgamepad for neatly packaging it into a controller.
On anything else, we use pygame and a lot of dumb stuff to use your KEYBOARD AND MOUSE as the controller. Horrible, but vgamepad is windows only. What can ya do

# How do I use it?
- Open the program up
- When using the SOLO files, put the JoyCon you wanna add into sync mode (small button on the colored bit)
- It'll ask you what side JoyCon it is (bits tend to be shifted on different sides so do this so your data gets sent right)
- WINDOWS: It'll start parsing every input from the JoyCon into an SDL XBox 360 Controller through vgamepad.
- OTHER: It'll start parsing every input from the JoyCon through your keyboard and mouse.

- DUAL: nun here yet i havent made it yet LOL

# TODO
- Add Sideways axis/button map support
- Add Dual JoyCon mode
- make less dumb
