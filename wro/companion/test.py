import numpy as np
import sounddevice as sd

def beep(frequency=440, duration=500, volume=0.5):
    fs = 44100
    t = np.linspace(0, duration / 1000, int(fs * duration / 1000), False)
    tone = np.sin(2 * np.pi * frequency * t)
    sd.play(volume * tone, samplerate=fs)
    sd.wait()

beep(1000,300)