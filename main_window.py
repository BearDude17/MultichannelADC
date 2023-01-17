from curses.panel import bottom_panel
from tkinter import CENTER
from tkinter.tix import MAX
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QMainWindow,
    QPushButton,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QApplication,

)
import pyqtgraph as pg
from serial.tools import list_ports


class OscilloscopeScreen(pg.PlotWidget):
    def __init__(self, parent=None, plotItem=None, **kargs):
        super().__init__(parent=parent, background="black", plotItem=plotItem, **kargs)

        styles = {"color": "k", "font-size": "12px"}
        self.setLabel("left", "V", **styles)
        self.setLabel("bottom", "s", **styles)

        self.showGrid(x=True, y=True)
        

        self.enableAutoRange(axis='x')



        #self.setXRange(0, 0, padding=0.02)
        self.setYRange(0, 3300, padding=0.02)

        self.pen_ch1 = pg.mkPen(color="r", width=1)

        self.plot_ch([0, 0], [0, 0])

    def plot_ch(self, x, y, ch=1):
        self.data_line_ch = self.plot(x, y, pen=self.pen_ch1)

    def update_ch(self, x, y, ch=1):
        self.data_line_ch.setData(x, y)

class SpectrScreen(pg.PlotWidget):
    def __init__(self, parent=None, plotItem=None, **kargs):
        super().__init__(parent=parent, background="w", plotItem=plotItem, **kargs)


        styles = {"color": "k", "font-size": "12px"}
        self.setLabel("left", "V", **styles)
        self.setLabel("bottom", "s", **styles)

        self.showGrid(x=True, y=True)
        self.setXRange(0, 420000, padding=0.02)

        self.setYRange(0, 1, padding=0.02)

        self.pen_ch1 = pg.mkPen(color="r", width=1)

        self.plot_ch([0, 420000], [0, 0])

    def plot_ch(self, x, y, ch=1):
        self.data_line_ch = self.plot(x, y, pen=self.pen_ch1)

    def update_ch(self, x, y, ch=1):
        self.data_line_ch.setData(x, y)

class ChannelBox(QGroupBox):
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent=parent)
        self.setCheckable(True)
        self.setChecked(True)

        vbox = QVBoxLayout()
        self.setLayout(vbox)

        vbox.addWidget(QLabel("Scale"))
        vbox.addWidget(QLabel("Position (V)"))


class TimebaseBox(QGroupBox):
    def __init__(self, controller, parent=None):
        super().__init__("Timebase", parent=parent)
        self.controller = controller

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.timebase_options = [
            "100 us",
            "200 us",
            "500 us",
            "1 ms",
            "2 ms",
            "5 ms",
            "10 ms",
            "20 ms",
        ]
        self.combobox_timebase = QComboBox()
        self.combobox_timebase.addItems(self.timebase_options)
        self.combobox_timebase.setCurrentIndex(7)

        layout.addWidget(QLabel("time/div (1 div = 1/10 graph)"))
        layout.addWidget(self.combobox_timebase)

        self.combobox_timebase.currentTextChanged.connect(self.set_timebase)

    def set_timebase(self):
        self.timebase = self.combobox_timebase.currentText()
        self.controller.set_timebase(self.timebase)


class SampleBox(QGroupBox):
    def __init__(self, controller, parent=None):
        super().__init__("Sample per second", parent=parent)
        self.controller = controller

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.timebase_options = [
            "0.05",
            "0.10",
            "0.20",
            "0.50",
            "1.0",
            "2.0",

        ]
        self.combobox_timebase = QComboBox()
        self.combobox_timebase.addItems(self.timebase_options)
        self.combobox_timebase.setCurrentIndex(2)

        layout.addWidget(QLabel("Frame"))
        layout.addWidget(self.combobox_timebase)
        self.combobox_timebase.currentTextChanged.connect(self.set_sample_rate)

    def set_sample_rate(self):
        timebase = self.combobox_timebase.currentText()
        if timebase == self.timebase_options[0]:
            self.controller.change_sample_time(50)
        if timebase == self.timebase_options[1]:
            self.controller.change_sample_time(100)
        if timebase == self.timebase_options[2]:
            self.controller.change_sample_time(200)
        if timebase == self.timebase_options[3]:
            self.controller.change_sample_time(500)
        if timebase == self.timebase_options[4]:
            self.controller.change_sample_time(1000)
        if timebase == self.timebase_options[5]:
            self.controller.change_sample_time(2000)



class TriggerBox(QGroupBox):
    def __init__(self, controller, parent=None):
        super().__init__("Trigger", parent=parent)
        self.controller = controller

        self.setCheckable(True)
        self.setChecked(False)

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.combobox_slope = QComboBox()
        self.combobox_slope.addItems(["Rising", "Falling", "Any"])
        self.combobox_slope.setCurrentIndex(0)

        layout.addWidget(QLabel("Trigger slope"))
        layout.addWidget(self.combobox_slope)

        self.toggled.connect(self.controller.set_trigger_state)
        self.combobox_slope.currentTextChanged.connect(
            self.controller.set_trigger_slope
        )


class AcquisitionBox(QGroupBox):
    def __init__(self, controller, parent=None):
        super().__init__("Acquisition", parent=parent)
        self.controller = controller

        self.is_running = False

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.button_run = QPushButton("RUN")
        self.button_single = QPushButton("SINGLE")

        layout.addWidget(self.button_run)
        layout.addWidget(self.button_single)

        self.button_single.clicked.connect(self.on_single_button)
        self.button_run.clicked.connect(self.on_run_stop_button)

    def on_run_stop_button(self):
        if self.is_running:
            self.controller.oscilloscope_stop()
            self.is_running = False
            self.button_run.setText("RUN")
        else:
            if self.controller.oscilloscope_continuous_run():
                self.is_running = True
                self.button_run.setText("STOP")

    def on_single_button(self):
        self.controller.oscilloscope_single_run()
        self.is_running = False
        self.button_run.setText("RUN")


class StatsBox(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Stats", parent=parent)

        self.fps_label = QLabel("0 fps")

        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Refresh rate:"))
        layout.addWidget(self.fps_label)


class DeviceBox(QGroupBox):
    def __init__(self, controller, parent=None):
        super().__init__("Device", parent=parent)
        self.controller = controller

        self.is_connected = False

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.button_refresh = QPushButton("Refresh")
        self.combobox_ports = QComboBox()
        self.button_connect = QPushButton("Connect")

        self.layout.addWidget(self.button_refresh)
        self.layout.addWidget(self.combobox_ports)
        self.layout.addWidget(self.button_connect)

        self.button_refresh.clicked.connect(self.refresh_ports)
        self.button_connect.clicked.connect(self.connect_to_device)

        # Get nanovna device automatically
    def getport(self) -> str:
        VID = 0x0483 #1155
        PID = 0x5740 #22336
        device_list = list_ports.comports()
        for device in device_list:
            if device.vid == VID and device.pid == PID:
                return device.device
        raise OSError("device not found")


    def refresh_ports(self):
        self.combobox_ports.clear()            
        self.combobox_ports.addItems(self.controller.get_ports_names())

    def connect_to_device(self):

        if not self.is_connected:
            port = self.combobox_ports.currentText()
            self.controller.connect_to_device(port)
        else:
            self.controller.disconnect_device()

        self.is_connected = self.controller.is_device_connected()
        if self.is_connected:
            self.button_connect.setText("Disconnect")
        else:
            self.button_connect.setText("Connect")


        #def enterPress(self):
        #        print("Enter pressed")


class ShareWindowHETERODINE(QGroupBox):

    def __init__(self, controller, parent=None):
        super().__init__("Command sender HETERODINE", parent=parent)
        self.controller = controller

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.widget = QLineEdit()
        self.widget.setMaxLength(10)
        self.widget.setPlaceholderText("Enter clock HZ")

        self.widget.setText("39900000")

        self.controller.het = 39900000

        self.widget.returnPressed.connect(self.return_pressed)

        self.layout.addWidget(self.widget)


    def return_pressed(self):
        print(self.widget.text())
        self.controller.het = int(self.widget.text())
        self.controller.write_command("clk 1 " + self.widget.text())

class ShareWindowREFERENCE(QGroupBox):

    def __init__(self, controller, parent=None):
        super().__init__("Command sender REFERENCE", parent=parent)
        self.controller = controller

        self.layout = QHBoxLayout()
    
        self.setLayout(self.layout)

        self.widget = QLineEdit()
        self.widget.setMaxLength(10)
        self.widget.setPlaceholderText("Enter clock Hz")
        
        self.widget.setText("40000000")
        self.controller.ref = 40000000

        self.widget.returnPressed.connect(self.return_pressed)


        self.layout.addWidget(self.widget)

    def return_pressed(self):
        print(self.widget.text())
        self.controller.ref = int(self.widget.text())
        self.controller.write_command("clk 0 " + self.widget.text())


class StatsBoxDelta(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Delta", parent=parent)

        self.dlta_label = QLabel("0 Hz")

        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Ref - Het"))
        layout.addWidget(self.dlta_label)

class ControlPanel(QFrame):
    def __init__(self, controller, parent=None):
        super().__init__(parent=parent)
        self.controller = controller

        self.setFrameStyle(QFrame.StyledPanel)

        self.sample_panel = SampleBox(self.controller)
        self.dev_panel = DeviceBox(self.controller)

        self.layout = QVBoxLayout()

        self.layout.addWidget(self.sample_panel)

        self.layout.addStretch()

        self.layout.addWidget(self.dev_panel)

        self.setLayout(self.layout)


class MainWindow(QMainWindow):
    def __init__(self, controller, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.controller = controller

        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("stm32")

        size = 240
        self.LEFT_CHANNEL = QVBoxLayout()
        self.RIGHT_CHANNEL = QVBoxLayout()

        self.content_layout = QHBoxLayout()

        self.CHANNEL0 = OscilloscopeScreen()
        self.CHANNEL1 = OscilloscopeScreen()
        self.CHANNEL2 = OscilloscopeScreen()
        self.CHANNEL3 = OscilloscopeScreen()
        self.CHANNEL4 = OscilloscopeScreen()

        self.CHANNEL5 = OscilloscopeScreen()
        self.CHANNEL6 = OscilloscopeScreen()
        self.CHANNEL7 = OscilloscopeScreen()
        self.CHANNEL8 = OscilloscopeScreen()
        self.CHANNEL9 = OscilloscopeScreen()

        self.LEFT_CHANNEL.addWidget(self.CHANNEL0)
        self.LEFT_CHANNEL.addWidget(self.CHANNEL1)
        self.LEFT_CHANNEL.addWidget(self.CHANNEL2)
        self.LEFT_CHANNEL.addWidget(self.CHANNEL3)
        self.LEFT_CHANNEL.addWidget(self.CHANNEL4)

        #self.RIGHT_CHANNEL.addWidget(self.CHANNEL5)
        #self.RIGHT_CHANNEL.addWidget(self.CHANNEL6)
        #self.RIGHT_CHANNEL.addWidget(self.CHANNEL7)
        #self.RIGHT_CHANNEL.addWidget(self.CHANNEL8)
        #self.RIGHT_CHANNEL.addWidget(self.CHANNEL9)


        #self.screen_layoute.addStretch()
        self.control_panel = ControlPanel(self.controller)


        self.control_panel.setFixedWidth(300)


        self.content_layout.addLayout(self.LEFT_CHANNEL)
        self.content_layout.addLayout(self.RIGHT_CHANNEL)


        self.content_layout.addWidget(self.control_panel)

        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(self.content_layout)

        self.setGeometry(0, 0, 2560, 1000)
