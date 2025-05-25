import cv2
import numpy as np
import mediapipe as mp
import sounddevice as sd
import tkinter as tk
from datetime import datetime
import threading
import time

# Initialize MediaPipe Face Detection and Facial Landmarks
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils
mp_face_mesh = mp.solutions.face_mesh

# Constants
VOLUME_THRESHOLD_LOUD = 30
VOLUME_THRESHOLD_QUIET = 10
UPDATE_INTERVAL = 2  # seconds
SAMPLE_RATE = 44100  # Audio sample rate

# Mood definitions
MOODS = {
    'excited': {'face': [0,1,0,0,0,0,1,0,1], 'freq': 1000, 'duration': 300},
    'sleepy': {'face': [0,0,0,1,1,1,0,0,0], 'freq': 400, 'duration': 500},
    'alert': {'face': [1,0,1,0,0,0,1,1,1], 'freq': 1500, 'duration': 200},
    'neutral': {'face': [1,0,1,0,0,0,1,0,1], 'freq': 600, 'duration': 400}
}

class VirtualCompanion:
    def __init__(self):
        # Initialize variables
        self.current_emotion = "neutral"
        self.current_volume = 0
        self.current_mood = "neutral"
        self.running = True
       
        # Initialize webcam
        self.cap = cv2.VideoCapture(0)
       
        # Initialize GUI
        self.root = tk.Tk()
        self.root.title("AI Virtual Companion")
        self.canvas = tk.Canvas(self.root, width=300, height=300, bg='white')
        self.canvas.pack()
        self.draw_face(MOODS['neutral']['face'])
       
        # Add quit button
        quit_button = tk.Button(self.root, text="Quit", command=self.on_close)
        quit_button.pack()
       
        # Start main loop in a separate thread
        self.thread = threading.Thread(target=self.main_loop)
        self.thread.start()
       
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()
   
    def on_close(self):
        self.running = False
        self.thread.join()
        self.cap.release()
        self.root.destroy()
   
    def beep(self, frequency=440, duration=500, volume=0.5):
        """Generate a beep sound using sounddevice"""
        try:
            t = np.linspace(0, duration / 1000, int(SAMPLE_RATE * duration / 1000), False)
            tone = np.sin(2 * np.pi * frequency * t)
            sd.play(volume * tone, samplerate=SAMPLE_RATE)
            sd.wait()
        except Exception as e:
            print(f"Error generating beep: {e}")
   
    def detect_emotion(self, frame):
        """Detect emotion from facial expression using MediaPipe"""
        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
       
        # Use MediaPipe Face Mesh for more detailed facial analysis
        with mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            min_detection_confidence=0.5) as face_mesh:
           
            results = face_mesh.process(rgb_frame)
           
            if results.multi_face_landmarks:
                # Very simple emotion detection based on mouth and eyebrows
                landmarks = results.multi_face_landmarks[0].landmark
               
                # Get mouth openness (simplified)
                mouth_top = landmarks[13].y
                mouth_bottom = landmarks[14].y
                mouth_openness = mouth_bottom - mouth_top
               
                # Get eyebrow position (simplified)
                left_eyebrow = landmarks[65].y
                right_eyebrow = landmarks[295].y
               
                if mouth_openness > 0.03:  # Smiling
                    return "happy"
                elif left_eyebrow < 0.2 and right_eyebrow < 0.2:  # Eyebrows raised
                    return "surprised"
                elif left_eyebrow > 0.25 or right_eyebrow > 0.25:  # Eyebrows furrowed
                    return "angry"
       
        return "neutral"
   
    def get_volume(self):
        """Measure ambient sound level"""
        try:
            duration = 1  # seconds
           
            # Record audio
            recording = sd.rec(int(duration * SAMPLE_RATE),
                              samplerate=SAMPLE_RATE,
                              channels=1,
                              blocking=True)
           
            # Calculate RMS volume
            rms = np.sqrt(np.mean(recording**2))
            volume = int(rms * 100)  # Scale to a reasonable range
           
            return volume
        except Exception as e:
            print(f"Error measuring volume: {e}")
            return 0
   
    def get_mood(self, emotion, volume):
        """Determine mood based on emotion and volume"""
        if emotion in ["angry", "surprised"]:
            return "alert"
        elif volume > VOLUME_THRESHOLD_LOUD and emotion == "happy":
            return "excited"
        elif volume < VOLUME_THRESHOLD_QUIET:
            return "sleepy"
        else:
            return "neutral"
   
    def draw_face(self, pattern):
        """Draw the retro face based on mood pattern"""
        self.canvas.delete("all")
       
        # Draw 3x3 grid of circles
        for i in range(3):
            for j in range(3):
                x = 100 + j * 50
                y = 100 + i * 50
                fill = 'black' if pattern[i*3 + j] else 'white'
                self.canvas.create_oval(x-20, y-20, x+20, y+20, fill=fill, outline='black')
       
        self.root.update()
   
    def play_mood_sound(self, mood):
        """Play sound based on mood using our beep function"""
        mood_settings = MOODS.get(mood, MOODS['neutral'])
        self.beep(mood_settings['freq'], mood_settings['duration'])
   
    def log_mood(self, mood):
        """Log mood to file with timestamp"""
        try:
            with open('companion_log.txt', 'a') as f:
                f.write(f"{datetime.now().isoformat()}: {mood}\n")
        except Exception as e:
            print(f"Error logging mood: {e}")
   
    def main_loop(self):
        """Main companion loop"""
        while self.running:
            try:
                # Capture frame from webcam
                ret, frame = self.cap.read()
                if not ret:
                    continue
               
                # Detect emotion
                emotion = self.detect_emotion(frame)
                self.current_emotion = emotion
               
                # Get ambient volume
                volume = self.get_volume()
                self.current_volume = volume
               
                # Determine mood
                mood = self.get_mood(emotion, volume)
                self.current_mood = mood
               
                # Update display and sound
                self.draw_face(MOODS[mood]['face'])
                self.play_mood_sound(mood)
               
                # Log mood
                self.log_mood(mood)
               
                # Wait for next update
                time.sleep(UPDATE_INTERVAL)
               
            except Exception as e:
                print(f"Error in main loop: {e}")
                continue

# Start the companion
if __name__ == "__main__":
    companion = VirtualCompanion()