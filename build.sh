rm -rf build dist
./create_icons_script.sh
uv run setup.py py2app