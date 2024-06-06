import RPi.GPIO as GPIO   
GPIO.setmode(GPIO.BCM)  # choose BCM numbering scheme.  

red_pin = 26
green_pin = 19
blue_pin = 13
  
GPIO.setup(red_pin, GPIO.OUT)# set GPIO 17 as output for white led  
GPIO.setup(green_pin, GPIO.OUT)# set GPIO 27 as output for red led  
GPIO.setup(blue_pin, GPIO.OUT)# set GPIO 22 as output for red led
  
hz = int(input('Please define the frequency in Herz(recommended:75): '))
reddc = int(input('Please define the red LED Duty Cycle: '))
greendc = int(input('Please define the green LED Duty Cycle: '))
bluedc = int(input('Please define the blue LED Duty Cycle: '))

red = GPIO.PWM(red_pin, hz)    # create object red for PWM on port 17  
green = GPIO.PWM(green_pin, hz)      # create object green for PWM on port 27   
blue = GPIO.PWM(blue_pin, hz)      # create object blue for PWM on port 22 

try:   
    while True:
        red.start((reddc/2.55))   #start red led
        green.start((greendc/2.55)) #start green led
        blue.start((bluedc/2.55))  #start blue led
 
except KeyboardInterrupt:
        red.stop()   #stop red led
        green.stop() #stop green led
        blue.stop()  #stop blue led
  
        GPIO.cleanup()          # clean up GPIO on CTRL+C exit