# for use with the ttdc motor with two wheels
# and two dc motors for the left and right wheels
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

class Motor:
    def __init__(self, in1, in2, enable=None, pwm_freq=1000):
        self.in1 = in1
        self.in2 = in2
        self.enable = enable
        self.pwm = None

        GPIO.setup(in1, GPIO.OUT)
        GPIO.setup(in2, GPIO.OUT)

        if enable:
            GPIO.setup(enable, GPIO.OUT)
            self.pwm = GPIO.PWM(enable, pwm_freq)
            self.pwm.start(0)

    def forward(self, speed=100):
        GPIO.output(self.in1, GPIO.HIGH)
        GPIO.output(self.in2, GPIO.LOW)
        if self.pwm:
            self.pwm.ChangeDutyCycle(speed)

    def backward(self, speed=100):
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.HIGH)
        if self.pwm:
            self.pwm.ChangeDutyCycle(speed)

    def stop(self):
        GPIO.output(self.in1, GPIO.LOW)
        GPIO.output(self.in2, GPIO.LOW)
        if self.pwm:
            self.pwm.ChangeDutyCycle(0)


class Vehicle:
    def __init__(self, dc_left, dc_right, tt_motor):
        self.dc_left = dc_left
        self.dc_right = dc_right
        self.tt_motor = tt_motor

    def move_forward(self, speed=100):
        self.dc_left.forward(speed)
        self.dc_right.forward(speed)
        self.tt_motor.forward(speed)

    def move_backward(self, speed=100):
        self.dc_left.backward(speed)
        self.dc_right.backward(speed)
        self.tt_motor.backward(speed)

    def turn_left(self, speed=100):
        self.dc_left.backward(speed)
        self.dc_right.forward(speed)
        self.tt_motor.forward(speed)

    def turn_right(self, speed=100):
        self.dc_left.forward(speed)
        self.dc_right.backward(speed)
        self.tt_motor.forward(speed)

    def stop(self):
        self.dc_left.stop()
        self.dc_right.stop()
        self.tt_motor.stop()