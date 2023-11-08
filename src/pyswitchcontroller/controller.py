from pyftdi import serialext  # type: ignore
from enum import IntEnum
from typing import Optional, Tuple
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
from PyQt6.QtCore import QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QBrush, QColor, QMouseEvent, QPaintEvent


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
    def __init__(self, url: str, baudrate: int = 115200) -> None:
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

    def push_button(
        self,
        button: Button,
        input_time: float = 0.1,
        pre_delay_time: float = 0,
        delay_time: float = 0,
    ) -> None:
        """push button

        Args:
            button (Button): button to push
            input_time (float, optional): time between button press and release. Defaults to 0.1.
            pre_delay_time (float, optional): time to wait before pushing the button. Defaults to 0.
            delay_time (float, optional): time to delay after button release. Defaults to 0.
        """

        sleep(pre_delay_time)
        self.press(button)
        sleep(input_time)
        self.release(button)
        sleep(delay_time)

    def initialize(self) -> None:
        """initialize controller"""
        for e in Button:
            self.release(e)

        self.tilt_left_stick(128, 128)
        self.tilt_right_stick(128, 128)


class JoystickWidget(QWidget):
    pressed = pyqtSignal(int, int)
    released = pyqtSignal(int, int)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumSize(150, 150)
        self.movingOffset = QPoint(0, 0)
        self.grabCenter = False

    def paintEvent(self, a0: Optional[QPaintEvent]):
        painter = QPainter(self)
        self.bounds = QRect(
            -self.__maxDistance, -self.__maxDistance, self.__maxDistance * 2, self.__maxDistance * 2
        ).translated(self._center())
        painter.drawRect(self.bounds)
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawEllipse(self._centerEllipse())

    def _centerEllipse(self) -> QRect:
        """円と外接する矩形

        Returns:
            QRect: 円と外接する矩形
        """
        if self.grabCenter:
            return QRect(-20, -20, 40, 40).translated(self.movingOffset)
        return QRect(-20, -20, 40, 40).translated(self._center())

    def _center(self):
        return QPoint(self.width() // 2, self.height() // 2)

    def _boundJoystick(self, point: QPoint) -> QPoint:
        """スティックの移動範囲を制限する

        Args:
            point (QPoint): マウスの座標

        Returns:
            QPoint: スティックの座標
        """
        limit_point = QPoint(point)
        if not self.bounds.contains(point):
            if self.bounds.topLeft().x() > limit_point.x():
                limit_point.setX(self.bounds.topLeft().x())
            elif self.bounds.bottomRight().x() < limit_point.x():
                limit_point.setX(self.bounds.bottomRight().x())
            if self.bounds.topLeft().y() > limit_point.y():
                limit_point.setY(self.bounds.topLeft().y())
            elif self.bounds.bottomRight().y() < limit_point.y():
                limit_point.setY(self.bounds.bottomRight().y())
        return limit_point

    def mousePressEvent(self, a0: Optional[QMouseEvent]):
        if a0 is not None:
            self.grabCenter = self._centerEllipse().contains(a0.pos())
        super().mousePressEvent(a0)

    def mouseReleaseEvent(self, a0: Optional[QMouseEvent]):
        self.grabCenter = False
        self.movingOffset = QPoint(0, 0)
        self.update()
        self.released.emit(*self.normVec())

    def normVec(self) -> Tuple[int, int]:
        """0~255に正規化されたjoyStickの座標

        Returns:
            tuple[int, int]: 0~255に正規化されたjoyStickの座標[x, y]
        """
        if not self.grabCenter:
            return 128, 128

        place = self.movingOffset - self._center() + QPoint(self.__maxDistance, self.__maxDistance)
        x = int(place.x() / (self.__maxDistance * 2) * 255)
        y = int(place.y() / (self.__maxDistance * 2) * 255)
        return x, y

    def mouseMoveEvent(self, a0: Optional[QMouseEvent]):
        if self.grabCenter and a0 is not None:
            self.movingOffset = self._boundJoystick(a0.pos())
            self.update()
        self.pressed.emit(*self.normVec())

    @property
    def __maxDistance(self) -> int:
        return min(self.width(), self.height()) // 2 - 20


class ControllerGui(QWidget):
    def __init__(self, url: Optional[str] = None, baudrate: int = 115200):
        super().__init__()
        self.url = url if url is not None else ""
        self.baudrate = baudrate
        self._init_ui()
        self._init_bind()

    def _init_ui(self):
        # URLの入力欄の作成
        self.url_label = QLabel("URL:")
        self.url_entry = QLineEdit(self.url)
        self.execute_button = QPushButton("connect")

        self.urlbox = QHBoxLayout()
        self.urlbox.addWidget(self.url_label)
        self.urlbox.addWidget(self.url_entry)
        self.urlbox.addWidget(self.execute_button)

        # 左コントローラを作成
        self.left = QVBoxLayout()
        self.minus_button = QPushButton("-")
        self.zl_button = QPushButton("ZL")
        self.l_button = QPushButton("L")
        self.l_click = QPushButton("L_click")
        self.left_joycon = JoystickWidget()
        self.up_button = QPushButton("↑")
        self.left_button = QPushButton("←")
        self.right_button = QPushButton("→")
        self.down_button = QPushButton("↓")
        self.capture_button = QPushButton("CAPTURE")

        self.left.addWidget(self.minus_button)
        self.left.addWidget(self.zl_button)
        self.left.addWidget(self.l_button)
        self.left.addWidget(self.l_click)
        self.left.addWidget(self.left_joycon)
        self.arrows = QVBoxLayout()
        self.arrows.addWidget(self.up_button)
        self.arrows_h = QHBoxLayout()
        self.arrows_h.addWidget(self.left_button)
        self.arrows_h.addWidget(self.right_button)
        self.arrows.addLayout(self.arrows_h)
        self.arrows.addWidget(self.down_button)
        self.left.addLayout(self.arrows)
        self.left.addWidget(self.capture_button)

        # 右コントローラを作成
        self.right = QVBoxLayout()
        self.plus_button = QPushButton("+")
        self.zr_button = QPushButton("ZR")
        self.r_button = QPushButton("R")
        self.x_button = QPushButton("X")
        self.y_button = QPushButton("Y")
        self.a_button = QPushButton("A")
        self.b_button = QPushButton("B")
        self.r_click = QPushButton("R_click")
        self.right_joycon = JoystickWidget()
        self.home_button = QPushButton("HOME")

        self.right.addWidget(self.plus_button)
        self.right.addWidget(self.zr_button)
        self.right.addWidget(self.r_button)
        self.buttons = QVBoxLayout()
        self.buttons.addWidget(self.x_button)
        self.buttons_h = QHBoxLayout()
        self.buttons_h.addWidget(self.y_button)
        self.buttons_h.addWidget(self.a_button)
        self.buttons.addLayout(self.buttons_h)
        self.buttons.addWidget(self.b_button)
        self.right.addLayout(self.buttons)
        self.right.addWidget(self.r_click)
        self.right.addWidget(self.right_joycon)
        self.right.addWidget(self.home_button)

        # 左右コントローラをまとめる
        self.controller = QHBoxLayout()
        self.controller.addLayout(self.left)
        self.controller.addLayout(self.right)

        self.all_layout = QVBoxLayout()
        self.all_layout.addLayout(self.urlbox)
        self.all_layout.addLayout(self.controller)
        self.setLayout(self.all_layout)

    def _init_bind(self):
        self.execute_button.clicked.connect(self.connect)

        self.minus_button.pressed.connect(lambda: self.button_press(Button.MINUS))
        self.minus_button.released.connect(lambda: self.button_release(Button.MINUS))
        self.zl_button.pressed.connect(lambda: self.button_press(Button.ZL))
        self.zl_button.released.connect(lambda: self.button_release(Button.ZL))
        self.l_button.pressed.connect(lambda: self.button_press(Button.L))
        self.l_button.released.connect(lambda: self.button_release(Button.L))
        self.l_click.pressed.connect(lambda: self.button_press(Button.LCLICK))
        self.l_click.released.connect(lambda: self.button_release(Button.LCLICK))
        self.left_joycon.pressed.connect(lambda x, y: self.tilt_left(x, y))
        self.left_joycon.released.connect(lambda x, y: self.tilt_left(128, 128))
        self.up_button.pressed.connect(lambda: self.button_press(Button.UP))
        self.up_button.released.connect(lambda: self.button_release(Button.UP))
        self.left_button.pressed.connect(lambda: self.button_press(Button.LEFT))
        self.left_button.released.connect(lambda: self.button_release(Button.LEFT))
        self.right_button.pressed.connect(lambda: self.button_press(Button.RIGHT))
        self.right_button.released.connect(lambda: self.button_release(Button.RIGHT))
        self.down_button.pressed.connect(lambda: self.button_press(Button.DOWN))
        self.down_button.released.connect(lambda: self.button_release(Button.DOWN))
        self.capture_button.pressed.connect(lambda: self.button_press(Button.CAPTURE))
        self.capture_button.released.connect(lambda: self.button_release(Button.CAPTURE))

        self.plus_button.pressed.connect(lambda: self.button_press(Button.PLUS))
        self.plus_button.released.connect(lambda: self.button_release(Button.PLUS))
        self.zr_button.pressed.connect(lambda: self.button_press(Button.ZR))
        self.zr_button.released.connect(lambda: self.button_release(Button.ZR))
        self.r_button.pressed.connect(lambda: self.button_press(Button.R))
        self.r_button.released.connect(lambda: self.button_release(Button.R))
        self.x_button.pressed.connect(lambda: self.button_press(Button.X))
        self.x_button.released.connect(lambda: self.button_release(Button.X))
        self.y_button.pressed.connect(lambda: self.button_press(Button.Y))
        self.y_button.released.connect(lambda: self.button_release(Button.Y))
        self.a_button.pressed.connect(lambda: self.button_press(Button.A))
        self.a_button.released.connect(lambda: self.button_release(Button.A))
        self.b_button.pressed.connect(lambda: self.button_press(Button.B))
        self.b_button.released.connect(lambda: self.button_release(Button.B))
        self.r_click.pressed.connect(lambda: self.button_press(Button.RCLICK))
        self.r_click.released.connect(lambda: self.button_release(Button.RCLICK))
        self.right_joycon.pressed.connect(lambda x, y: self.tilt_right(x, y))
        self.right_joycon.released.connect(lambda x, y: self.tilt_right(128, 128))
        self.home_button.pressed.connect(lambda: self.button_press(Button.HOME))
        self.home_button.released.connect(lambda: self.button_release(Button.HOME))

    def connect(self):
        try:
            self.url = self.url_entry.text()
            self.con = Controller(self.url, self.baudrate)
            print("connect")
        except:
            self.con = None
            print("not connect")

    def button_press(self, button: Button):
        if self.con is None:
            print("not connected")
            return
        self.con.press(button)

    def button_release(self, button: Button):
        if self.con is None:
            print("not connected")
            return
        self.con.release(button)

    def tilt_left(self, x: int, y: int):
        if self.con is None:
            print("not connected")
            return
        self.con.tilt_left_stick(x, y)

    def tilt_right(self, x: int, y: int):
        if self.con is None:
            print("not connected")
            return
        self.con.tilt_right_stick(x, y)


def show_devices():
    from pyftdi.ftdi import Ftdi  # type: ignore

    Ftdi.show_devices()


if __name__ == "__main__":
    from time import sleep

    for e in Button:
        print(e)
    show_devices()
    app = QApplication(sys.argv)
    window = ControllerGui("ftdi://ftdi:232:A50285BI/1")
    window.show()
    app.exec()
    # window.con.push_button(Button.A)
    # window.con.initialize()
