import RPi.GPIO as GPIO   
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  # choose BCM numbering scheme.  

red_pin = 13
green_pin = 19
blue_pin = 26
  
GPIO.setup(red_pin, GPIO.OUT)# set GPIO 17 as output for white led  
GPIO.setup(green_pin, GPIO.OUT)# set GPIO 27 as output for red led  
GPIO.setup(blue_pin, GPIO.OUT)# set GPIO 22 as output for red led

hz = 75

red = GPIO.PWM(red_pin, hz)    # create object red for PWM on port 17  
green = GPIO.PWM(green_pin, hz)      # create object green for PWM on port 27   
blue = GPIO.PWM(blue_pin, hz)      # create object blue for PWM on port 22 


def change_color(color):
    if color == 1:
        #cakaj (oranzova)
        reddc = 255
        greendc = 150
        bluedc = 0

    elif color == 2:
        #databaza (modra)
        reddc = 0
        greendc = 0
        bluedc = 255

    elif color == 3:
        #fotenie (biela)
        reddc = 255
        greendc = 255
        bluedc = 255

    elif color == 4:
        #otvorenie brany (zelena)
        reddc = 0
        greendc = 255
        bluedc = 0
    elif color == 5:
        #opustit priestor (cervena)
        reddc = 255
        greendc = 0
        bluedc = 0
    

    red.start((reddc/2.55))   #start red led
    green.start((greendc/2.55)) #start green led
    blue.start((bluedc/2.55))  #start blue led
    