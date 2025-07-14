import pyautogui

pyautogui.FAILSAFE = False          # keep the corner-abort feature
pyautogui.PAUSE   = 0              # disable the global 100 ms pause
pyautogui.MINIMUM_DURATION = 0     # no forced smoothing


class InputSimulator:

    def mouse_down(self):
        pyautogui.mouseDown()

    def mouse_up(self):
        pyautogui.mouseUp()


    def mouse_down_right(self):
        pyautogui.mouseDown(button='right')

    def mouse_up_right(self):
        pyautogui.mouseUp(button='right')

    def mouse_scroll(self, movement, direction='vertical'):
        if direction == 'vertical':
            pyautogui.scroll(movement)
        else:
            pyautogui.hscroll(movement)

    def mouse_move(self, x, y):
        pyautogui.moveRel(x, y, duration=0)

    def click(self, button='left'):
        pyautogui.click(button=button)

if __name__ == "__main__":
    simulator = InputSimulator()
    # simulator.mouse_scroll(10, 'vertical')
    simulator.mouse_scroll(-15, 'horizontal')
                #lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal#lalalalalallalalal
