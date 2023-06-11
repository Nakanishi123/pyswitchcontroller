from pyftdi import serialext
from time import sleep
from enum import IntEnum, Enum
from typing import Optional
import sys
from PyQt6.QtWidgets import (
    QWidget,
    QApplication,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)
from PyQt6.QtCore import QPointF, QRectF, QLineF, QPoint, QRect, QLine, pyqtSignal
from PyQt6.QtGui import QPainter, QBrush, QColor, QMouseEvent


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
        command = b"S" + button.value.to_bytes(1, "big") + b"\x01\x45"
        self.port.write(command)

    def release(self, button: Button) -> None:
        """release button

        Args:
            button (Button): button to release
        """
        command = b"S" + button.value.to_bytes(1, "big") + b"\xf2\x45"
        self.port.write(command)

    def tilt_left_stick(self, x: int, y: int) -> None:
        """tilt left stick

        Args:
            x (int): x coordinate center: 128 min: 0 max: 255
            y (int): y coordinate center: 128 min: 0 max: 255
        """
        if x < 0 or x > 255 or y < 0 or y > 255:
            raise ValueError("x and y must be between 0 and 255")

        command = (
            b"S"
            + JoyStick.leftX.value.to_bytes(1, "big")
            + x.to_bytes(1, "big")
            + b"E"
            + b"S"
            + JoyStick.leftY.value.to_bytes(1, "big")
            + y.to_bytes(1, "big")
            + b"E"
        )
        self.port.write(command)

    def tilt_right_stick(self, x: int, y: int) -> None:
        """tilt right stick

        Args:
            x (int): x coordinate center: 128 min: 0 max: 255
            y (int): y coordinate center: 128 min: 0 max: 255
        """
        if x < 0 or x > 255 or y < 0 or y > 255:
            raise ValueError("x and y must be between 0 and 255")

        command = (
            b"S"
            + JoyStick.rightX.value.to_bytes(1, "big")
            + x.to_bytes(1, "big")
            + b"E"
            + b"S"
            + JoyStick.rightY.value.to_bytes(1, "big")
            + y.to_bytes(1, "big")
            + b"E"
        )
        self.port.write(command)

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
