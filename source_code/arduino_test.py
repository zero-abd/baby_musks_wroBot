import serial
import time

# test using direct arduino cable connected to jetson nano
ser = serial.Serial(port='/dev/ttyACM0', baudrate='9600', timeout=10)

for i in range(0, 111, 5):
    ser.write(bytes(chr(i), 'utf-8'))
    print(ser.readline())
    time.sleep(3)