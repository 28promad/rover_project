import RPi.GPIO as GPIO
import time
import json
from datetime import datetime

class UltrasonicSensor:
    def __init__(self, trig_pin=18, echo_pin=24, detection_distance=20):
        """
        Initialize ultrasonic sensor
        
        Args:
            trig_pin: GPIO pin for trigger
            echo_pin: GPIO pin for echo
            detection_distance: Distance in cm to detect objects
        """
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin
        self.detection_distance = detection_distance
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trig_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        
        # Initialize trigger to low
        GPIO.output(self.trig_pin, False)
        time.sleep(0.1)
    
    def measure_distance(self):
        """
        Measure distance using ultrasonic sensor
        
        Returns:
            distance in cm
        """
        # Send 10us pulse to trigger
        GPIO.output(self.trig_pin, True)
        time.sleep(0.00001)
        GPIO.output(self.trig_pin, False)
        
        # Wait for echo to start
        pulse_start = time.time()
        while GPIO.input(self.echo_pin) == 0:
            pulse_start = time.time()
        
        # Wait for echo to end
        pulse_end = time.time()
        while GPIO.input(self.echo_pin) == 1:
            pulse_end = time.time()
        
        # Calculate distance
        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150  # Speed of sound = 34300 cm/s, divide by 2
        distance = int(distance)
        
        return distance
    
    def detect_object(self):
        """
        Check if object is within detection range
        
        Returns:
            tuple: (is_detected, distance)
        """
        distance = self.measure_distance()
        is_detected = distance <= self.detection_distance
        
        return is_detected, distance
    
    def log_detection(self, distance, detected=False, object_type=None):
        """
        Log detection data to JSON file
        
        Args:
            distance: measured distance
            detected: whether object was detected
            object_type: type of object if identified by camera
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "distance_cm": distance,
            "object_detected": detected,
            "object_type": object_type,
            "within_range": distance <= self.detection_distance
        }
        
        try:
            # Read existing log
            with open('log.json', 'r') as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []
        
        # Add new entry
        logs.append(log_entry)
        
        # Keep only last 100 entries to prevent file from growing too large
        logs = logs[-100:]
        
        # Write back to file
        with open('log.json', 'w') as f:
            json.dump(logs, f, indent=2)
    
    def continuous_monitoring(self, interval=1):
        """
        Continuously monitor for objects
        
        Args:
            interval: time between measurements in seconds
        """
        print(f"Starting continuous monitoring...")
        print(f"Detection range: {self.detection_distance}cm")
        
        try:
            while True:
                detected, distance = self.detect_object()
                
                if detected:
                    print(f"OBJECT DETECTED! Distance: {distance}cm")
                    self.log_detection(distance, detected=True)
                    # Here you would trigger camera capture/analysis
                    return True, distance
                else:
                    print(f"Clear path. Distance: {distance}cm")
                    self.log_detection(distance, detected=False)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
            return False, None
        finally:
            GPIO.cleanup()

# Example usage
if __name__ == "__main__":
    # Initialize sensor
    sensor = UltrasonicSensor(trig_pin=27, echo_pin=22, detection_distance=100)
    
    # Single measurement
    distance = sensor.measure_distance()
    print(f"Distance: {distance}cm")
    
    # Check for object detection
    detected, dist = sensor.detect_object()
    if detected:
        print(f"Object detected at {dist}cm!")
    else:
        print(f"No object detected. Distance: {dist}cm")
    
    # Start continuous monitoring
    sensor.continuous_monitoring(interval=0.5)xx
