from pynput.mouse import Controller, Button
import time

class InputSimulator:
    def __init__(self):
        self.mouse = Controller()
        self.last_click = time.time()
        self.click_delay_time = 0

    def mouse_down(self):
        self.mouse.press(Button.left)
        click_time = time.time()
        self.click_delay_time = click_time - self.last_click
        self.last_click = click_time

    def mouse_up(self):
        self.mouse.release(Button.left)
        if self.click_delay_time * 1000 < 300:
            self.mouse_double_click()


    def mouse_down_right(self):
        self.mouse.press(Button.right)

    def mouse_up_right(self):
        self.mouse.release(Button.right)

    def mouse_double_click(self, interval=0.1):
        self.mouse.click(Button.left, 2)

    def mouse_scroll(self, movement, direction='vertical'):
        if direction == 'vertical':
            self.mouse.scroll(0,movement)
        else:
            self.mouse.scroll(movement, 0)

    def mouse_move(self, x, y):
        self.mouse.move(x,y)

if __name__ == "__main__":
    simulator = InputSimulator()
    # simulator.mouse_scroll(10, 'vertical')
    simulator.mouse_scroll(-15, 'horizontal')
                #lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal
