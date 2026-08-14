# ============================================
# Hand Gesture PPT Controller — Gesture Engine
# ============================================

import cv2
import mediapipe as mp
import config


class GestureEngine:
    """MediaPipe-based hand gesture detection engine (optimised for speed)."""

    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=config.MAX_HANDS,
            model_complexity=config.MODEL_COMPLEXITY,
            min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
        )
        self.prev_wrist_x = None

        # Frame-skip state
        self._frame_counter = 0
        self._last_detections = []

    def _count_fingers(self, landmarks, hand_label):
        """Count how many fingers are raised."""
        lm = landmarks.landmark
        fingers = []

        # Thumb — direction depends on left/right hand
        if hand_label == "Right":
            fingers.append(1 if lm[4].x < lm[3].x else 0)
        else:
            fingers.append(1 if lm[4].x > lm[3].x else 0)

        # Index, Middle, Ring, Pinky
        for tip in [8, 12, 16, 20]:
            fingers.append(1 if lm[tip].y < lm[tip - 2].y else 0)

        return fingers.count(1)

    def _detect_swipe(self, wrist_x):
        """Detect horizontal swipe and return direction or None."""
        if self.prev_wrist_x is None:
            self.prev_wrist_x = wrist_x
            return None

        diff = wrist_x - self.prev_wrist_x
        self.prev_wrist_x = wrist_x

        if diff > config.SWIPE_THRESHOLD:
            return "swipe_right"
        elif diff < -config.SWIPE_THRESHOLD:
            return "swipe_left"
        return None

    def detect(self, frame):
        """
        Process a single frame and return detection results.

        Uses frame-skipping: only runs MediaPipe every PROCESS_EVERY_N frames,
        returning cached detections on skipped frames for smooth camera display.

        Returns a list of dicts, each containing:
            - label: "Left" or "Right"
            - fingers: int (0-5)
            - gesture: str or None  (gesture name from GESTURE_MAP keys)
            - landmarks: hand landmarks for drawing
        """
        self._frame_counter += 1

        # On skipped frames, return cached detections (no heavy processing)
        if self._frame_counter % config.PROCESS_EVERY_N != 0:
            return self._last_detections

        # Downscale for faster MediaPipe inference
        h, w = frame.shape[:2]
        process_w, process_h = 240, 180
        if w > process_w or h > process_h:
            small = cv2.resize(frame, (process_w, process_h), interpolation=cv2.INTER_NEAREST)
        else:
            small = frame

        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False          # small perf hint for MediaPipe
        result = self.hands.process(rgb)
        rgb.flags.writeable = True
        detections = []

        if not result.multi_hand_landmarks:
            self.prev_wrist_x = None
            self._last_detections = detections
            return detections

        for hand_landmarks, hand_info in zip(
            result.multi_hand_landmarks, result.multi_handedness
        ):
            label = hand_info.classification[0].label
            fingers = self._count_fingers(hand_landmarks, label)
            wrist_x = hand_landmarks.landmark[0].x
            gesture = None

            # Gesture detection
            if label == "Right" and fingers == 5:
                gesture = "first_slide"
            elif label == "Right" and fingers == 2:
                gesture = "next_slide"
            elif label == "Left" and fingers == 2:
                gesture = "prev_slide"
            else:
                # Check swipe
                swipe = self._detect_swipe(wrist_x)
                if swipe == "swipe_right":
                    gesture = "next_slide"
                elif swipe == "swipe_left":
                    gesture = "prev_slide"

            detections.append({
                "label": label,
                "fingers": fingers,
                "gesture": gesture,
                "landmarks": hand_landmarks,
            })

        self._last_detections = detections
        return detections

    def draw_landmarks(self, frame, landmarks):
        """Draw hand landmarks on the frame."""
        self.mp_drawing.draw_landmarks(
            frame, landmarks, self.mp_hands.HAND_CONNECTIONS,
            self.mp_drawing.DrawingSpec(color=(0, 255, 128), thickness=2, circle_radius=3),
            self.mp_drawing.DrawingSpec(color=(0, 200, 255), thickness=2),
        )

    def release(self):
        """Release MediaPipe resources."""
        self.hands.close()
