from flask import Flask, render_template, request, Response, jsonify
import cv2
import numpy as np
import json
import base64
import time
import threading
from datetime import datetime
import atexit

# Import our custom modules
from .ultrasonic import UltrasonicSensor
from .color import ColorDetector
from .led import LEDController
from .data import DataLogger
from .camera import CameraHandler

app = Flask(__name__)

# Global system components
sensor = None
led_controller = None
logger = None
camera_handler = None
color_detector = None

# System state
system_initialized = False
detection_active = False
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
            'red': 12,      # Red color detection
            'green': 16,    # Green color detection  
            'blue': 20,     # Brown color detection (using blue LED)
            'status': 21    # System status
        }
        led_controller = LEDController(led_pins)
        
        # Initialize color detector
        color_detector = ColorDetector()
        
        # Initialize camera handler
        camera_handler = CameraHandler(camera_index=0, resolution=(640, 480))
        
        # Set up camera callbacks
        camera_handler.set_detection_callback(handle_color_detection)
        
        # Start camera capture
        if camera_handler.start_capture():
            logger.log_system_event('info', 'Camera capture started successfully')
        else:
            logger.log_system_event('error', 'Failed to start camera capture')
        
        # Test LEDs
        led_controller.test_all_leds(0.3)
        led_controller.set_system_status('ready')
        
        system_initialized = True
        logger.log_system_event('startup', 'System initialization completed successfully')
        print("✓ Rover system initialization complete!")
        
    except Exception as e:
        logger.log_system_event('error', f'System initialization failed: {str(e)}') if logger else None
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
        
        # Log the detection
        logger.log_color_detection(color, material, confidence, True)
        
        # Control LEDs based on detection
        led_controller.handle_color_detection(color, confidence)
        led_controller.set_system_status('detecting')
        
        print(f"🎯 {color.upper()} detected: {material} ({confidence:.1f}%)")
    else:
        led_controller.set_system_status('scanning')

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
                
                time.sleep(2)  # Update every 2 seconds
        except Exception as e:
            logger.log_system_event('error', f'Sensor monitoring error: {str(e)}')
            time.sleep(5)

# Routes
@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/send-video')
def send_video():
    """Video feed page with detection overlay"""
    return render_template('send_video.html')

@app.route('/video_feed')
def video_feed():
    """Video stream endpoint"""
    def generate():
        while True:
            if camera_handler:
                frame_bytes = camera_handler.get_frame_as_jpeg()
                if frame_bytes:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                else:
                    # Placeholder frame
                    placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(placeholder, 'Camera Not Available', (200, 240),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    ret, buffer = cv2.imencode('.jpg', placeholder)
                    if ret:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.1)
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/system_status')
def api_system_status():
    """Get comprehensive system status"""
    global current_detection, current_distance
    
    status = {
        'system_initialized': system_initialized,
        'timestamp': datetime.now().isoformat(),
        'detection': current_detection,
        'distance_cm': current_distance,
        'sensor_status': sensor.get_status() if sensor else {'initialized': False},
        'led_status': led_controller.get_status() if led_controller else {'initialized': False},
        'camera_status': camera_handler.get_camera_info() if camera_handler else {'camera_available': False}
    }
    
    return jsonify(status)

@app.route('/api/distance')
def api_distance():
    """Get current distance reading"""
    try:
        if sensor:
            distance = sensor.measure_distance()
            return jsonify({
                'distance_cm': distance,
                'object_detected': distance <= sensor.detection_distance if distance else False,
                'detection_range_cm': sensor.detection_distance
            })
        else:
            return jsonify({'error': 'Sensor not initialized'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/detection')
def api_detection():
    """Get current color detection results"""
    global current_detection
    return jsonify(current_detection)

@app.route('/api/mine', methods=['POST'])
def api_mine():
    """Trigger mining action"""
    global current_detection, current_distance, logger
    
    try:
        if not current_detection['detected']:
            return jsonify({
                'status': 'no_target',
                'message': 'No target detected for mining'
            })
        
        if current_distance is None or current_distance > sensor.detection_distance:
            return jsonify({
                'status': 'too_far',
                'message': f'Target too far. Distance: {current_distance}cm, Max: {sensor.detection_distance}cm'
            })
        
        # Successful mining action
        color = current_detection['color']
        material = current_detection['material']
        confidence = current_detection['confidence']
        
        # Log mining action
        logger.log_mining_action(current_distance, color, material, confidence, True)
        
        # LED feedback for successful mining
        led_controller.blink('status', 0.1, 2.0)  # Fast blink for 2 seconds
        
        return jsonify({
            'status': 'mining_success',
            'material': material,
            'color': color,
            'confidence': confidence,
            'distance': current_distance,
            'message': f'Successfully mined {material}!'
        })
        
    except Exception as e:
        logger.log_system_event('error', f'Mining action failed: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def api_logs():
    """Get system logs"""
    try:
        log_type = request.args.get('type')
        limit = request.args.get('limit', type=int)
        
        logs = logger.get_logs(log_type, limit) if logger else []
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/recent')
def api_recent_logs():
    """Get recent logs"""
    try:
        minutes = request.args.get('minutes', 60, type=int)
        logs = logger.get_recent_logs(minutes) if logger else []
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/stats')
def api_log_stats():
    """Get logging statistics"""
    try:
        stats = logger.get_statistics() if logger else {}
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/led/<led_name>/<action>', methods=['POST'])
def api_led_control(led_name, action):
    """Control individual LEDs"""
    try:
        if not led_controller:
            return jsonify({'error': 'LED controller not initialized'}), 500
        
        result = False
        if action == 'on':
            result = led_controller.turn_on(led_name)
        elif action == 'off':
            result = led_controller.turn_off(led_name)
        elif action == 'toggle':
            result = led_controller.toggle(led_name)
        elif action == 'blink':
            interval = request.json.get('interval', 0.5) if request.json else 0.5
            duration = request.json.get('duration') if request.json else None
            led_controller.blink(led_name, interval, duration)
            result = True
        
        if result:
            logger.log_led_event(led_name, action)
            return jsonify({'status': 'success', 'led': led_name, 'action': action})
        else:
            return jsonify({'error': f'Failed to {action} LED {led_name}'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/camera/capture')
def api_capture_frame():
    """Capture and save current frame"""
    try:
        if not camera_handler:
            return jsonify({'error': 'Camera not initialized'}), 500
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'capture_{timestamp}.jpg'
        
        if camera_handler.save_frame(filename):
            logger.log_system_event('info', f'Frame captured: {filename}')
            return jsonify({'status': 'success', 'filename': filename})
        else:
            return jsonify({'error': 'Failed to capture frame'}), 500
            
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
    
    if logger:
        logger.log_system_event('shutdown', 'System shutdown completed')
    
    print("System cleanup completed")

# Register cleanup function
atexit.register(cleanup_system)

if __name__ == '__main__':
    # Initialize system
    initialize_system()
    
    # Start sensor monitoring thread
    if system_initialized:
        sensor_thread = threading.Thread(target=sensor_monitor_thread, daemon=True)
        sensor_thread.start()
    
    # Create templates directory if it doesn't exist
    import os
    os.makedirs('templates', exist_ok=True)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)  # Set debug=False for production
    except KeyboardInterrupt:
        print("\nShutting down...")
        cleanup_system()