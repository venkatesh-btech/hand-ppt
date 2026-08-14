# ============================================
# Hand Gesture PPT Controller — Slide Controller
# ============================================

import time
import pyautogui
import config


class SlideController:
    """Maps detected gestures to keyboard actions and maintains history."""

    def __init__(self):
        self.last_action_time = 0
        self.cooldown = config.COOLDOWN
        self.history = []          # list of {"time": ..., "gesture": ..., "label": ...}
        self.current_action = ""   # last action label string
        pyautogui.FAILSAFE = False

    def execute(self, gesture_name):
        """
        Execute the action for a gesture if cooldown has passed.
        Returns the action label string, or None if on cooldown / unknown gesture.
        """
        now = time.time()

        if now - self.last_action_time < self.cooldown:
            return None

        mapping = config.GESTURE_MAP.get(gesture_name)
        if not mapping:
            return None

        key = mapping["key"]
        label = mapping["label"]

        if key:
            pyautogui.press(key)

        self.last_action_time = now
        self.current_action = label
        self._log(gesture_name, label)
        return label

    def _log(self, gesture_name, label):
        """Append to history (keep last 200 entries)."""
        entry = {
            "time": time.strftime("%H:%M:%S"),
            "timestamp": time.time(),
            "gesture": gesture_name,
            "label": label,
        }
        self.history.append(entry)
        if len(self.history) > 200:
            self.history = self.history[-200:]

    def get_history(self, limit=50):
        """Return the most recent history entries."""
        return list(reversed(self.history[-limit:]))

    def get_stats(self):
        """Return basic gesture statistics."""
        total = len(self.history)
        gestures_count = {}
        for entry in self.history:
            g = entry["gesture"]
            gestures_count[g] = gestures_count.get(g, 0) + 1
        most_used = max(gestures_count, key=gestures_count.get) if gestures_count else "none"
        return {
            "total_gestures": total,
            "most_used": most_used,
            "breakdown": gestures_count,
        }
