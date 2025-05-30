import RPi.GPIO as GPIO
import time
import threading
from typing import Dict, Optional

class LEDController:
    def __init__(self, led_pins: Dict[str, int] = None):
        """
        Initialize LED controller
        
        Args:
            led_pins: Dictionary mapping LED names to GPIO pins
                     Example: {'red': 12, 'green': 16, 'blue': 20, 'status': 21}
        """
        self.led_pins = led_pins or {
            'red': 12,      # Red LED for red color detection
            'green': 16,    # Green LED for green color detection
            'blue': 20,     # Blue LED for general status
            'status': 21    # Status LED for system status
        }
        
        self.led_states = {name: False for name in self.led_pins.keys()}
        self.blink_threads = {}
        self.is_initialized = False
        
        self._setup_gpio()
    
    def _setup_gpio(self):
        """Setup GPIO pins for LEDs"""
        try:
            GPIO.setmode(GPIO.BCM)
            for led_name, pin in self.led_pins.items():
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)  # Start with LEDs off
            
            self.is_initialized = True
            print("LED Controller initialized successfully")
        except Exception as e:
            print(f"Error initializing LED controller: {e}")
            self.is_initialized = False
    
    def turn_on(self, led_name: str) -> bool:
        """
        Turn on specific LED
        
        Args:
            led_name: Name of the LED to turn on
            
        Returns:
            Success status
        """
        if not self.is_initialized or led_name not in self.led_pins:
            return False
        
        try:
            # Stop any blinking for this LED
            self._stop_blink(led_name)
            
            GPIO.output(self.led_pins[led_name], GPIO.HIGH)
            self.led_states[led_name] = True
            return True
        except Exception as e:
            print(f"Error turning on LED {led_name}: {e}")
            return False
    
    def turn_off(self, led_name: str) -> bool:
        """
        Turn off specific LED
        
        Args:
            led_name: Name of the LED to turn off
            
        Returns:
            Success status
        """
        if not self.is_initialized or led_name not in self.led_pins:
            return False
        
        try:
            # Stop any blinking for this LED
            self._stop_blink(led_name)
            
            GPIO.output(self.led_pins[led_name], GPIO.LOW)
            self.led_states[led_name] = False
            return True
        except Exception as e:
            print(f"Error turning off LED {led_name}: {e}")
            return False
    
    def toggle(self, led_name: str) -> bool:
        """
        Toggle specific LED
        
        Args:
            led_name: Name of the LED to toggle
            
        Returns:
            Success status
        """
        if self.led_states.get(led_name, False):
            return self.turn_off(led_name)
        else:
            return self.turn_on(led_name)
    
    def blink(self, led_name: str, interval: float = 0.5, duration: Optional[float] = None):
        """
        Blink specific LED
        
        Args:
            led_name: Name of the LED to blink
            interval: Blink interval in seconds
            duration: Total duration to blink (None for indefinite)
        """
        if not self.is_initialized or led_name not in self.led_pins:
            return
        
        # Stop any existing blink for this LED
        self._stop_blink(led_name)
        
        # Start new blink thread
        blink_thread = threading.Thread(
            target=self._blink_worker,
            args=(led_name, interval, duration),
            daemon=True
        )
        self.blink_threads[led_name] = blink_thread
        blink_thread.start()
    
    def _stop_blink(self, led_name: str):
        """Stop blinking for specific LED"""
        if led_name in self.blink_threads:
            # The thread will stop on next iteration when it's no longer in the dict
            del self.blink_threads[led_name]
    
    def _blink_worker(self, led_name: str, interval: float, duration: Optional[float]):
        """Worker function for blinking LED"""
        start_time = time.time()
        
        try:
            while led_name in self.blink_threads:
                # Check duration limit
                if duration and (time.time() - start_time) >= duration:
                    break
                
                # Toggle LED
                current_state = GPIO.input(self.led_pins[led_name])
                GPIO.output(self.led_pins[led_name], not current_state)
                
                time.sleep(interval)
            
            # Ensure LED is off when blinking stops
            GPIO.output(self.led_pins[led_name], GPIO.LOW)
            self.led_states[led_name] = False
            
        except Exception as e:
            print(f"Error in blink worker for LED {led_name}: {e}")
        finally:
            # Clean up thread reference
            if led_name in self.blink_threads:
                del self.blink_threads[led_name]
    
    def handle_color_detection(self, color_detected: str, confidence: float):
        """
        Handle LED response to color detection
        
        Args:
            color_detected: Color that was detected ('red', 'green', 'brown')
            confidence: Detection confidence percentage
        """
        if not self.is_initialized:
            return
        
        # Turn off all color LEDs first
        self.turn_off('red')
        self.turn_off('green')
        self.turn_off('blue')
        
        if color_detected == 'red':
            if confidence > 50:
                self.turn_on('red')  # Solid red for high confidence
            else:
                self.blink('red', 0.3)  # Fast blink for low confidence
                
        elif color_detected == 'green':
            if confidence > 50:
                self.turn_on('green')  # Solid green for high confidence
            else:
                self.blink('green', 0.3)  # Fast blink for low confidence
                
        elif color_detected == 'brown':
            # Use blue LED for brown detection (since we don't have brown LED)
            if confidence > 50:
                self.turn_on('blue')
            else:
                self.blink('blue', 0.3)
    
    def set_system_status(self, status: str):
        """
        Set system status LED
        
        Args:
            status: 'ready', 'scanning', 'detecting', 'error'
        """
        if not self.is_initialized:
            return
        
        status_led = 'status'
        
        if status == 'ready':
            self.turn_on(status_led)
        elif status == 'scanning':
            self.blink(status_led, 1.0)  # Slow blink for scanning
        elif status == 'detecting':
            self.blink(status_led, 0.2)  # Fast blink for detecting
        elif status == 'error':
            self.blink(status_led, 0.1, 3.0)  # Very fast blink for 3 seconds
        else:
            self.turn_off(status_led)
    
    def turn_off_all(self):
        """Turn off all LEDs"""
        for led_name in self.led_pins.keys():
            self.turn_off(led_name)
    
    def test_all_leds(self, duration: float = 0.5):
        """
        Test all LEDs by turning them on briefly
        
        Args:
            duration: How long to keep each LED on during test
        """
        if not self.is_initialized:
            return
        
        print("Testing all LEDs...")
        for led_name in self.led_pins.keys():
            print(f"Testing {led_name} LED...")
            self.turn_on(led_name)
            time.sleep(duration)
            self.turn_off(led_name)
            time.sleep(0.2)
        print("LED test complete")
    
    def get_status(self) -> Dict:
        """
        Get current LED status
        
        Returns:
            Dictionary with LED states and system info
        """
        return {
            'initialized': self.is_initialized,
            'led_states': self.led_states.copy(),
            'led_pins': self.led_pins.copy(),
            'active_blinks': list(self.blink_threads.keys())
        }
    
    def cleanup(self):
        """Clean up GPIO resources"""
        try:
            # Stop all blinking
            self.blink_threads.clear()
            
            # Turn off all LEDs
            if self.is_initialized:
                for pin in self.led_pins.values():
                    GPIO.output(pin, GPIO.LOW)
            
            # Note: GPIO.cleanup() will be called by ultrasonic sensor
            # to avoid conflicts
            print("LED Controller cleaned up")
        except Exception as e:
            print(f"Error during LED cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()