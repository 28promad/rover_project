from camera import CameraHandler
from color import ColorDetector
from led import LEDController
from ultrasonic import UltrasonicSensor
import cv2
import time

def test_leds():
    """Test LED functionality"""
    print("\n=== Testing LEDs ===")
    led_pins = {
        'red': 12,
        'green': 16
    }
    
    led_controller = LEDController(led_pins)
    
    # Test individual LEDs
    print("Testing individual LEDs...")
    for led_name in led_pins.keys():
        print(f"Testing {led_name} LED - ON")
        led_controller.turn_on(led_name)
        time.sleep(1)
        print(f"Testing {led_name} LED - OFF")
        led_controller.turn_off(led_name)
        time.sleep(0.5)
    
    # Test blinking
    print("\nTesting LED blinking...")
    led_controller.blink('red', interval=0.2, duration=2)
    time.sleep(2.5)
    led_controller.blink('green', interval=0.2, duration=2)
    time.sleep(2.5)
    
    return led_controller

def test_ultrasonic():
    """Test ultrasonic sensor"""
    print("\n=== Testing Ultrasonic Sensor ===")
    sensor = UltrasonicSensor(trig_pin=18, echo_pin=24, detection_distance=50)
    
    print("Taking 5 distance measurements...")
    for i in range(5):
        distance = sensor.measure_distance()
        print(f"Measurement {i+1}: {distance} cm")
        time.sleep(0.5)
    
    return sensor

def test_camera_detection():
    """Test camera and color detection"""
    print("\n=== Testing Camera and Color Detection ===")
    
    try:
        # Initialize with RPi camera
        print("Initializing RPi camera...")
        camera = CameraHandler(camera_index="picam", resolution=(640, 480))
        detector = ColorDetector()
        
        def detection_callback(result):
            if result['detected']:
                print(f"🎯 Detection: {result['material']}")
                print(f"   Color: {result['color']}")
                print(f"   Confidence: {result['confidence']:.1f}%")
        
        camera.set_detection_callback(detection_callback)
        if not camera.start_capture():
            print("Failed to start camera capture!")
            return None
        
        print("\nCamera test running...")
        print("You should see a window with the camera feed")
        print("Show different materials to test detection")
        print("Press 'q' to quit\n")
        
        # Create named window
        cv2.namedWindow('Camera Test', cv2.WINDOW_NORMAL)
        
        while True:
            frame = camera.get_frame()
            if frame is not None:
                cv2.imshow('Camera Test', frame)
                print("Frame captured", end='\r')
            else:
                print("No frame available", end='\r')
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            
            time.sleep(0.1)
            
    except Exception as e:
        print(f"\nCamera test error: {e}")
        return None
    finally:
        if 'camera' in locals():
            camera.cleanup()
        cv2.destroyAllWindows()
        
    return camera

def run_all_tests():
    """Run all hardware component tests"""
    try:
        # Initialize components
        led_controller = test_leds()
        sensor = test_ultrasonic()
        camera = test_camera_detection()
        
        # Cleanup
        print("\n=== Cleaning Up ===")
        if led_controller:
            led_controller.cleanup()
        if sensor:
            sensor.cleanup()
        if camera:
            camera.cleanup()
            
        print("\n✅ Hardware tests completed!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        
if __name__ == "__main__":
    run_all_tests()