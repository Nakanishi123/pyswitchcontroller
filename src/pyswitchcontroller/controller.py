from pyftdi import serialext
from time import sleep
from enum import IntEnum, Enum, auto


class Button(IntEnum):
    B = 0
    A = 1
    Y = 2
    X = 3
    L = 4
    R = 5
    ZL = 6
    ZR = 7
    MINUS = 8
    PLUS = 9
    LCLICK = 10
    RCLICK = 11
    UP = 12
    DOWN = 13
    LEFT = 14
    RIGHT = 15
    HOME = 16
    CAPTURE = 17


class JoyStick(IntEnum):
    leftX = 18
    leftY = 19
    rightX = 20
    rightY = 21


class Controller:
    def __init__(self, url: str, baudrate=115200) -> None:
        self.port = serialext.serial_for_url(url, baudrate=baudrate)

    def press(self, button: Button) -> None:
        """press button

        Args:
            button (Button): button to press
        """
        self.port.write(b"S")
        self.port.write([button.value])
        self.port.write([1])
        self.port.write(b"E")

    def release(self, button: Button) -> None:
        """release button

        Args:
            button (Button): button to release
        """
        self.port.write(b"S")
        self.port.write([button.value])
        self.port.write([14])
        self.port.write(b"E")

    def tilt_left_stick(self, x: int, y: int) -> None:
        """tilt left stick

        Args:
            x (int): x coordinate center: 128 min: 0 max: 255
            y (int): y coordinate center: 128 min: 0 max: 255
        """
        if x < 0 or x > 255 or y < 0 or y > 255:
            raise ValueError("x and y must be between 0 and 255")

        self.port.write(b"S")
        self.port.write([JoyStick.leftX.value])
        self.port.write([x])
        self.port.write(b"E")

        self.port.write(b"S")
        self.port.write([JoyStick.leftY.value])
        self.port.write([y])
        self.port.write(b"E")

    def tilt_right_stick(self, x: int, y: int) -> None:
        """tilt right stick

        Args:
            x (int): x coordinate center: 128 min: 0 max: 255
            y (int): y coordinate center: 128 min: 0 max: 255
        """
        if x < 0 or x > 255 or y < 0 or y > 255:
            raise ValueError("x and y must be between 0 and 255")

        self.port.write(b"S")
        self.port.write([JoyStick.rightX.value])
        self.port.write([x])
        self.port.write(b"E")

        self.port.write(b"S")
        self.port.write([JoyStick.rightY.value])
        self.port.write([y])
        self.port.write(b"E")

    def push_button(self, button: Button, input_time: float = 0.1) -> None:
        """push button

        Args:
            button (Button): button to push
            input_time (float, optional): time between button press and release. Defaults to 0.1.
        """
        self.press(button)
        sleep(input_time)
        self.release(button)


def show_devices():
    from pyftdi.ftdi import Ftdi

    Ftdi.show_devices()
