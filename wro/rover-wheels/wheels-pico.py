# filepath: /wheels-pico-project/wheels-pico-project/src/wheels-pico.py

import machine
import time

class Motor:
    def __init__(self, in1, in2, enable=None):
        self.in1 = machine.Pin(in1, machine.Pin.OUT)
        self.in2 = machine.Pin(in2, machine.Pin.OUT)
        self.pwm = None

        if enable is not None:
            self.enable = machine.Pin(enable, machine.Pin.OUT)
            self.pwm = machine.PWM(self.enable)
            self.pwm.freq(1000)
            self.pwm.duty(0)

    def forward(self, speed=1023):
        self.in1.value(1)
        self.in2.value(0)
        if self.pwm:
            self.pwm.duty(speed)

    def backward(self, speed=1023):
        self.in1.value(0)
        self.in2.value(1)
        if self.pwm:
            self.pwm.duty(speed)

    def stop(self):
        self.in1.value(0)
        self.in2.value(0)
        if self.pwm:
            self.pwm.duty(0)


class Vehicle:
    def __init__(self, dc_left, dc_right, tt_motor):
        self.dc_left = dc_left
        self.dc_right = dc_right
        self.tt_motor = tt_motor

    def move_forward(self, speed=1023):
        self.dc_left.forward(speed)
        self.dc_right.forward(speed)
        self.tt_motor.forward(speed)

    def move_backward(self, speed=1023):
        self.dc_left.backward(speed)
        self.dc_right.backward(speed)
        self.tt_motor.backward(speed)

    def turn_left(self, speed=1023):
        self.dc_left.backward(speed)
        self.dc_right.forward(speed)
        self.tt_motor.forward(speed)

    def turn_right(self, speed=1023):
        self.dc_left.forward(speed)
        self.dc_right.backward(speed)
        self.tt_motor.forward(speed)

    def stop(self):
        self.dc_left.stop()
        self.dc_right.stop()
        self.tt_motor.stop()