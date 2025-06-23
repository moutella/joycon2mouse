# joycon2py
A light Python script that turns the Joy Con 2's into working PC controllers.

# What is this?
JoyCon2Py - a project aimed at giving the Joy Con 2's life on the PC (ig while we wait for official nintendo support, if ever)

# WARNING FOR WINDOWS USERS
If you're on windows PLEASE use the windows file its sooo much better vgamepad is so good i promise (make sure to get the windows dependencies, listed below so it works)


# DEPENDENCIES
- python (duh)  
- bleak (`pip install bleak`)  
- WINDOWS:  
  - vgamepad (`pip install vgamepad`) (requires installation of ViGEmBus drivers, found here: https://github.com/ViGEm/ViGEmBus/releases/latest)  
- OTHER:  
  - pynput (`pip install pynput`)
  - screeninfo (`pip install pynput`)

# How does it work?
Starting up the program, it'll look for JoyCons. If it finds one, it'll connect to it and start looking for input notifications, through which we obtain input data from the JoyCon.  
It mainly uses bleak for this BLE stuff.  
On Windows, we use vgamepad for neatly packaging it into a controller.  
On anything else, we use pynput and a lot of dumb stuff to use your KEYBOARD AND MOUSE as the controller. Horrible, but vgamepad is windows only. What can ya do

# How do I use it?
- Open the program up  
- When using the SOLO files, put the JoyCon you wanna add into sync mode (small button on the colored bit)  
- It'll ask you what side JoyCon it is (bits tend to be shifted on different sides so do this so your data gets sent right)  
- WINDOWS: It'll start parsing every input from the JoyCon into an SDL XBox 360 Controller through vgamepad.  
- OTHER: It'll start parsing every input from the JoyCon through your keyboard and mouse. (Press F6 to toggle the joystick moving the mouse)

- DUAL: nun here yet i havent made it yet LOL

# Can I edit the code?
do whatever with the code idc.
im not the best coder so if u wanna make the ui better, parse new buttons, use different stuff whatever idc dude go for it. maybe even do a pull request of that stuff

# TODO
- Add Sideways axis/button map support  
- Add Dual JoyCon mode  
- Make the non-windows version wayyy less bad (like seriously the joystick is catastrophically bad right now)
