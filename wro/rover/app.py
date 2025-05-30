from flask import Flask, render_template, request, Response, jsonify
import cv2
import time
import threading
from datetime import datetime

# Import modular components
from camera import CameraHandler
from color import ColorDetector
from data import DataLogger
from led import LEDController
from ultrasonic import UltrasonicSensor

app = Flask(__name__)

# Global system components
sensor = None
led_controller = None
logger = None
camera_handler = None
color_detector = None

# System state
system_initialized = False
current_detection = {'detected': False, 'material': None, 'confidence': 0, 'color': None}
current_distance = None

def initialize_system():
    """Initialize all system components"""
    global sensor, led_controller, logger, camera_handler, color_detector, system_initialized
    
    try:
        # Initialize data logger
        logger = DataLogger('rover_log.json', max_entries=1000)
        logger.log_system_event('startup', 'System initialization started')
        
        # Initialize ultrasonic sensor
        sensor = UltrasonicSensor(trig_pin=18, echo_pin=24, detection_distance=50)
        
        # Initialize LED controller
        led_pins = {
            'red': 12,    # Red color detection
            'green': 16,  # Green color detection  
            'blue': 20,   # Brown color detection (using blue LED)
            'status': 21  # System status
        }
        led_controller = LEDController(led_pins)
        
        # Initialize color detector and camera
        color_detector = ColorDetector()
        camera_handler = CameraHandler(camera_index=0, resolution=(640, 480))
        camera_handler.set_detection_callback(handle_color_detection)
        
        # Start camera capture
        if camera_handler.start_capture():
            logger.log_system_event('info', 'Camera capture started')
        else:
            logger.log_system_event('error', 'Failed to start camera')
        
        # Test LEDs
        led_controller.test_all_leds(0.3)
        led_controller.set_system_status('ready')
        
        # Start sensor monitoring thread
        sensor_thread = threading.Thread(target=sensor_monitor_thread, daemon=True)
        sensor_thread.start()
        
        system_initialized = True
        logger.log_system_event('startup', 'System initialized successfully')
        print("✓ Rover system initialization complete!")
        
    except Exception as e:
        logger.log_system_event('error', f'System initialization failed: {str(e)}')
        print(f"✗ System initialization failed: {e}")
        system_initialized = False

def handle_color_detection(detection_result):
    """Handle color detection events"""
    global current_detection, led_controller, logger
    
    current_detection = detection_result
    if detection_result['detected']:
        color = detection_result['color']
        confidence = detection_result['confidence']
        material = detection_result['material']
        
        logger.log_color_detection(color, material, confidence, True)
        led_controller.handle_color_detection(color, confidence)
        print(f"🎯 {color.upper()} detected: {material} ({confidence:.1f}%)")

def sensor_monitor_thread():
    """Background thread to monitor ultrasonic sensor"""
    global current_distance, sensor, logger
    
    while system_initialized:
        try:
            if sensor:
                distance = sensor.measure_distance()
                if distance is not None:
                    current_distance = distance
                    detected = distance <= sensor.detection_distance
                    logger.log_sensor_data(distance, detected)
                time.sleep(0.5)  # Update every 500ms
        except Exception as e:
            logger.log_system_event('error', f'Sensor error: {str(e)}')
            time.sleep(5)

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video stream endpoint"""
    def generate():
        while True:
            if camera_handler:
                frame = camera_handler.get_frame_as_jpeg()
                if frame:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.1)
    
    return Response(generate(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/system_status')
def api_system_status():
    """Get system status"""
    return jsonify({
        'initialized': system_initialized,
        'distance': current_distance,
        'detection': current_detection,
        'camera_status': camera_handler.get_camera_info() if camera_handler else None
    })

@app.route('/api/led/<led_name>/<action>', methods=['POST'])
def api_led_control(led_name, action):
    """Control individual LEDs"""
    try:
        if not led_controller:
            return jsonify({'error': 'LED controller not initialized'}), 500
        
        success = False
        if action == 'on':
            success = led_controller.turn_on(led_name)
        elif action == 'off':
            success = led_controller.turn_off(led_name)
        elif action == 'blink':
            led_controller.blink(led_name, 0.5)
            success = True
            
        if success:
            logger.log_led_event(led_name, action)
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': f'Failed to {action} LED {led_name}'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def cleanup_system():
    """Clean up system resources"""
    global sensor, led_controller, camera_handler, logger
    
    print("Cleaning up system resources...")
    
    if logger:
        logger.log_system_event('shutdown', 'System shutdown initiated')
    
    if camera_handler:
        camera_handler.cleanup()
    
    if led_controller:
        led_controller.cleanup()
    
    if sensor:
        sensor.cleanup()
    
    print("System cleanup completed")

# Register cleanup handler
atexit.register(cleanup_system)

# Initialize system on startup
initialize_system()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)