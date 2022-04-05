import serial

ser = serial.Serial('COM3', 9600, timeout=1)
for i in range(100):
    line = ser.readline()
    print("{:016b}".format((int(line.decode('utf-8').strip("\r\n")))))
ser.close()
