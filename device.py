import time
import serial
import numpy as np


class Device:

    COM_CODES = {
        "START": b"0",
        "TIMEBASE": {
            "20 us": b"\x21",
            "50 us": b"\x22",
            "100 us": b"\x23",
            "200 us": b"\x24",
            "500 us": b"\x25",
            "1 ms": b"\x26",
            "2 ms": b"\x27",
            "5 ms": b"\x28",
            "10 ms": b"\x29",
            "20 ms": b"\x2a",
        },
        "SAMPLERATES":{
            "1.5 cycles":b"15",
            "7.5 cycles":b"75",
            "13.5 cycles":b"135",
            "28.5 cycles":b"285",
            "41.5 cycles":b"415",
            "55.5 cycles":b"555",
            "71.5 cycles":b"715",
            "239.5 cycles":b"2395",
        },
        "TRIGGER_ENABLE": b"\x31",
        "TRIGGER_DISABLE": b"\x32",
        "TRIGGER_EDGE": {
            "Rising": b"\x33",
            "Falling": b"\x34",
            "Any": b"\x35",
        },
    }
    BUFFER_SIZE = 1024  # 512
    BAUDRATE = 115200

    def __init__(self):
        self.serial_port = serial.Serial()
        self.serial_port.baudrate = self.BAUDRATE
        self.sempl_per_second = 23950
        self.timebase = "20 ms"
        self.samplerates = "1.5 cycles"
        self.trigger_on = False
        self.trigger_slope = "Rising"

    def connect(self, port):
        print(port)
        self.serial_port.port = port
        self.serial_port.open()
        time.sleep(2)  # wait until arduino is available
        self.write_all_settings()

    def disconnect(self):
        self.serial_port.close()

    def write_all_settings(self):
        self.write_timebase()
        self.write_trigger_state()
        self.write_trigger_slope()

    def write_command(self, command):
        self.serial_port.write(str(command).encode())

    def write_timebase(self):
        self.serial_port.write(self.COM_CODES["TIMEBASE"][self.timebase])

    def write_clock(self, ic, freq):
        self.serial_port.write(b"set_clock" + str(ic).encode() + b" " + str(freq).encode())

    def write_samplerates(self):
        self.serial_port.write(b"smpl " + self.COM_CODES["SAMPLERATES"][self.samplerates])
        ack = self.serial_port.readline()
        print(f"{ack}")


    def write_trigger_state(self):
        if self.trigger_on:
            self.serial_port.write(self.COM_CODES["TRIGGER_ENABLE"])
        else:
            self.serial_port.write(self.COM_CODES["TRIGGER_DISABLE"])

    def write_trigger_slope(self):
        self.serial_port.write(self.COM_CODES["TRIGGER_EDGE"][self.trigger_slope])

    def clean_buffers(self):
        self.serial_port.reset_input_buffer()
        self.serial_port.reset_output_buffer()

    def fnc(self, in_buff, idx):
        return in_buff[idx], in_buff[idx + 1]

    def acquire_single(self, ch):
        self.serial_port.write(str(ch).encode())
        data = self.serial_port.read(2)
        lb = data[0]
        hb = data[1]
        hb = hb << 8

        res = float((hb | lb) * 3300 / 4095)
        print(res)
        return res

    def acquire_single1(self):
        self.serial_port.write(self.COM_CODES["START"])
        data = self.serial_port.read(size=self.BUFFER_SIZE*2)
        var3 = []
        i = 0
        while i < self.BUFFER_SIZE*2:

            lb = data[i]
            hb = data[i + 1]

            hb = hb << 8
            i += 2
            buf = float((hb | lb) * 3.3 / 4096)
            var3 = np.append(var3, buf)
        
        #time.sleep(0.06)
        #data = np.frombuffer(data, dtype=np.uint16).astype(float) * 3.3 / 4096
        return var3

    def is_connected(self):
        return self.serial_port.is_open
