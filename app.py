import numpy as np
from PIL import Image
from ultralytics import YOLO
import cv2
import easyocr
import csv
from led import change_color
from util import check_allowed_car, get_mode_db, write_csv, update_table, check_spz, free_places_db
import uuid
import os
import av
import time
# settings for button
import RPi.GPIO as GPIO
ir_pin = 17
ir_pin_2 = 27
# BUTTON_PIN = 22

# treba nacitat z db
free_places = 10

parking_house_id = 1

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
# GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ir_pin, GPIO.IN)
GPIO.setup(ir_pin_2, GPIO.IN)

# brana setup
servo_pin = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(servo_pin, GPIO.OUT)
servo1 = GPIO.PWM(servo_pin, 50)
#nastavi ho na 0
servo1.start(7)
time.sleep(0.5)
servo1.ChangeDutyCycle(0)

folder_path = "./licenses_plates_imgs_detected/"
LICENSE_MODEL_DETECTION_DIR = './models/license_plate_detector.pt'
COCO_MODEL_DIR = "./models/yolov8n.pt"

reader = easyocr.Reader(['en'], gpu=False)

vehicles = [2]

coco_model = YOLO(COCO_MODEL_DIR)
license_plate_detector = YOLO(LICENSE_MODEL_DETECTION_DIR)
print('ready')

def read_license_plate(license_plate_crop, img):
    scores = 0
    detections = reader.readtext(license_plate_crop)

    width = img.shape[1]
    height = img.shape[0]
    
    if detections == [] :
        return None, None

    rectangle_size = license_plate_crop.shape[0]*license_plate_crop.shape[1]

    plate = [] 

    for result in detections:
        length = np.sum(np.subtract(result[0][1], result[0][0]))
        height = np.sum(np.subtract(result[0][2], result[0][1]))
        
        if length*height / rectangle_size > 0.17:
            bbox, text, score = result
            text = result[1]
            text = text.upper()
            scores += score
            plate.append(text)
    
    if len(plate) != 0 : 
        return " ".join(plate), scores/len(plate)
    else :
        return " ".join(plate), 0

def model_prediction(img):
    license_numbers = 0
    results = {}
    licenses_texts = []
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    object_detections = coco_model(img)[0]
    license_detections = license_plate_detector(img)[0]

    if len(object_detections.boxes.cls.tolist()) != 0 :
        for detection in object_detections.boxes.data.tolist() :
            xcar1, ycar1, xcar2, ycar2, car_score, class_id = detection

            if int(class_id) in vehicles :
                cv2.rectangle(img, (int(xcar1), int(ycar1)), (int(xcar2), int(ycar2)), (0, 0, 255), 3)
    else :
            xcar1, ycar1, xcar2, ycar2 = 0, 0, 0, 0
            car_score = 0

    if len(license_detections.boxes.cls.tolist()) != 0 :
        license_plate_crops_total = []
        for license_plate in license_detections.boxes.data.tolist() :
            x1, y1, x2, y2, score, class_id = license_plate

            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 3)

            license_plate_crop = img[int(y1):int(y2), int(x1): int(x2), :]

            img_name = '{}.jpg'.format(uuid.uuid1())
         
            cv2.imwrite(os.path.join(folder_path, img_name), license_plate_crop)

            license_plate_crop_gray = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY) 

            license_plate_text, license_plate_text_score = read_license_plate(license_plate_crop_gray, img)

            licenses_texts.append(license_plate_text)

            if license_plate_text is not None and license_plate_text_score is not None  :
                license_plate_crops_total.append(license_plate_crop)
                results[license_numbers] = {}
                
                results[license_numbers][license_numbers] = {'car': {'bbox': [xcar1, ycar1, xcar2, ycar2], 'car_score': car_score},
                                                        'license_plate': {'bbox': [x1, y1, x2, y2],
                                                                            'text': license_plate_text,
                                                                            'bbox_score': score,
                                                                            'text_score': license_plate_text_score}} 
                license_numbers+=1
          
        write_csv(results, f"./csv_detections/detection_results.csv")

        img_wth_box = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
        return [img_wth_box, licenses_texts, license_plate_crops_total, car_score]
    
    else: 
        img_wth_box = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return [img_wth_box]

def sensor_detect():
    while GPIO.input(ir_pin) == GPIO.LOW:
        time.sleep(0.1)

    if GPIO.input(ir_pin_2) == GPIO.LOW:
        while GPIO.input(ir_pin_2) == GPIO.LOW:
            time.sleep(0.1)
        if GPIO.input(ir_pin) == GPIO.LOW:
            print('odisiel')
            return False
        print('presiel cez zavoru')
        return True
    else:
        print('odisiel skor')
        return False

def servo_motor(angle):
    servo1.ChangeDutyCycle(2+(angle/18))
    time.sleep(0.5)
    servo1.ChangeDutyCycle(0)

def odfot(obrazok):
    os.system(f'fswebcam -r 640x480 test_imgs/{obrazok}')
    return

obrazok_test = "spz.jpg"
obrazok = "img.jpg"
pocitadlo = 0

while True:
    f = open('csv_detections/detection_results.csv', "w+")
    f.close()
    
    mod = 1
    mod = get_mode_db()

    #prichod ku senzoru
    # orange led
    change_color(1)
    if GPIO.input(ir_pin) != GPIO.HIGH:

        if mod == 1:
            #mod - otvorena pre vsetkych pokial je volne miesto
            #blue led
            change_color(2)
            free_places = free_places_db()
            if free_places > 0:
                #white led
                change_color(3)
                time.sleep(0.3)
                odfot(obrazok)
                img = np.array(Image.open(f"test_imgs/{obrazok}"))
                results = model_prediction(img)
                if len(results) == 1:
                    change_color(2)
                    #blue led
                    print('plate not detected')
                    continue
                else:
                    if results[-1] == 0:
                        change_color(2)
                        #blue led
                        print('Car was not detected')
                        continue
                    file = open('csv_detections/detection_results.csv')
                    csv_reader = csv.reader(file)
                    csv_data = list(csv_reader)
                    try:
                        license_plate_text = csv_data[1][5]
                        license_plate_text.replace(" ", "")
                    except:
                        change_color(2)
                        #blue led
                        print('Nevie precitat znacku')
                        continue
                    license_plate_score = csv_data[1][6]
                    print(license_plate_text, license_plate_score)

                    #kontrola pri nedokonalosti senzora alebo sa rozhodol odist zatial co sa robilo OCR
                    while GPIO.input(ir_pin) == GPIO.HIGH:
                        time.sleep(0.5)
                        pocitadlo += 1
                        if pocitadlo >= 10:
                            break
                        continue

                    # if check_spz(license_plate_text) != '':
                    #     print('SPZ uz je zaevidovana (zrejme kvoli vypadku elektriny)')
                        
                    if pocitadlo < 10 and free_places > 0:
                        # 1. otvori rampu (cez servo)
                        #green led
                        change_color(4)
                        print("farba zelena")
                        print('brana sa otvorila')
                        servo_motor(180)
                        # 2. kontrola ci presiel za druhy senzor
                        if sensor_detect():
                            
                            print('brana sa zatvara')
                            #red led
                            change_color(5)
                            time.sleep(0.8)
                            servo_motor(90)
                            print('zapise sa do db')
                            update_table(f"INSERT INTO parked_cars (spz, created_at, updated_at, parking_house_id) VALUES ('{license_plate_text}', now(), now(), '{parking_house_id}')")
                            free_places -= 1
                        else:
                            #red led
                            change_color(5)
                            print('rozhodol sa odist')
                            servo_motor(90)

                    else:
                        pocitadlo = 0
                        print('odisiel')
                    
                    pocitadlo = 0


                    while (GPIO.input(ir_pin) == GPIO.LOW):
                        # red led
                        change_color(5)
                        print('pustito !')
                    time.sleep(0.5)
            else:
                #red led
                change_color(5)
                print('parkovisko je plne')
                time.sleep(0.5)
        
        elif mod == 2:
            #mod 2 - otvara sa len pre povolene auta pokial nie je plne
            #blue led
            change_color(2)
            free_places = free_places_db()

            if free_places > 0:
                # white led
                change_color(3)
                time.sleep(0.3)
                odfot(obrazok)
                img = np.array(Image.open(f"test_imgs/{obrazok}"))
                results = model_prediction(img)
                if len(results) == 1:
                    change_color(2)
                    #blue led
                    print('plate not detected')
                    continue
                else:
                    if results[-1] == 0:
                        change_color(2)
                        #blue led
                        print('Car was not detected')
                        continue
                    file = open('csv_detections/detection_results.csv')
                    csv_reader = csv.reader(file)
                    csv_data = list(csv_reader)
                    try:
                        license_plate_text = csv_data[1][5]
                        license_plate_text.replace(" ", "")
                    except:
                        change_color(2)
                        #blue led
                        print('Nevie precitat znacku')
                        continue
                    license_plate_score = csv_data[1][6]
                    print(license_plate_text, license_plate_score)

                    #kontrola pri nedokonalosti senzora alebo sa rozhodol odist zatial co sa robilo OCR
                    while GPIO.input(ir_pin) == GPIO.HIGH:
                        time.sleep(0.5)
                        pocitadlo += 1
                        if pocitadlo >= 10:
                            break
                        continue

                    # if check_spz(license_plate_text) != '':
                    #     print('SPZ uz je zaevidovana (zrejme kvoli vypadku elektriny)')
                        
                    #skontrolovat kolko je volnych miest na parkovisku a ci ma znacka povolene parkovanie
                    # free_places = free_places_db()


                    kontrola = check_allowed_car(license_plate_text)

                    if pocitadlo < 10 and free_places > 0 and kontrola:
                        # 1. otvori rampu (cez servo)
                        change_color(4)
                        # green led
                        print('brana sa otvorila')
                        servo_motor(180)
                        # 2. kontrola ci presiel za druhy senzor
                        if sensor_detect():
                            print('brana sa zatvara')
                            change_color(5)
                            time.sleep(0.8)
                            servo_motor(90)
                            print('zapise sa do db')
                            update_table(f"INSERT INTO parked_cars (spz, created_at, updated_at, parking_house_id) VALUES ('{license_plate_text}', now(), now(), '{parking_house_id}')")
                            free_places -= 1
                        else:
                            change_color(5)

                            print('rozhodol sa odist')
                            servo_motor(90)

                    else:
                        pocitadlo = 0
                        print('odisiel alebo nema povoleny prejazd')
                    
                    pocitadlo = 0


                    while (GPIO.input(ir_pin) == GPIO.LOW):
                        #red led
                        change_color(5)
                        print('pustito !')
                        time.sleep(0.5)
            else:
                change_color(5)
                #red led
                print('parkovisko je plne')
        
        elif mod == 3:
            #mod 3 - brana bude neustale otvorena
            change_color(4)
            servo_motor(180)
            if sensor_detect():
                pass
            print('brana sa zatvara')
            change_color(5)
            time.sleep(0.8)
            servo_motor(90)
            
        elif mod == 4:
            #mod 4 - brana bude neustale zatvorena
            change_color(5)
            servo_motor(90)