
import gpiozero

from nextbox_daemon.config import log

class Shield:
    def __init__(self):
        self.led = gpiozero.RGBLED(19, 20, 21, active_high=False)
        #self.led.on()

    def set_led(self, r, g, b):
        self.led.on()

        self.led.green = max(0, min(1, g))
        self.led.red = max(0, min(1, r))
        self.led.blue = max(0, min(1, b))


    def set_led_off(self):
        self.led.off()
    