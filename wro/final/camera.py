import cv2
import numpy as np
import threading
import time
from typing import Optional, Tuple, Callable
from color_detector import ColorDetector

class CameraHandler:
    def __init__(self, camera_index: int = 0, resolution: Tuple[int, int] = (640, 480)):
        """
        Initialize camera handler
        
        Args:
            camera_index: Camera device index (0 for Pi camera)
            resolution: Camera resolution (width, height)
        """
        self.camera_index = camera_index
        self.resolution = resolution
        self.cap = None
        self.current_frame = None
        self.is_running = False
        self.frame_lock = threading.Lock()
        self.capture_thread = None
        
        # Initialize color detector
        self.color_detector = ColorDetector()
        
        # Callbacks
        self.frame_callback = None
        self.detection_callback = None
        
        self._initialize_camera()
    
    def _initialize_camera(self):
        """Initialize camera capture"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                raise Exception(f"Could not open camera {self.camera_index}")
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            print(f"Camera initialized: {self.resolution[0]}x{self.resolution[1]}")
            
        except Exception as e:
            print(f"Error initializing camera: {e}")
            self.cap = None
    
    def start_capture(self):
        """Start camera capture in separate thread"""
        if self.cap is None:
            print("Camera not initialized")
            return False
        
        if self.is_running:
            print("Camera capture already running")
            return True
        
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        print("Camera capture started")
        return True
    
    def stop_capture(self):
        """Stop camera capture"""
        self.is_running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        print("Camera capture stopped")
    
    def _capture_loop(self):
        """Main camera capture loop"""
        while self.is_running and self.cap:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to read frame from camera")
                    time.sleep(0.1)
                    continue
                
                # Process frame for color detection
                processed_frame, detection_result = self.color_detector.process_frame(frame)
                
                # Update current frame
                with self.frame_lock:
                    self.current_frame = processed_frame
                
                # Call callbacks if set
                if self.frame_callback:
                    self.frame_callback(processed_frame)
                
                if self.detection_callback and detection_result['detected']:
                    self.detection_callback(detection_result)
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"Error in capture loop: {e}")
                time.sleep(0.1)
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """
        Get the current frame
        
        Returns:
            Current frame or None if not available
        """
        with self.frame_lock:
            return self.current_frame.copy() if self.current_frame is not None else None
    
    def get_frame_with_detection(self) -> Tuple[Optional[np.ndarray], dict]:
        """
        Get current frame with detection results
        
        Returns:
            Tuple of (frame, detection_results)
        """
        frame = self.get_current_frame()
        if frame is None:
            return None, {'detected': False, 'material': None, 'confidence': 0, 'color': None}
        
        # Get fresh detection results
        _, detection_result = self.color_detector.process_frame(frame)
        return frame, detection_result
    
    def capture_single_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame (blocking)
        
        Returns:
            Single captured frame or None
        """
        if self.cap is None:
            return None
        
        try:
            ret, frame = self.cap.read()
            if ret:
                processed_frame, _ = self.color_detector.process_frame(frame)
                return processed_frame
            return None
        except Exception as e:
            print(f"Error capturing single frame: {e}")
            return None
    
    def set_frame_callback(self, callback: Callable[[np.ndarray], None]):
        """
        Set callback for new frames
        
        Args:
            callback: Function to call with each new frame
        """
        self.frame_callback = callback
    
    def set_detection_callback(self, callback: Callable[[dict], None]):
        """
        Set callback for detection events
        
        Args:
            callback: Function to call when detection occurs
        """
        self.detection_callback = callback
    
    def get_frame_as_jpeg(self) -> Optional[bytes]:
        """
        Get current frame as JPEG bytes for web streaming
        
        Returns:
            JPEG encoded frame bytes or None
        """
        frame = self.get_current_frame()
        if frame is None:
            return None
        
        try:
            # Resize for web streaming if needed
            if frame.shape[1] > 640:
                frame = cv2.resize(frame, (640, 480))
            
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                return buffer.tobytes()
            return None
        except Exception as e:
            print(f"Error encoding frame as JPEG: {e}")
            return None
    
    def save_frame(self, filename: str) -> bool:
        """
        Save current frame to file
        
        Args:
            filename: Path to save the frame
            
        Returns:
            Success status
        """
        frame = self.get_current_frame()
        if frame is None:
            return False
        
        try:
            cv2.imwrite(filename, frame)
            print(f"Frame saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving frame: {e}")
            return False
    
    def get_camera_info(self) -> dict:
        """
        Get camera information
        
        Returns:
            Dictionary with camera info
        """
        info = {
            'camera_index': self.camera_index,
            'resolution': self.resolution,
            'is_running': self.is_running,
            'camera_available': self.cap is not None and self.cap.isOpened()
        }
        
        if self.cap and self.cap.isOpened():
            info.update({
                'actual_width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'actual_height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': int(self.cap.get(cv2.CAP_PROP_FPS))
            })
        
        return info
    
    def cleanup(self):
        """Clean up camera resources"""
        self.stop_capture()
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        print("Camera handler cleaned up")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()