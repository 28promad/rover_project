import cv2
import numpy as np
from typing import Dict, Tuple, Optional

class ColorDetector:
    def __init__(self):
        """Initialize color detector with predefined color ranges"""
        # HSV color ranges for detection
        self.COLOR_RANGES = {
            'red': {
                'lower': np.array([0, 120, 70]),
                'upper': np.array([10, 255, 255]),
                'material': 'palladium',
                'color_bgr': (0, 0, 255)  # Red in BGR
            },
            'brown': {
                'lower': np.array([10, 50, 20]),
                'upper': np.array([20, 255, 200]),
                'material': 'dirt',
                'color_bgr': (42, 42, 165)  # Brown in BGR
            },
            'green': {
                'lower': np.array([40, 40, 40]),
                'upper': np.array([80, 255, 255]),
                'material': 'copper',
                'color_bgr': (0, 255, 0)  # Green in BGR
            }
        }
        
        # Detection square parameters
        self.detection_square_size = 100
        self.confidence_threshold = 5.0  # Minimum confidence percentage
    
    def draw_detection_square(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw detection square in the center of the frame
        
        Args:
            frame: Input frame
            
        Returns:
            Frame with detection square drawn
        """
        if frame is None:
            return frame
            
        h, w = frame.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # Calculate square coordinates
        half_size = self.detection_square_size // 2
        x1 = center_x - half_size
        y1 = center_y - half_size
        x2 = center_x + half_size
        y2 = center_y + half_size
        
        # Draw detection square
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
        
        # Draw crosshairs
        cv2.line(frame, (center_x - 10, center_y), (center_x + 10, center_y), (255, 255, 255), 1)
        cv2.line(frame, (center_x, center_y - 10), (center_x, center_y + 10), (255, 255, 255), 1)
        
        # Add label
        cv2.putText(frame, "DETECTION ZONE", (x1, y1 - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def detect_color_in_square(self, frame: np.ndarray) -> Dict:
        """
        Detect colors within the detection square
        
        Args:
            frame: Input frame
            
        Returns:
            Detection results dictionary
        """
        if frame is None:
            return {'detected': False, 'material': None, 'confidence': 0, 'color': None}
        
        h, w = frame.shape[:2]
        center_x, center_y = w // 2, h // 2
        
        # Extract detection square region
        half_size = self.detection_square_size // 2
        x1 = max(0, center_x - half_size)
        y1 = max(0, center_y - half_size)
        x2 = min(w, center_x + half_size)
        y2 = min(h, center_y + half_size)
        
        detection_region = frame[y1:y2, x1:x2]
        
        if detection_region.size == 0:
            return {'detected': False, 'material': None, 'confidence': 0, 'color': None}
        
        # Convert to HSV
        hsv_region = cv2.cvtColor(detection_region, cv2.COLOR_BGR2HSV)
        
        best_match = {'detected': False, 'material': None, 'confidence': 0, 'color': None}
        
        for color_name, color_info in self.COLOR_RANGES.items():
            # Create mask for this color
            mask = cv2.inRange(hsv_region, color_info['lower'], color_info['upper'])
            
            # Calculate confidence
            total_pixels = mask.shape[0] * mask.shape[1]
            colored_pixels = cv2.countNonZero(mask)
            confidence = (colored_pixels / total_pixels) * 100 if total_pixels > 0 else 0
            
            # Update best match if this color has higher confidence
            if confidence > best_match['confidence'] and confidence > self.confidence_threshold:
                best_match = {
                    'detected': True,
                    'material': color_info['material'],
                    'confidence': round(confidence, 2),
                    'color': color_name,
                    'color_bgr': color_info['color_bgr']
                }
        
        return best_match
    
    def add_detection_overlay(self, frame: np.ndarray, detection_result: Dict) -> np.ndarray:
        """
        Add detection overlay to frame
        
        Args:
            frame: Input frame
            detection_result: Detection results from detect_color_in_square
            
        Returns:
            Frame with detection overlay
        """
        if frame is None:
            return frame
        
        # Draw detection square
        frame = self.draw_detection_square(frame)
        
        h, w = frame.shape[:2]
        
        if detection_result['detected']:
            color_name = detection_result['color']
            material = detection_result['material']
            confidence = detection_result['confidence']
            color_bgr = detection_result.get('color_bgr', (0, 255, 0))
            
            # Status text
            status_text = f"{color_name.upper()} DETECTED"
            material_text = f"Material: {material}"
            confidence_text = f"Confidence: {confidence:.1f}%"
            
            # Background rectangle for text
            cv2.rectangle(frame, (10, 10), (300, 80), (0, 0, 0), -1)
            cv2.rectangle(frame, (10, 10), (300, 80), color_bgr, 2)
            
            # Text overlay
            cv2.putText(frame, status_text, (15, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_bgr, 2)
            cv2.putText(frame, material_text, (15, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, confidence_text, (15, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        else:
            # No detection status
            cv2.rectangle(frame, (10, 10), (200, 40), (0, 0, 0), -1)
            cv2.rectangle(frame, (10, 10), (200, 40), (128, 128, 128), 2)
            cv2.putText(frame, "NO TARGET DETECTED", (15, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Process frame for color detection
        
        Args:
            frame: Input frame
            
        Returns:
            Tuple of (processed_frame, detection_results)
        """
        if frame is None:
            return None, {'detected': False, 'material': None, 'confidence': 0, 'color': None}
        
        # Detect colors in the detection square
        detection_result = self.detect_color_in_square(frame)
        
        # Add overlay to frame
        processed_frame = self.add_detection_overlay(frame.copy(), detection_result)
        
        return processed_frame, detection_result
    
    def get_detection_colors(self) -> Dict:
        """
        Get available detection colors
        
        Returns:
            Dictionary of available colors and their materials
        """
        return {color: info['material'] for color, info in self.COLOR_RANGES.items()}