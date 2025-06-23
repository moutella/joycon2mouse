# joycon2py
repo for the joycon2py syncer script

# What is this?
JoyCon2Py - a project aimed at giving the Joy Con 2's life on the PC (ig while we wait for official nintendo support, if ever)

# How does it work?
Starting up the program, it'll look for JoyCons. If it finds one, it'll connect to it and start looking for input notifications, through which we obtain input data from the JoyCon. T
It mainly uses bleak for this BLE stuff.
On Windows, we use vgamepad for neatly packaging it into a controller.
On anything else, we use pygame and a lot of dumb stuff to use your KEYBOARD AND MOUSE as the controller. Horrible, but vgamepad is windows only. What can ya do

# TODO
Unlink the left/right checker from my addresses so that it can actually be added to the repo
