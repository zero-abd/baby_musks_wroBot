from jetcam.csi_camera import CSICamera
from threading import Thread
from flask import Flask, Response
import time
import numpy as np
import cv2
import serial
import statistics


camera = CSICamera(width=272, height=204, capture_width=3280, capture_height=2464, capture_fps=21)
currentImage = [[[]]]


# get all the required images for wall edges and green and red traffic signals
def split_image(current_frame):
    red_min = (0, 35, 75)
    red_max = (5, 255, 255)
    red_min2 = ((180-red_max[0]), 35, 75)
    red_max2 = (180, 255, 255)
    green_min = (70, 25, 25)
    green_max = (90, 255, 255)
    # turn color format to hsv
    hsv = cv2.cvtColor(current_frame, cv2.COLOR_BGR2HSV)
        
    # red mask
    red_mask1 = cv2.inRange(hsv, red_min, red_max)
    red_mask2 = cv2.inRange(hsv, red_min2, red_max2)
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)
    red_mask = cv2.medianBlur(red_mask, 5)
        
    # green mask
    green_mask = cv2.inRange(hsv, green_min, green_max)
    green_mask = cv2.medianBlur(green_mask, 5)
        
    # wall edges
    gray_image = cv2.cvtColor(current_frame, cv2.COLOR_RGB2GRAY)
    blur_image = cv2.GaussianBlur(gray_image, (3,3),0)
    wall_line = cv2.Canny(blur_image, 100, 125, 3)
        
    return wall_line, green_mask, red_mask
    

# create traffic signals blob to get area and coordinates
def create_blob():
    parameter = cv2.SimpleBlobDetector_Params()
    parameter.filterByArea = True
    parameter.minArea = 50
    return cv2.SimpleBlobDetector_create(parameter)        


def wall_split(wall_vimage):
    wall_heights_np = (wall_vimage != 0).argmax(axis=1)
    wall_heights1 = [wall_heights_np[i:i+34] for i in range(0, 272, 34)]

    wall_slopes = [sum(np.diff(heights)) / len(heights) for heights in wall_heights1]
    wall_heights = [sum(heights) / len(heights) for heights in wall_heights1]

    wall_type = [0] * 8
    sp = False
    for i in range(6, 2, -1):
        if sp or wall_heights[i] - wall_heights[i+1] > 4:
            wall_type[i] = 1
            sp = True

    sp = False
    for i in range(2, 6):
        if sp or wall_heights[i+1] - wall_heights[i] > 4:
            wall_type[i+1] = 2
            sp = True

    for i in range(7):
        if wall_type[i] == 1 and wall_type[i + 1] == 2:
            wall_type[i] = wall_type[i + 1] = 0

    wall_type[0] = wall_type[1] = 1
    wall_type[6] = wall_type[7] = 2

    return wall_type, wall_heights


# calculating walls turn
def get_wall_turn(walls, heights, cl):
    turn = 0
    cturn = 0

    for i, section in enumerate(walls):
        print(f'no: {i}, section: {section}, height: {heights[i]}')
        print()
        tmp_turn = 10

        if section == 1:
            tmp_turn -= 0
            tmp_turn += 3.5 * abs(4 - i) if i <= 3 else 0
            tmp_turn += ((heights[i] - 12) ** 2)
        elif section == 2:
            tmp_turn -= 20
            tmp_turn -= 3.5 * abs(i - 3) if i >= 4 else 0
            tmp_turn -= ((heights[i] - 12) ** 2)
        elif section == 0:
            cturn += (30 + (heights[i] - 5) ** 2) * cl
        turn += tmp_turn

    if abs(turn) < abs(cturn):
        turn += cturn
    return turn


# calculating traffic signal turn
def get_traffic_turn(redp, greenp):
    target = [0, None]
    threshold = 50

    for points, index in [(redp, 1), (greenp, 2)]:
        for point in points:
            if point.pt[0] > threshold:
                if target[1] is None or target[1].size < point.size:
                    target = [index, point]

    if target[0] == 0:
        return 0

    result = max((((target[1].size / 10) ** 4) * (target[1].pt[0] * 0.1) - 50), 0)
    return (result * (1 if target[0] == 1 else -1))


clockwise = 1
traffic_past = 0

def calculate(current_frame):
    try:
        wall_line, green_image, red_image = split_image(current_frame)
        detector = create_blob()    
        
        global clockwise, traffic_past
        traffic_turn = 0
        wall_turn = 0
        final_turn = 0

        # crop images for traffic signs and walls
        red_image = cv2.copyMakeBorder(red_image[79:100],1,1,1,1, cv2.BORDER_CONSTANT)
        green_image = cv2.copyMakeBorder(green_image[79:100],1,1,1,1, cv2.BORDER_CONSTANT)

        wall_image = np.concatenate((wall_line[79:130], np.full((2,272),1)), axis=0)
        wall_vimage = np.swapaxes(wall_image,0,1)
        
       
        # center - 0, left - 1, right - 2
        walls, heights = wall_split(wall_vimage)
        wall_turn = get_wall_turn(walls, heights, clockwise)
        if wall_turn > 1000: wall_turn = 1000
        if wall_turn < -1000: wall_turn = -1000

        red_detections = []
        green_detections = []
        detector.empty()
        red_detections = detector.detect(255 - red_image)
        detector.empty()
        green_detections = detector.detect(255 - green_image)

        traffic_turn = get_traffic_turn(red_detections, green_detections)
        if traffic_turn > 500: traffic_turn = 500
        if traffic_turn < -500: traffic_turn = -500
        
        traffic_past *= 0.9
        traffic_turn += traffic_past * 0.9
        if abs(traffic_past) < 100:
            traffic_past = traffic_turn
        

        final_turn = wall_turn + traffic_turn
        return final_turn, wall_image 
    
    except Exception as e:
        print(e)
        return 0, None


def camera_start():
    camera.running = True
    def cap():
        try:
            global camera, currentImage
            while True:
                start = time.time()
                currentImage = camera.value
                time.sleep(max(0.01-(time.time()-start), 0))
        except Exception as err:
            print(err)
    cam_th = Thread(target = cap)
    cam_th.start()

        
def read():
    global currentImage
    out_image = cv2.rotate(currentImage, cv2.ROTATE_180)
    return out_image


def run_debug():
    while True:
        frame = read()
        wall_line, green_mask, red_mask = split_image(frame)
        debug_frame = (cv2.merge((wall_line, green_mask, red_mask)))
        turn, _frame = calculate(frame)
        mapped_turn = int(np.interp(turn, [-1000, 1000], [0, 110]))

        ser.write(bytes(chr(mapped_turn), 'utf-8'))
        print(turn)
        try:
            ret, buffer = cv2.imencode('.jpg', debug_frame)
            debug_frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + debug_frame + b'\r\n')
        except Exception as e:
            print(e)

def run():
    while True:
        frame = read()
        split_frame = split_image(frame)
        turn, debug_frame = calculate(frame)
        mapped_turn = int(np.interp(turn, [-1200, 1200], [0, 110]))
        
        ser.write(bytes(chr(mapped_turn), 'utf-8'))
        print(turn)

app = Flask(__name__)
@app.route('/')
def index():
    return Response(run_debug(), mimetype='multipart/x-mixed-replace; boundary=frame')



if __name__ == '__main__':
    ser = serial.Serial(port='/dev/ttyUSB0', baudrate='9600', timeout=10)
    camera_start()

    # run()
    app.run(host='0.0.0.0', port=5000)
