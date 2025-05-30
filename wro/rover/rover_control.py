#!/usr/bin/env python3
"""
Integrated Mining Rover Control System
Combines ultrasonic sensor detection with camera-based material identification
"""

import threading
import time
import requests
import json
from datetime import datetime

# Import the ultrasonic sensor class
try:
    from ultrasonic_sensor import UltrasonicSensor
    SENSOR_AVAILABLE = True
except ImportError:
    print("Warning: Could not import ultrasonic sensor. Running in simulation mode.")
    SENSOR_AVAILABLE = False

class MockSensor:
    """Mock sensor for testing without hardware"""
    def __init__(self, detection_distance=20):
        self.detection_distance = detection_distance
        self.mock_distance = 25
    
    def detect_object(self):
        # Simulate varying distances
        self.mock_distance += (time.time() % 10 - 5) * 2
        self.mock_distance = max(5, min(50, self.mock_distance))
        detected = self.mock_distance <= self.detection_distance
        return detected, round(self.mock_distance, 2)
    
    def log_detection(self, distance, detected=False, object_type=None):
        # Mock logging
        pass

class RoverController:
    def __init__(self, server_url="http://localhost:5000"):
        """
        Initialize rover controller
        
        Args:
            server_url: URL of the Flask web server
        """
        self.server_url = server_url
        self.running = False
        self.mining_mode = False
        
        # Initialize sensor (real or mock)
        if SENSOR_AVAILABLE:
            self.sensor = UltrasonicSensor(detection_distance=15)
            print("✅ Ultrasonic sensor initialized")
        else:
            self.sensor = MockSensor(detection_distance=15)
            print("⚠️  Using mock sensor for testing")
        
        # Threading events
        self.stop_event = threading.Event()
        
    def get_detection_status(self):
        """
        Get current material detection status from server
        
        Returns:
            dict: Detection status
        """
        try:
            response = requests.get(f"{self.server_url}/api/detection", timeout=5)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException as e:
            print(f"❌ Error getting detection status: {e}")
        
        return {'detected': False, 'material': None, 'confidence': 0}
    
    def trigger_mining(self, distance, material_info):
        """
        Trigger mining operation via server API
        
        Args:
            distance: Current distance reading
            material_info: Material detection information
        """
        try:
            payload = {
                'distance': distance,
                'material': material_info.get('material'),
                'confidence': material_info.get('confidence', 0)
            }
            
            response = requests.post(
                f"{self.server_url}/api/mine", 
                json=payload, 
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"⛏️  Mining result: {result['message']}")
                return result
            else:
                print(f"❌ Mining request failed: {response.status_code}")
                
        except requests.RequestException as e:
            print(f"❌ Error triggering mining: {e}")
        
        return None
    
    def rover_main_loop(self):
        """
        Main rover operation loop
        """
        print("🤖 Rover main loop started")
        scan_interval = 1.0  # seconds between scans
        
        while not self.stop_event.is_set():
            try:
                # Get distance reading from ultrasonic sensor
                object_detected, distance = self.sensor.detect_object()
                
                print(f"📏 Distance: {distance}cm", end="")
                
                if object_detected:
                    print(f" - 🎯 Object detected within range!")
                    
                    # Get camera detection results
                    detection_info = self.get_detection_status()
                    
                    if detection_info.get('detected', False):
                        material = detection_info.get('material', 'unknown')
                        confidence = detection_info.get('confidence', 0)
                        
                        print(f"📷 Camera detected: {material} ({confidence}% confidence)")
                        
                        if self.mining_mode:
                            # Automatically trigger mining
                            mining_result = self.trigger_mining(distance, detection_info)
                            if mining_result:
                                print(f"⚡ Auto-mining: {mining_result['status']}")
                        else:
                            print("💡 Manual mode: Use web interface to trigger mining")
                    
                    else:
                        print("📷 Camera: No valuable material detected")
                
                else:
                    print(" - ✅ Clear path")
                
                # Log the detection
                material_type = None
                if object_detected:
                    detection_info = self.get_detection_status()
                    if detection_info.get('detected'):
                        material_type = detection_info.get('material')
                
                self.sensor.log_detection(
                    distance, 
                    detected=object_detected, 
                    object_type=material_type
                )
                
                # Wait before next scan
                time.sleep(scan_interval)
                
            except KeyboardInterrupt:
                print("\n⏹️  Stopping rover...")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                time.sleep(2)  # Wait longer on error
        
        print("🛑 Rover main loop stopped")
    
    def start_rover(self, auto_mining=False):
        """
        Start the rover operation
        
        Args:
            auto_mining: Enable automatic mining when materials are detected
        """
        if self.running:
            print("⚠️  Rover is already running")
            return
        
        self.running = True
        self.mining_mode = auto_mining
        self.stop_event.clear()
        
        print(f"🚀 Starting rover...")
        print(f"🔧 Mining mode: {'AUTO' if auto_mining else 'MANUAL'}")
        print(f"🌐 Server: {self.server_url}")
        print(f"📡 Sensor range: {self.sensor.detection_distance}cm")
        
        # Start main loop in separate thread
        self.rover_thread = threading.Thread(target=self.rover_main_loop)
        self.rover_thread.daemon = True
        self.rover_thread.start()
        
        print("✅ Rover started successfully")
    
    def stop_rover(self):
        """
        Stop the rover operation
        """
        if not self.running:
            print("⚠️  Rover is not running")
            return
        
        print("🛑 Stopping rover...")
        self.stop_event.set()
        self.running = False
        
        if hasattr(self, 'rover_thread'):
            self.rover_thread.join(timeout=5)
        
        print("✅ Rover stopped")
    
    def status(self):
        """
        Print current rover status
        """
        print(f"\n📊 ROVER STATUS")
        print(f"Running: {'Yes' if self.running else 'No'}")
        print(f"Mining Mode: {'AUTO' if self.mining_mode else 'MANUAL'}")
        print(f"Server: {self.server_url}")
        print(f"Sensor: {'Hardware' if SENSOR_AVAILABLE else 'Mock'}")
        
        # Try to get current detection
        if self.running:
            try:
                detected, distance = self.sensor.detect_object()
                print(f"Current Distance: {distance}cm")
                print(f"Object Detected: {'Yes' if detected else 'No'}")
                
                detection_info = self.get_detection_status()
                if detection_info.get('detected'):
                    print(f"Material: {detection_info['material']} ({detection_info['confidence']}%)")
                else:
                    print("Material: None detected")
            except Exception as e:
                print(f"Status check error: {e}")

def main():
    """
    Main function with interactive CLI
    """
    print("🤖 Mining Rover Control System")
    print("=" * 40)
    
    # Initialize rover controller
    rover = RoverController()
    
    print("\nCommands:")
    print("  start [auto] - Start rover (optional: auto-mining mode)")
    print("  stop         - Stop rover")
    print("  status       - Show rover status")
    print("  mine         - Manually trigger mining")
    print("  help         - Show this help")
    print("  quit         - Exit program")
    
    try:
        while True:
            command = input("\nrover> ").strip().lower().split()
            
            if not command:
                continue
            
            cmd = command[0]
            
            if cmd == "start":
                auto_mode = len(command) > 1 and command[1] == "auto"
                rover.start_rover(auto_mining=auto_mode)
            
            elif cmd == "stop":
                rover.stop_rover()
            
            elif cmd == "status":
                rover.status()
            
            elif cmd == "mine":
                if rover.running:
                    detected, distance = rover.sensor.detect_object()
                    detection_info = rover.get_detection_status()
                    result = rover.trigger_mining(distance, detection_info)
                    if result:
                        print(f"Mining result: {result['message']}")
                else:
                    print("⚠️  Start rover first")
            
            elif cmd == "help":
                print("\nCommands:")
                print("  start [auto] - Start rover (optional: auto-mining mode)")
                print("  stop         - Stop rover")
                print("  status       - Show rover status")
                print("  mine         - Manually trigger mining")
                print("  help         - Show this help")
                print("  quit         - Exit program")
            
            elif cmd in ["quit", "exit", "q"]:
                if rover.running:
                    rover.stop_rover()
                print("👋 Goodbye!")
                break
            
            else:
                print(f"❌ Unknown command: {cmd}")
                print("Type 'help' for available commands")
    
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        if rover.running:
            rover.stop_rover()
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if rover.running:
            rover.stop_rover()

if __name__ == "__main__":
    main()