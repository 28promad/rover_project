from flask import Flask, render_template, request, Response, jsonify
import cv2
import numpy as np
import json
import base64
from datetime import datetime
import threading
import time
from ultrasonic_sensor import UltrasonicSensor

app = Flask(__name__)

# Global variables for video stream
current_frame = None
video_available = False
detection_results = {}
use_pi_camera = False # Set to True if using Raspberry Pi camera
# Initialize the sensor (adjust pins as needed)
sensor = UltrasonicSensor()


@app.route('/api/distance')
def api_distance():
    try:
        distance = sensor.measure_distance()
        return jsonify({'distance_cm': distance})
    except Exception as e:
        return jsonify({'distance_cm': None, 'error': str(e)})

# Color detection ranges (HSV)
COLOR_RANGES = {
    'red': {
        'lower': np.array([0, 120, 70]),
        'upper': np.array([10, 255, 255]),
        'material': 'palladium'
    },
    'brown': {
        'lower': np.array([10, 50, 20]),
        'upper': np.array([20, 255, 200]),
        'material': 'dirt'
    },
    'green': {
        'lower': np.array([40, 40, 40]),
        'upper': np.array([80, 255, 255]),
        'material': 'copper'
    }
}

def detect_colored_objects(frame):
    """
    Detect colored objects in frame and return material type
    
    Args:
        frame: OpenCV frame
        
    Returns:
        dict: Detection results
    """
    if frame is None:
        return {'detected': False, 'material': None, 'confidence': 0}
    
    # Convert to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    best_match = {'detected': False, 'material': None, 'confidence': 0, 'color': None}
    
    for color_name, color_info in COLOR_RANGES.items():
        # Create mask
        mask = cv2.inRange(hsv, color_info['lower'], color_info['upper'])
        
        # Calculate percentage of pixels matching color
        total_pixels = mask.shape[0] * mask.shape[1]
        colored_pixels = cv2.countNonZero(mask)
        confidence = (colored_pixels / total_pixels) * 100
        
        # If this color has higher confidence and meets threshold
        if confidence > best_match['confidence'] and confidence > 5:  # 5% threshold
            best_match = {
                'detected': True,
                'material': color_info['material'],
                'confidence': round(confidence, 2),
                'color': color_name
            }
    
    return best_match

def log_mining_data(distance, material_detected, material_type=None, confidence=0):
    """
    Log mining data to JSON file
    
    Args:
        distance: Distance from ultrasonic sensor
        material_detected: Boolean if material was detected
        material_type: Type of material detected
        confidence: Confidence level of detection
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "distance_cm": distance,
        "material_detected": material_detected,
        "material_type": material_type,
        "confidence": confidence,
        "action": "mining" if material_detected else "scanning"
    }
    
    try:
        with open('log.json', 'r') as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []
    
    logs.append(log_entry)
    logs = logs[-100:]  # Keep last 100 entries
    
    with open('log.json', 'w') as f:
        json.dump(logs, f, indent=2)

@app.route('/')
def index():
    """
    Main page with rover controls
    """
    return render_template('index.html')
""" 
@app.route('/send-video', methods=['GET', 'POST'])
def send_video():
    global current_frame, video_available, detection_results
    if request.method == 'POST':
        data = request.get_json()
        if 'frame' in data:
            try:
                img_data = base64.b64decode(data['frame'].split(',')[1])
                nparr = np.frombuffer(img_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                # Resize to 320x240 for lower latency
                frame = cv2.resize(frame, (320, 240))
                current_frame = frame
                video_available = True
                detection_results = detect_colored_objects(frame)
                return jsonify({'status': 'success', 'detection': detection_results})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)})
    return render_template('send_video.html')

 """
# --- Pi Camera Thread ---
def pi_camera_stream():
    global current_frame, video_available, detection_results
    cap = cv2.VideoCapture(0)  # 0 is usually the Pi camera
    while use_pi_camera:
        ret, frame = cap.read()
        if ret:
            # Resize for lower latency
            frame = cv2.resize(frame, (320, 240))
            current_frame = frame
            video_available = True
            detection_results = detect_colored_objects(frame)
        time.sleep(0.05)  # ~20 FPS
    cap.release()

# Start Pi camera thread if enabled
if use_pi_camera:
    threading.Thread(target=pi_camera_stream, daemon=True).start()


@app.route('/video_feed')
def video_feed():
    def generate():
        global current_frame, video_available
        while True:
            if video_available and current_frame is not None:
                # Ensure playback is also 320x240
                frame = cv2.resize(current_frame, (320, 240))
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                placeholder = np.zeros((240, 320, 3), dtype=np.uint8)
                cv2.putText(placeholder, 'No Video Available', (30, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                ret, buffer = cv2.imencode('.jpg', placeholder)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.05)  # 20 FPS
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/logs')
def logs():
    """
    Display logs page
    """
    try:
        with open('log.json', 'r') as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []
    
    return render_template('logs.html', logs=logs)

@app.route('/manage')
def manage():
    """
    Management page with live feed and log data
    """
    try:
        with open('log.json', 'r') as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []
    
    return render_template('manage.html', logs=logs, video_available=video_available)

@app.route('/api/logs')
def api_logs():
    """
    API endpoint to get logs as JSON
    """
    try:
        with open('log.json', 'r') as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []
    
    return jsonify(logs)

@app.route('/api/detection')
def api_detection():
    """
    API endpoint to get current detection results
    """
    global detection_results
    return jsonify(detection_results)

@app.route('/api/mine', methods=['POST'])
def api_mine():
    """
    API endpoint to trigger mining action
    """
    global detection_results
    
    data = request.get_json()
    distance = data.get('distance', 0)
    
    if detection_results.get('detected', False):
        material_type = detection_results.get('material')
        confidence = detection_results.get('confidence', 0)
        
        log_mining_data(distance, True, material_type, confidence)
        
        return jsonify({
            'status': 'mining',
            'material': material_type,
            'confidence': confidence,
            'message': f'Mining {material_type} detected!'
        })
    else:
        log_mining_data(distance, False)
        return jsonify({
            'status': 'no_target',
            'message': 'No valuable material detected'
        })

if __name__ == '__main__':
    # Create templates directory structure if it doesn't exist
    import os
    os.makedirs('templates', exist_ok=True)
    
    app.run(host='0.0.0.0', port=5000, debug=True)