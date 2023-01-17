from PySide6.QtCore import QMutex, QObject, QThread, QTimer, QWaitCondition, Signal
from PySide6.QtWidgets import QApplication, QMessageBox
import serial.tools.list_ports
from main_window import MainWindow
from device import Device
from fure_transform import Spectr
from serial.tools import list_ports

import time
import numpy as np


class Controller:
    def __init__(self):

        # gui
        self.app = QApplication([])
        self.main_window = MainWindow(controller=self)
        self.eee = 1
        # device
        self.device = Device()
        self.fast_fure = Spectr()

        self.het = 0
        self.ref = 0

        # fps stats
        self.fps_timer = QTimer()
        #self.fps_timer.timeout.connect(self.update_ui_fps)
        self.spf = 1  # seconds per frame
        self.timestamp_last_capture = 0

        # acquisition thread
        self.continuous_acquisition = False
        self.worker_wait_condition = QWaitCondition()
        self.acquisition_worker = AcquisitionWorker(
            self.worker_wait_condition, device=self.device
        )
        self.acquisition_thread = QThread()
        self.acquisition_worker.moveToThread(self.acquisition_thread)
        self.acquisition_thread.started.connect(self.acquisition_worker.run)
        self.acquisition_worker.finished.connect(self.acquisition_thread.quit)
        # self.acquisition_worker.finished.connect(self.acquisition_thread.deleteLater)
        # self.acquisition_thread.finished.connect(self.acquisition_worker.deleteLater)
        self.acquisition_worker.data_ready.connect(self.data_ready_callback)
        #self.acquisition_worker.data_ready_spectr.connect(self.data_spectr_ready_callback)
        self.acquisition_thread.start()
        self.data_time_array = (np.arange(0, 1000) * 1000)
        self.dataggg = np.arange(0, 10000)
        # default timebase
        #self.set_timebase("20 ms")

        # on app exit
        self.app.aboutToQuit.connect(self.on_app_exit)

    def getport(self):
        VID = 0x0483 #1155
        PID = 0x5740 #22336
        device_list = list_ports.comports()
        for device in device_list:
            if device.vid == VID and device.pid == PID:
                return device.device
        return "device not found"
        #raise OSError("device not found")

    def run_app(self):
        if self.getport() != "device not found":
            self.device.connect(self.getport())
            self.oscilloscope_continuous_run()
        self.main_window.show()
        return self.app.exec_()

    def get_ports_names(self):
        return [p.device for p in serial.tools.list_ports.comports()]

    def update_ui_fps(self):

        fps = 1 / self.spf
        self.main_window.control_panel.stats_panel.fps_label.setText(f"{fps:.2f} fps")
        self.main_window.control_panel.delta_herz_label.dlta_label.setText(f"{self.ref - self.het} Hz")


    def set_timebase(self, timebase: str):
        # send timebase to device
        self.device.timebase = timebase
        if self.is_device_connected():
            self.device.write_samplerates()
        # adjust timebase in the osc_screen
        seconds_per_sample = (
            float(timebase.split()[0])
            / 10
            * {"ms": 1e-3, "us": 1e-6}[timebase.split()[1]]
        )
        self.data_time_array = (
            np.arange(0, self.device.BUFFER_SIZE) * seconds_per_sample
        )
        #self.main_window.CHANNEL0.setXRange(
        #    0, self.device.BUFFER_SIZE * seconds_per_sample, padding=0.02
        #)
        #self.main_window.CHANNEL0.setYRange(0, 3.3)

    def set_sample_rate(self, sample_list:str):
        self.device.samplerates = sample_list
        if self.is_device_connected():
            self.device.write_samplerates()

    def set_trigger_state(self, on):
        self.device.trigger_on = on
        if self.is_device_connected():
            self.device.write_trigger_state()

    def set_trigger_slope(self, slope):
        self.device.trigger_slope = slope
        if self.is_device_connected():
            self.device.write_trigger_slope()

    def connect_to_device(self, port):
        if port == "":
            QMessageBox.about(
                self.main_window,
                "Connection failed",
                "Could not connect to device. No port is selected.",
            )
        elif port not in self.get_ports_names():
            QMessageBox.about(
                self.main_window,
                "Connection failed",
                f"Could not connect to device. Port {port} not available. Refresh and try again.",
            )
        else:
            self.device.connect(port)

    def disconnect_device(self):
        self.device.disconnect()

    def is_device_connected(self):
        return self.device.is_connected()

    def write_command(self, cmd):
        self.device.write_command(cmd)

    def show_no_connection_message(self):
        QMessageBox.about(
            self.main_window,
            "Device not connected",
            "No device is connected. Connect a device first.",
        )

    def oscilloscope_single_run(self):
        if self.device.is_connected():
            self.continuous_acquisition = False
            self.device.clean_buffers()
            self.worker_wait_condition.notify_one()
            return True
        else:
            self.show_no_connection_message()
            return False

    def oscilloscope_continuous_run(self):
        if self.device.is_connected():
            self.timestamp_last_capture = time.time()
            self.spf = 0.1
            self.fps_timer.start(500)
            self.continuous_acquisition = True
            self.device.clean_buffers()
            self.worker_wait_condition.notify_one()
            return True
        else:
            self.show_no_connection_message()
            print("Disconnected STM")
            return False

    def oscilloscope_stop(self):
        self.continuous_acquisition = False
        self.fps_timer.stop()


    def data_ready_callback(self):
        if self.device.is_connected():
            curr_time = time.time()
            #self.spf = 0.9 * (curr_time - self.timestamp_last_capture) + 0.1 * self.spf
            #self.timestamp_last_capture = curr_time
            self.main_window.CHANNEL0.update_ch(self.data_time_array, self.dataggg)
            self.eee += 1
            time.sleep(0.01)
            if self.continuous_acquisition == True:
                self.worker_wait_condition.notify_one()
            else:
                print("self.continuous_acquisition == False")
        else:
            self.show_no_connection_message()
            print("Disconnected STM")


    def on_app_exit(self):
        print("exiting")


class AcquisitionWorker(QObject):

    finished = Signal()
    data_ready = Signal()
    
    def __init__(self, wait_condition, device, parent=None):
        super().__init__(parent=parent)
        self.wait_condition = wait_condition
        self.device = device
        self.mutex = QMutex()

    def run(self):

        while True:
            self.mutex.lock()
            self.wait_condition.wait(self.mutex)
            self.mutex.unlock()

            self.data = self.device.acquire_single(0)
            self.data_ready.emit()

        self.finished.emit()
