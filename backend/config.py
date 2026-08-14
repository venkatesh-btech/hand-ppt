# ============================================
# Hand Gesture PPT Controller — Configuration
# ============================================

# Camera settings
CAMERA_INDEX = 0
# To use phone camera (IP Webcam app), set this to your phone's stream URL:
# Example: CAMERA_URL = "http://192.168.1.5:8080/video"
CAMERA_URL = None   # None = use laptop webcam
FRAME_WIDTH = 480
FRAME_HEIGHT = 360
CAMERA_FPS = 30     # Request 30 FPS from webcam driver

# MediaPipe Hand Detection
MAX_HANDS = 1
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5
MODEL_COMPLEXITY = 0   # 0 = Lite (fastest), 1 = Full (more accurate)

# Gesture control
COOLDOWN = 1.5          # seconds between actions
SWIPE_THRESHOLD = 0.15  # normalized wrist displacement to trigger swipe

# Performance
JPEG_QUALITY = 50       # Balance between quality and speed
PROCESS_EVERY_N = 3     # Run detection every Nth frame (display all frames)

# Server
HOST = "127.0.0.1"
PORT = 8000

# Gesture → Action mapping
GESTURE_MAP = {
    "next_slide":      {"key": "right",  "label": "Next Slide"},
    "prev_slide":      {"key": "left",   "label": "Previous Slide"},
    "first_slide":     {"key": "home",   "label": "First Slide"},
}
