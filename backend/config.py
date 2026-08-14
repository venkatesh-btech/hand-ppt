# ============================================
# Hand Gesture PPT Controller — Configuration
# ============================================

# Camera settings
CAMERA_INDEX = 0
# To use phone camera (IP Webcam app), set this to your phone's stream URL:
# Example: CAMERA_URL = "http://192.168.1.5:8080/video"
CAMERA_URL = None   # None = use laptop webcam
FRAME_WIDTH = 384   # Reduced from 480 for faster processing
FRAME_HEIGHT = 288  # Reduced from 360 for faster processing
CAMERA_FPS = 30     # Request 30 FPS from webcam driver

# MediaPipe Hand Detection
MAX_HANDS = 1
MIN_DETECTION_CONFIDENCE = 0.6  # Higher threshold = faster, fewer false positives
MIN_TRACKING_CONFIDENCE = 0.6
MODEL_COMPLEXITY = 0   # 0 = Lite (fastest), 1 = Full (more accurate)

# Gesture control
COOLDOWN = 1.5          # seconds between actions
SWIPE_THRESHOLD = 0.15  # normalized wrist displacement to trigger swipe

# Performance
JPEG_QUALITY = 35       # Lower quality = faster transmission & smaller storage
PROCESS_EVERY_N = 4     # Run detection every 4th frame for better performance (still smooth @ 30fps)

# Server
HOST = "127.0.0.1"
PORT = 8000

# Gesture → Action mapping
GESTURE_MAP = {
    "next_slide":      {"key": "right",  "label": "Next Slide"},
    "prev_slide":      {"key": "left",   "label": "Previous Slide"},
    "first_slide":     {"key": "home",   "label": "First Slide"},
}
