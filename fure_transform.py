import numpy as np
from scipy.fft import fft, fftfreq
from device import Device
from scipy.signal import blackman

class Spectr:
    def __init__(self):
        self.device = Device()
        self.fft_light = self.device.BUFFER_SIZE
        self.freq_grid = 0
        self.magnitude = 0
        self.semple_per_second = self.device.sempl_per_second
        self.sample_cpicing = 1.0 / 29250

    def get_spectr_buff(self, data):
        window = blackman(self.fft_light)
        self.magnitude = fft(data * 10 )#* window
        self.freq_grid = fftfreq(self.fft_light, self.sample_cpicing)[:self.fft_light//2]
        return 2.0/self.device.BUFFER_SIZE * np.abs(self.magnitude[0:self.device.BUFFER_SIZE//2]), self.freq_grid,

'''
from serial.tools import list_ports
import serial

import matplotlib.pyplot as plt

start = b"\x10"

# Get nanovna device automatically
def getport() -> str:
    VID = 0x0483 #1155
    PID = 0x5740 #22336
    device_list = list_ports.comports()
    for device in device_list:
        if device.vid == VID and device.pid == PID:
            return device.device
    raise OSError("device not found")


def fnc(in_buff, idx):
    return in_buff[idx], in_buff[idx + 1]


def main():

    len = 512

    stm = serial.Serial(getport(), 115200)  

    ip = 0
    while ip < 1:

        stm.write(start)
        data = stm.read(len * 2)

        var3 = np.array([])

        i = 0
        while i < len * 2:

            lb, hb = fnc(data, i)

            hb = hb << 8
            i += 2
            buf = float((hb | lb) * 3.3 / 4096)
            var3 = np.append(var3, buf)
        
        ip += 1

    print(var3)

    N = len
    T = 1.0 / 23950.0

    yf = fft(var3)
    xf = fftfreq(N, T)[:N//2]
    print(yf)
    print(xf)

    print(2.0/N * np.abs(yf[0:N//2]))

    plt.plot(xf, 2.0/N * np.abs(yf[0:N//2]))
    plt.grid()
    plt.show()

    stm.close()

    
if __name__ == '__main__':
    main()
'''