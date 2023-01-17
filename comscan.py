import serial
from serial.tools import list_ports
import time

def get_ports_names():
   return [p.device for p in serial.tools.list_ports.comports()]

def getport():
    VID = 0x0483 #1155
    PID = 0x5740 #22336
    device_list = list_ports.comports()
    for device in device_list:
        if device.vid == VID and device.pid == PID:
            return device.device
    return "device not found"
    #raise OSError("device not found")

#print(get_ports_names())

serial_port = serial.Serial()

port = getport()

serial_port.port = port
serial_port.baudrate = 115200

serial_port.open()
print(port)

time.sleep(1)
serial_port.write(b"1")

for x in range(10): 
    serial_port.write(b"1")

    print(serial_port.read(1))
print("loss")
serial_port.close()