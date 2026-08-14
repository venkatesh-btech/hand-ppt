# ============================================
# Hand Gesture PPT Controller — FastAPI Server
# ============================================

import os
import sys
import time
import asyncio
import base64

import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add backend dir to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from slide_controller import SlideController

# ── App Setup ────────────────────────────────────────────
app = FastAPI(title="Hand Gesture PPT Controller")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ── Shared State ─────────────────────────────────────────
engine = None
controller = SlideController()
camera = None

def get_engine():
    """Lazy-load GestureEngine on first use."""
    global engine
    if engine is None:
        try:
            from gesture_engine import GestureEngine
            engine = GestureEngine()
            print("[Engine] GestureEngine initialized successfully")
        except Exception as e:
            print(f"[Engine] Warning: Failed to initialize GestureEngine: {e}")
            print("[Engine] Server will run in UI-only mode")
    return engine


def get_camera():
    global camera
    if camera is None or not camera.isOpened():
        source = config.CAMERA_URL if config.CAMERA_URL else config.CAMERA_INDEX
        print(f"[Camera] Opening: {source}")
        camera = cv2.VideoCapture(source)

        # For IP streams, wait a moment for the connection to establish
        if config.CAMERA_URL and not camera.isOpened():
            import time as _time
            for attempt in range(3):
                _time.sleep(1)
                camera = cv2.VideoCapture(source)
                if camera.isOpened():
                    break
                print(f"[Camera] Retry {attempt + 1}/3...")

        camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        camera.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        print(f"[Camera] Opened: {camera.isOpened()}")
    return camera


# ── Routes ───────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    return FileResponse(index_path)


@app.get("/api/history")
async def get_history():
    return {
        "history": controller.get_history(50),
        "stats": controller.get_stats(),
    }


class CameraSwitch(BaseModel):
    source: str             # "laptop" or "mobile"
    url: str | None = None  # required when source == "mobile"


@app.get("/api/camera")
async def get_camera_info():
    return {
        "source": "mobile" if config.CAMERA_URL else "laptop",
        "url": config.CAMERA_URL or "",
    }


@app.post("/api/camera")
async def switch_camera(data: CameraSwitch):
    global camera
    # Release current camera
    if camera and camera.isOpened():
        camera.release()
        camera = None

    if data.source == "mobile" and data.url:
        # Clean up the URL — ensure it ends with /video for IP Webcam app
        url = data.url.strip().rstrip("/")
        if not url.endswith("/video"):
            url = url + "/video"
        config.CAMERA_URL = url
    else:
        config.CAMERA_URL = None

    # Try to open the new camera and verify it works
    cap = get_camera()
    if cap.isOpened():
        return {"status": "ok", "source": data.source}
    else:
        # Camera failed to open — fall back to laptop
        if camera and camera.isOpened():
            camera.release()
        camera = None
        config.CAMERA_URL = None
        return {"status": "error", "error": f"Could not connect to {data.url}. Check the URL and ensure your phone is on the same network."}


# ── WebSocket — Live Camera + Gesture Stream ─────────────
@app.websocket("/ws")
async def websocket_stream(ws: WebSocket):
    await ws.accept()
    cap = get_camera()

    if not cap.isOpened():
        await ws.send_json({"error": "Camera not available"})
        await ws.close()
        return

    encode_params = [cv2.IMWRITE_JPEG_QUALITY, config.JPEG_QUALITY]

    try:
        while True:
            success, frame = cap.read()
            if not success:
                await asyncio.sleep(0.01)
                continue

            frame = cv2.flip(frame, 1)

            # Resize to target dims if camera gives larger frames
            h, w = frame.shape[:2]
            if w != config.FRAME_WIDTH or h != config.FRAME_HEIGHT:
                frame = cv2.resize(frame, (config.FRAME_WIDTH, config.FRAME_HEIGHT))

            # Detect gestures (engine handles frame-skipping internally)
            gesture_engine = get_engine()
            detections = gesture_engine.detect(frame) if gesture_engine else []

            gesture_data = None
            for det in detections:
                gesture_engine.draw_landmarks(frame, det["landmarks"])
                if det["gesture"]:
                    result = controller.execute(det["gesture"])
                    if result:
                        gesture_data = {
                            "hand": det["label"],
                            "fingers": det["fingers"],
                            "gesture": det["gesture"],
                            "action": result,
                            "time": time.strftime("%H:%M:%S"),
                        }

            # Encode frame to JPEG
            _, buffer = cv2.imencode(".jpg", frame, encode_params)
            b64_frame = base64.b64encode(buffer).decode("utf-8")

            # Build single JSON payload
            payload = {
                "frame": b64_frame,
                "detections": [
                    {"hand": d["label"], "fingers": d["fingers"], "gesture": d["gesture"]}
                    for d in detections
                ],
            }
            if gesture_data:
                payload["action"] = gesture_data

            await ws.send_json(payload)
            await asyncio.sleep(0.001)  # yield to event loop

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")


# ── Startup / Shutdown ───────────────────────────────────
@app.on_event("shutdown")
async def shutdown():
    global camera
    if camera and camera.isOpened():
        camera.release()
    engine.release()


# ── Run ──────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("\n[Hand Gesture PPT Controller]")
    print(f"  -> Open http://localhost:{config.PORT} in your browser\n")
    uvicorn.run(app, host=config.HOST, port=config.PORT)