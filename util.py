import easyocr
import base64
import streamlit as st
import mariadb

# Initialize the OCR reader
reader = easyocr.Reader(['en'], gpu=False)

# Mapping dictionaries for character conversion
dict_char_to_int = {'O': '0',
                    'I': '1',
                    'J': '3',
                    'A': '4',
                    'G': '6',
                    'S': '5'}

dict_int_to_char = {'0': 'O',
                    '1': 'I',
                    '3': 'J',
                    '4': 'A',
                    '6': 'G',
                    '5': 'S'}


def write_csv(results, output_path):
    """
    Write the results to a CSV file.

    Args:
        results (dict): Dictionary containing the results.
        output_path (str): Path to the output CSV file.
    """
    with open(output_path, 'w') as f:
        f.write('{},{},{},{},{},{},{}\n'.format('frame_nmr', 'car_id', 'car_bbox',
                                                'license_plate_bbox', 'license_plate_bbox_score', 'license_number',
                                                'license_number_score'))

        for frame_nmr in results.keys():
            for car_id in results[frame_nmr].keys():
                if 'car' in results[frame_nmr][car_id].keys() and \
                   'license_plate' in results[frame_nmr][car_id].keys() and \
                   'text' in results[frame_nmr][car_id]['license_plate'].keys():
                    f.write('{},{},{},{},{},{},{}\n'.format(frame_nmr,
                                                            car_id,
                                                            '[{} {} {} {}]'.format(
                                                                results[frame_nmr][car_id]['car']['bbox'][0],
                                                                results[frame_nmr][car_id]['car']['bbox'][1],
                                                                results[frame_nmr][car_id]['car']['bbox'][2],
                                                                results[frame_nmr][car_id]['car']['bbox'][3]),
                                                            '[{} {} {} {}]'.format(
                                                                results[frame_nmr][car_id]['license_plate']['bbox'][0],
                                                                results[frame_nmr][car_id]['license_plate']['bbox'][1],
                                                                results[frame_nmr][car_id]['license_plate']['bbox'][2],
                                                                results[frame_nmr][car_id]['license_plate']['bbox'][3]),
                                                            results[frame_nmr][car_id]['license_plate']['bbox_score'],
                                                            results[frame_nmr][car_id]['license_plate']['text'],
                                                            results[frame_nmr][car_id]['license_plate']['text_score'])
                            )
        f.close()

def read_license_plate(license_plate_crop):
    """
    Read the license plate text from the given cropped image.

    Args:
        license_plate_crop (PIL.Image.Image): Cropped image containing the license plate.

    Returns:
        tuple: Tuple containing the formatted license plate text and its confidence score.
    """

    detections = reader.readtext(license_plate_crop)

    if detections == [] :
        return None, None

    for detection in detections:
        bbox, text, score = detection

        #text = text.upper().replace(' ', '')
        text = text.upper()

        if text is not None and score is not None and bbox is not None and len(text) >= 6:
        #if license_complies_format(text):
        #    return format_license(text), score
            return text, score

    return None, None

def connect_db():
    """
    To db we can use SELECT, INSERT, DELETE commands
    """
    try:
        conn = mariadb.connect(
                user="zavora",
                password="zavora123",
                host="10.42.0.1",
                port=3306,
                database="parkovisko"
        )
    except mariadb.Error as e:
            print(f"Error: {e}")
            sys.exit(1)

def update_table(sql_query):
    global conn
    connect_db()

    cur = conn.cursor()
    cur.execute(sql_query)
    conn.commit()
    first_word = (sql_query.split())[0]
    if first_word == 'SELECT':
        return 0

def check_spz(license_plate_text):
    connect_db()
    
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM parked_cars WHERE spz={license_plate_text}')
    for spz in cur:
        if spz[1] == '':
            return ''
        return spz[1]

def free_places_db():
    connect_db()
    
    cur = conn.cursor()
    cur.execute('SELECT COUNT(occupied) FROM parking_slots WHERE occupied=0')
    for i in cur:
        if i[1] == '':
            return ''
        return i[1]