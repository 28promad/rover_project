from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
import threading
import time
from ultrasonic_sensor import UltrasonicSensor

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Globals
current_frame = None
detection_results = {}
distance_cm = None

# Initialize ultrasonic sensor
sensor = UltrasonicSensor(trig_pin=18, echo_pin=24, detection_distance=20)

# --- Color Detection (as before, but function returns best match) ---
COLOR_RANGES = {
    'red': [
        {'lower': np.array([0, 70, 50]), 'upper': np.array([10, 255, 255])},
        {'lower': np.array([170, 70, 50]), 'upper': np.array([180, 255, 255])}
    ],
    'brown': [
        {'lower': np.array([10, 100, 20]), 'upper': np.array([20, 255, 200])},
        {'lower': np.array([10, 50, 20]), 'upper': np.array([30, 255, 200])}
    ],
    'green': [
        {'lower': np.array([35, 40, 40]), 'upper': np.array([85, 255, 255])}
    ]
}
COLOR_TO_MATERIAL = {'red': 'palladium', 'brown': 'dirt', 'green': 'copper'}

def detect_colored_objects(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    best_match = {'detected': False, 'material': None, 'confidence': 0, 'color': None}
    for color_name, ranges in COLOR_RANGES.items():
        mask = None
        for r in ranges:
            current_mask = cv2.inRange(hsv, r['lower'], r['upper'])
            mask = current_mask if mask is None else cv2.bitwise_or(mask, current_mask)
        confidence = cv2.countNonZero(mask)
        if confidence > best_match['confidence'] and confidence > 100:
            best_match = {
                'detected': True,
                'material': COLOR_TO_MATERIAL[color_name],
                'confidence': int(confidence),
                'color': color_name
            }
    return best_match

# --- Background thread for distance updates ---
def distance_thread():
    global distance_cm
    while True:
        try:
            distance_cm = sensor.measure_distance()
            socketio.emit('distance_update', {'distance_cm': distance_cm})
        except Exception as e:
            socketio.emit('distance_update', {'distance_cm': None, 'error': str(e)})
        time.sleep(1)

threading.Thread(target=distance_thread, daemon=True).start()

# --- WebSocket Events ---
@socketio.on('video_frame')
def handle_video_frame(data):
    global current_frame, detection_results
    # data['frame'] is a base64 JPEG string
    img_data = base64.b64decode(data['frame'].split(',')[1])
    nparr = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    frame = cv2.resize(frame, (320, 240))
    current_frame = frame
    detection_results = detect_colored_objects(frame)
    # Broadcast detection results to all clients
    socketio.emit('detection_update', detection_results)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/manage')
def manage():
    return render_template('manage.html')

@app.route('/send-video')
def send_video():
    return render_template('send_video.html')

@app.route('/logs')
def logs():
    # Implement as before, or use SocketIO for real-time log updates
    return render_template('logs.html')

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000)