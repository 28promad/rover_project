import RPi.GPIO as GPIO
import time
import json
from datetime import datetime
from typing import Tuple, Optional

class UltrasonicSensor:
    def __init__(self, trig_pin: int = 18, echo_pin: int = 24, detection_distance: int = 20):
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
        self.is_initialized = False
        
        self._setup_gpio()
    
    def _setup_gpio(self):
        """Setup GPIO pins for the sensor"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.trig_pin, GPIO.OUT)
            GPIO.setup(self.echo_pin, GPIO.IN)
            
            # Initialize trigger to low
            GPIO.output(self.trig_pin, False)
            time.sleep(0.1)
            self.is_initialized = True
        except Exception as e:
            print(f"Error initializing ultrasonic sensor: {e}")
            self.is_initialized = False
    
    def measure_distance(self) -> Optional[int]:
        """
        Measure distance using ultrasonic sensor
        
        Returns:
            distance in cm or None if measurement fails
        """
        if not self.is_initialized:
            return None
            
        try:
            # Send 10us pulse to trigger
            GPIO.output(self.trig_pin, True)
            time.sleep(0.00001)
            GPIO.output(self.trig_pin, False)
            
            # Wait for echo to start (with timeout)
            pulse_start = time.time()
            timeout = time.time() + 1  # 1 second timeout
            while GPIO.input(self.echo_pin) == 0 and time.time() < timeout:
                pulse_start = time.time()
            
            # Wait for echo to end (with timeout)
            pulse_end = time.time()
            timeout = time.time() + 1  # 1 second timeout
            while GPIO.input(self.echo_pin) == 1 and time.time() < timeout:
                pulse_end = time.time()
            
            # Calculate distance
            pulse_duration = pulse_end - pulse_start
            distance = pulse_duration * 17150  # Speed of sound = 34300 cm/s, divide by 2
            distance = int(distance)
            
            # Filter out unrealistic readings
            if distance < 2 or distance > 400:
                return None
                
            return distance
            
        except Exception as e:
            print(f"Error measuring distance: {e}")
            return None
    
    def detect_object(self) -> Tuple[bool, Optional[int]]:
        """
        Check if object is within detection range
        
        Returns:
            tuple: (is_detected, distance)
        """
        distance = self.measure_distance()
        if distance is None:
            return False, None
            
        is_detected = distance <= self.detection_distance
        return is_detected, distance
    
    def get_status(self) -> dict:
        """
        Get current sensor status
        
        Returns:
            dict: Sensor status information
        """
        distance = self.measure_distance()
        is_detected, _ = self.detect_object()
        
        return {
            "initialized": self.is_initialized,
            "distance_cm": distance,
            "object_detected": is_detected,
            "detection_range_cm": self.detection_distance,
            "timestamp": datetime.now().isoformat()
        }
    
    def cleanup(self):
        """Clean up GPIO resources"""
        try:
            GPIO.cleanup()
        except Exception as e:
            print(f"Error during GPIO cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure GPIO cleanup"""
        self.cleanup()