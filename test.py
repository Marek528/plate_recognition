import RPi.GPIO as GPIO
import time

ir_pin = 17
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(ir_pin, GPIO.IN)

while True:
    if GPIO.input(ir_pin) == GPIO.LOW:
        print('je tu auto')
        time.sleep(0.1)
    else:
        print('neni tu nic')
        time.sleep(0.1)
    