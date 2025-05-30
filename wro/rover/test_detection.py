from camera import CameraHandler
from color import ColorDetector
import cv2
import time

def test_detection():
    """Test camera and color/material detection"""
    print("\n=== Testing Camera and Detection ===")
    
    # Initialize components
    camera = CameraHandler()  # Using default Pi Camera
    detector = ColorDetector()
    
    def detection_callback(result):
        """Handle detection events"""
        if result['detected']:
            material = result['material']
            color = result['color']
            confidence = result['confidence']
            
            print("\n🎯 Detection:")
            print(f"Material: {material}")
            print(f"Color: {color}")
            print(f"Confidence: {confidence:.1f}%")
            print("-" * 40)
    
    # Set callback and start camera
    camera.set_detection_callback(detection_callback)
    if not camera.start_capture():
        print("❌ Failed to start camera!")
        return
    
    print("\n✓ Camera initialized")
    print("• Show different materials to test detection")
    print("• Press 'q' to quit")
    
    try:
        while True:
            # Get frame with detection overlay
            frame = camera.get_current_frame()
            if frame is not None:
                # Show the frame
                cv2.imshow('Detection Test', frame)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            time.sleep(0.1)  # Small delay
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
    finally:
        camera.cleanup()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    test_detection()