# Mining Rover Prototype Setup Guide

## Overview
This prototype system combines:
- **Ultrasonic sensor** for distance detection
- **Camera system** (mobile browser or AI camera) for object identification
- **Web interface** for monitoring and control
- **Color-based material detection** (Red=Palladium, Brown=Dirt, Green=Copper)

## Hardware Requirements
- Raspberry Pi 5
- HC-SR04 Ultrasonic Sensor
- Jumper wires
- Optional: AI Camera module

## Software Requirements

### Install Python Dependencies
```bash
pip install flask opencv-python numpy RPi.GPIO requests
```

### GPIO Wiring (Ultrasonic Sensor)
```
HC-SR04  →  Raspberry Pi 5
VCC      →  5V (Pin 2)
GND      →  Ground (Pin 6)
Trig     →  GPIO 18 (Pin 12)
Echo     →  GPIO 24 (Pin 18)
```

## File Structure
Create the following directory structure:
```
rover_project/
├── ultrasonic_sensor.py      # Sensor control code
├── app.py                    # Flask web application
├── rover_control.py          # Integrated control system
├── templates/                # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── send_video.html
│   ├── manage.html
│   └── logs.html
└── log.json                  # Auto-generated log file
```

## Quick Start

### 1. Hardware Setup
- Connect ultrasonic sensor to Raspberry Pi according to wiring diagram
- Ensure all connections are secure

### 2. Save the Code Files
Save each artifact to its respective file:
- Save "Ultrasonic Sensor Code" as `ultrasonic_sensor.py`
- Save "Flask Rover Web Application" as `app.py`
- Save "Integrated Rover Control System" as `rover_control.py`
- Create `templates/` directory and save HTML templates

### 3. Start the Web Server
```bash
python app.py
```
The server will start on `http://localhost:5000`

### 4. Access Web Interface
- **Main Control**: `http://your-pi-ip:5000/`
- **Send Video**: `http://your-pi-ip:5000/send-video`
- **Management**: `http://your-pi-ip:5000/manage`
- **Logs**: `http://your-pi-ip:5000/logs`

### 5. Start Rover Control (Optional)
In a separate terminal:
```bash
python rover_control.py
```

## Usage Options

### Option 1: Mobile Camera Stream
1. Open `http://your-pi-ip:5000/send-video` on your phone
2. Click "Start Camera" to begin streaming
3. Point camera at colored paper objects
4. System will detect and classify materials

### Option 2: AI Camera Module
- Connect AI camera to Raspberry Pi
- Modify the Flask app to read from camera module instead of mobile stream

### Testing the System

#### Material Detection Test
1. Cut colored paper pieces:
   - 🔴 **Red paper** = Palladium
   - 🟤 **Brown paper** = Dirt  
   - 🟢 **Green paper** = Copper

2. Place colored paper in front of camera
3. Check detection results in web interface

#### Distance Detection Test
1. Place objects at various distances from ultrasonic sensor
2. Check distance readings in rover control terminal
3. Verify detection threshold (default: 15cm)

## Configuration

### Adjust Detection Distance
In `ultrasonic_sensor.py`, modify:
```python
sensor = UltrasonicSensor(detection_distance=20)  # 20cm threshold
```

### Modify Color Ranges
In `app.py`, adjust COLOR_RANGES dictionary:
```python
COLOR_RANGES = {
    'red': {
        'lower': np.array([0, 120, 70]),
        'upper': np.array([10, 255, 255]),
        'material': 'palladium'
    },
    # Add more colors as needed
}
```

## Troubleshooting

### GPIO Permission Issues
```bash
sudo usermod -a -G gpio $USER
# Logout and login again
```

### Camera Access Issues
- Ensure browser has camera permissions
- Try HTTPS for mobile camera access
- Check firewall settings

### Flask Server Issues
- Ensure port 5000 is available
- Check if server is accessible from other devices on network

### Mock Mode Testing
If running without hardware, the system automatically uses mock sensors for testing

## API Endpoints

### GET Endpoints
- `/` - Main control page
- `/send-video` - Video streaming page
- `/manage` - Management dashboard
- `/logs` - Log viewer
- `/api/logs` - JSON log data
- `/api/detection` - Current detection status

### POST Endpoints
- `/send-video` - Submit video frames
- `/api/mine` - Trigger mining operation

## Log File Format
```json
[
  {
    "timestamp": "2025-05-29T12:00:00",
    "distance_cm": 12.5,
    "material_detected": true,
    "material_type": "palladium",
    "confidence": 85.2,
    "action": "mining"
  }
]
```

## Next Steps for Full Implementation

1. **Add Motor Control**: Integrate motors for rover movement
2. **Implement Mining Mechanism**: Add actuators for mining operations
3. **Enhance Object Detection**: Use machine learning for better material identification
4. **Add Navigation**: Implement path planning and obstacle avoidance
5. **Real-time Mapping**: Create maps of explored areas and material locations

## Safety Notes
- Always verify electrical connections before powering on
- Use appropriate voltage levels for GPIO pins
- Test in safe environment before autonomous operation
- Monitor system for overheating during extended use

## Support
Check the web interface logs and terminal output for debugging information. The system includes comprehensive error handling and status reporting.