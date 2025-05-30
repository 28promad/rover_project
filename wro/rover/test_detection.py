from camera import CameraHandler
from color import ColorDetector
import cv2
import time

def test_detection():
    # Initialize components
    camera = CameraHandler(camera_index=0, resolution=(640, 480))
    detector = ColorDetector()
    
    def detection_callback(result):
        print(f"Detection: {result}")
        if result['detected']:
            print(f"🎯 Material: {result['material']}")
            print(f"Confidence: {result['confidence']:.1f}%")
            print(f"Color: {result['color']}")
            print("-" * 50)
    
    # Set callback and start camera
    camera.set_detection_callback(detection_callback)
    if not camera.start_capture():
        print("Failed to start camera!")
        return
    
    print("Test running - Press 'q' to quit")
    try:
        while True:
            # Get frame (this will trigger detection callback)
            frame = camera.get_frame()
            if frame is not None:
                # Show the frame
                cv2.imshow('Test Detection', frame)
                
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            time.sleep(0.1)  # Small delay
            
    finally:
        camera.cleanup()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    test_detection()