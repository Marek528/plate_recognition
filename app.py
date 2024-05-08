import numpy as np
from PIL import Image
from ultralytics import YOLO
import cv2
import easyocr
import csv
from util import write_csv, update_table
import uuid
import os
import av
import time
# settings for button
import RPi.GPIO as GPIO
ir_pin = 17
ir_pin_2 = 27
BUTTON_PIN = 22

# treba nacitat z db
free_places = 8

# GPIO.setwarnings(False)
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(ir_pin, GPIO.IN)
# GPIO.setup(ir_pin_2, GPIO.IN)

servo_pin = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(servo_pin, GPIO.OUT)
servo1 = GPIO.PWM(servo_pin, 50)
#nastavi ho na 0
servo1.start(7)

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

obrazok_test = "spz.jpg"
obrazok = "img.jpg"

while True:
    f = open('csv_detections/detection_results.csv', "w+")
    f.close()
    
    if GPIO.input(BUTTON_PIN) != GPIO.HIGH:
        os.system(f'fswebcam -r 640x480 test_imgs/{obrazok}')
        img = np.array(Image.open(f"test_imgs/{obrazok}"))
        results = model_prediction(img)
        if len(results) == 1:
            print('plate not detected')
            continue
        else:
            if results[-1] == 0:
                print('Car was not detected')
                continue
            file = open('csv_detections/detection_results.csv')
            csv_reader = csv.reader(file)
            csv_data = list(csv_reader)
            license_plate_text = csv_data[1][5]
            license_plate_score = csv_data[1][6]
            print(license_plate_text, license_plate_score)

            while GPIO.input(ir_pin) == GPIO.HIGH:
                time.sleep(0.5)
                continue
            
            #skontrolovat kolko je volnych miest na parkovisku
            if free_places > 0:
                # 1. otvori rampu (cez servo)
                print('brana sa otvorila')
                servo1.ChangeDutyCycle(2+(180/18))
                # 2. kontrola ci presiel za druhy senzor
                if sensor_detect():
                    print('zapise sa do db')
                    free_places -= 1
                    print('brana sa zatvara')
                    servo1.ChangeDutyCycle(2+(90/18))
                else:
                    print('rozhodol sa odist')
            else:
                print('parkovisko je plne')


            while (GPIO.input(BUTTON_PIN) == GPIO.LOW):
                print('pustito !')
            time.sleep(0.5)