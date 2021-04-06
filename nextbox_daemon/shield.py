
import gpiozero

from nextbox_daemon.config import log

class Shield:
    """
    Singleton class for the NextBox Reset Board / Shield

    Use only via `shield` global instance after import
    """
    def __init__(self):
        self.led = gpiozero.RGBLED(19, 20, 21, active_high=False)
        self.button = gpiozero.Button(16, hold_time=5, hold_repeat=False)
        #self.led.on()

    def set_led(self, r, g, b):
        """Switch LED on with `(red, green, blue)` color"""
        self.led.off()
        self.led.on()

        self.led.green = max(0, min(1, g))
        self.led.red = max(0, min(1, r))
        self.led.blue = max(0, min(1, b))


    def set_led_blink(self, r, g, b):
        """Blink (2s / 50% on) LED on with `(red, green, blue)` color"""
        self.led.off()

        col = max(0, min(1, r)), max(0, min(1, g)), max(0, min(1, b))

        self.led.blink(on_color=col, off_color=(0, 0, 0))


    def set_led_off(self):
        """Switch LED off"""
        self.led.off()


    def set_led_state(self, state):
        """
        Top-level access to LED by state
        
        * 'ready'           => green
        * 'started'         => yellow
        * 'updating'        => yellow-blinking
        * 'stopped'         => red
        * 'factory-reset'   => red-blinking
        * 'button'          => blue
        """

        if state == "ready":
            self.set_led(0, 1, 0)
        elif state == "started":
            self.set_led(1, 1, 0)
        elif state == "updating":
            self.set_led_blink(1, 1, 0)
        elif state == "stopped":
            self.set_led(1, 0, 0)
        elif state == "factory-reset":
            self.set_led_blink(1, 0, 0)
        elif state == "button":
            self.set_led(0, 0, 1)
        else:
            self.set_led(0, 1, 0)
        


shield = Shield()