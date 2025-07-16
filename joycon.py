import logging
from mouse import InputSimulator

MASKS = {
    "RIGHT": {
        "A":    0x000800,
        "B":    0x000400,
        "X":    0x000200,
        "Y":    0x000100,
        "PLUS": 0x000002,
        "STICK":0x000004,
        "SL":  0x002000,
        "SR":  0x001000,
        "R":  0x004000,
        "ZR":  0x008000,
        "HOME": 0x000010,
        "CHAT": 0x000040,
    },
    "LEFT": {
        "UP":     0x000002,
        "DOWN":   0x000001,
        "LEFT":   0x000008,
        "RIGHT":  0x000004,
        "MINUS":  0x000100,
        "STICK":  0x000800,
        "SL_MASK":  0x002000,
        "SR_MASK":  0x001000,
        "LEFT_SL_MASK":  0x000020,
        "LEFT_SR_MASK":  0x000010,
    }
}
class JoyCon:
    def __init__(self, side="RIGHT"):
        pass
        self.settings = None
        self.buttons = {
            "A": "left",
            "B": "right",
            "X": "middle"
        }
        self.input_simulator = InputSimulator()
        self.last_pressed = None
        self.side = side
        self.is_left = True if side == "LEFT" else False
        self.last_mouse_pos = (None, None)
        self.last_data = None

    def process_buttons(self, data):
        button_map = MASKS[self.side]

        offset = 4 if self.is_left else 3
        state = int.from_bytes(data[offset:offset+3], 'big')
        if self.last_data is not None:
            last_state = int.from_bytes(self.last_data[offset:offset+3], 'big') 
        else:
            last_state = 0 
        for name, val in button_map.items():
            mask = val
            pressed = bool(state & mask)
            # last_pressed = getattr(gamepad, f"_last_btn_{vg_btn}", None)
            last_pressed = bool(last_state & mask)
            if name == "R":
                if pressed and not last_pressed:
                    self.input_simulator.mouse_down()
                elif not pressed and last_pressed:
                    self.input_simulator.mouse_up()

            if name == "ZR":
                if pressed and not last_pressed:
                    self.input_simulator.mouse_down_right()
                elif not pressed and last_pressed:
                    self.input_simulator.mouse_up_right()
            

            if name == "A":
                if not pressed and last_pressed:
                    print("click")
                    self.input_simulator.mouse_double_click()
                    
            self.last_data = data
        

    def process_mouse(self, data):
        if len(data) < 0x3c:
            return None
        
        mouse_data = data[0x10:0x18]
        logging.debug(f"Mouse data: {mouse_data.hex()}")
        mouse_hex_str = ' '.join(f'{b:02X}' for b in mouse_data)
        # print(hex_str[48:75])
        # print(mouse_hex_str)


        def to_signed_16(b1, b2):
            return int.from_bytes(bytes([b1, b2]), byteorder='little', signed=True)
        

        mouse_x_raw = to_signed_16(mouse_data[0x00], mouse_data[0x01]) 
        mouse_y_raw = to_signed_16(mouse_data[0x02], mouse_data[0x03])
        if self.last_mouse_pos[0] is not None:
            mouse_x_delta = mouse_x_raw - self.last_mouse_pos[0]
            mouse_y_delta = mouse_y_raw - self.last_mouse_pos[1]
            self.input_simulator.mouse_move(mouse_x_delta, mouse_y_delta)

            self.last_mouse_pos = (mouse_x_raw, mouse_y_raw)
        else:
            self.last_mouse_pos = (mouse_x_raw, mouse_y_raw)


    def process_sticks(self, data):
        stick_data = data[10:13] if self.is_left else data[13:16]
        if len(stick_data) != 3:
            return 0, 0
        x = ((stick_data[1] & 0x0F) << 8) | stick_data[0]
        y = (stick_data[2] << 4) | ((stick_data[1] & 0xF0) >> 4)
        x = (x - 2048) / 2048.0
        y = (y - 2048) / 2048.0

        deadzone = 0.08
        if abs(x) < deadzone and abs(y) < deadzone:
            return 0, 0
        x = max(-1.0, min(1.0, x * 1.7))
        y = max(-1.0, min(1.0, y * 1.7))
        sensitivity = 4
        move_x = -int(x * sensitivity)
        # if move_x < 0 and move_x > -10:
        #     move_x = -10
        self.input_simulator.mouse_scroll(int(y * sensitivity), "vertical")
        self.input_simulator.mouse_scroll(move_x, "horizontal")
        # print(int(x * sensitivity))
        # print(x,y)