# -*- coding: utf-8 -*-
# @Time : 25/03/2024 17:12
# @Author : Qingyu Zhang
# @Email : qingyu.zhang.23@ucl.ac.uk
# @Institution : UCL
# @FileName: u_serial_protocols.py
# @Software: PyCharm
# @Blog ：https://github.com/alfredzhang98


import serial
import time


def default_handler():
    raise Warning("Unknown cmd handler")


class SerialCommunication:
    def __init__(self, port, baud_rate):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = serial.Serial(port, baud_rate, timeout=100)

    def send_data(self, data):
        self.ser.write(data.encode())

    def receive_data(self):
        data = self.ser.readline().decode().strip()
        return data
