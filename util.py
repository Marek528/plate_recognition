import easyocr
import base64
import streamlit as st
import mariadb

parking_house_id = 1

znacky =['AUDI TT']

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

def connect_db():
    global conn
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
    cur.execute(f'SELECT * FROM parked_cars WHERE spz="{license_plate_text}"')
    for spz in cur:
        if spz[1] == '':
            return ''
        return spz[1]

def free_places_db():
    connect_db()
    
    cur = conn.cursor()
    cur.execute(f'SELECT COUNT(occupied) FROM parking_slots WHERE occupied=0')
    for i in cur:
        return i[0]


# ziskanie modu z databazy
def get_mode_db():
    connect_db()

    cur = conn.cursor()
    cur.execute(f'SELECT mode FROM parking_houses WHERE id="{parking_house_id}"')
    for i in cur:
        if i[0] == "allowed":
            return 2
        elif i[0] == "everyone":
            return 1
        elif i[0] == "open":
            return 3
        elif i[0] == "closed":
            return 4

def check_allowed_car(license_plate_text):
    global conn
    connect_db()
    
    cur = conn.cursor()
    cur.execute(f'SELECT COUNT(*) FROM allowed_cars WHERE spz="{license_plate_text}"')
    for i in cur:
        if int(i[0]) > 0:
            print('1')
            return 1
        else:
            print('0')
            return 0

def check_allowed_car_2(license_plate_text):
    if license_plate_text in znacky:
        print('1')
        return 1
    else:
        print('0')
        return 0