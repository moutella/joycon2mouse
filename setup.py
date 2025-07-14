from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'packages': ["PIL", "pyautogui", "uvicorn", "rumps"],
    'iconfile': 'JoyCon2Mouse.icns',  # Optional
    'plist': 'Info.plist',
    'excludes': ['rubicon'],
    'resources': ['assets']
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
