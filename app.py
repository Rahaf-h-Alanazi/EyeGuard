import cv2
import time
import threading
from flask import Flask, render_template, Response, jsonify
from PIL import Image
from transformers import pipeline
from rules import EyeRules

app = Flask(__name__)

# ===== Load AI Model =====
print("Loading AI model...")
pipe = pipeline("image-classification", model="dima806/closed_eyes_image_detection")
print("Model ready!")

# ===== Face and Eye Detectors =====
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade  = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# ===== Shared State =====
state = {
    "running":     False,
    "eye_status":  "Waiting",
    "is_open":     None,
    "rules":       None,
    "frame":       None,
    "lock":        threading.Lock()
}

def analyze_frame(frame):
    """Analyzes a frame and returns eye status"""
    h, w  = frame.shape[:2]
    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100,100))

    is_open    = None
    eye_status = "No face detected"

    for (x, y, fw, fh) in faces:
        roi_gray  = gray[y:y+fh//2, x:x+fw]
        roi_color = frame[y:y+fh//2, x:x+fw]
        eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 10, minSize=(25,25))

        if len(eyes) >= 1:
            eyes   = sorted(eyes, key=lambda e: e[2]*e[3], reverse=True)
            closed = 0

            for (ex, ey, ew, eh) in eyes[:2]:
                eye_img = roi_color[ey:ey+eh, ex:ex+ew]
                if eye_img.size > 0 and eye_img.shape[0] > 10:
                    eye_img = cv2.resize(eye_img, (128,128))
                    pil_img = Image.fromarray(cv2.cvtColor(eye_img, cv2.COLOR_BGR2RGB))
                    result  = pipe(pil_img)
                    if "close" in result[0]["label"].lower():
                        closed += 1
                    c = (0,200,0) if "open" in result[0]["label"].lower() else (0,0,255)
                    cv2.rectangle(roi_color, (ex,ey), (ex+ew,ey+eh), c, 2)

            is_open    = closed == 0
            eye_status = "Open" if is_open else "Closed"

        elif len(faces) > 0:
            is_open    = False
            eye_status = "Closed"

        cv2.rectangle(frame, (x,y), (x+fw,y+fh), (40,40,80), 1)

    return frame, is_open, eye_status

def camera_loop():
    """Runs the camera in a separate thread"""
    cap = cv2.VideoCapture(1)
    while state["running"]:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue

        frame, is_open, eye_status = analyze_frame(frame)

        if state["rules"] and is_open is not None:
            state["rules"].update(is_open)

        with state["lock"]:
            state["is_open"]    = is_open
            state["eye_status"] = eye_status
            state["frame"]      = frame.copy()

        time.sleep(0.05)
    cap.release()

# ===== Flask Routes =====

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    if not state["running"]:
        state["running"] = True
        state["rules"]   = EyeRules()
        t = threading.Thread(target=camera_loop, daemon=True)
        t.start()
    return jsonify({"status": "started"})

@app.route('/stop', methods=['POST'])
def stop():
    state["running"] = False
    return jsonify({"status": "stopped"})

@app.route('/data')
def data():
    if not state["rules"]:
        return jsonify({"running": False})

    stats         = state["rules"].get_stats()
    alerts        = state["rules"].alerts[-5:]
    elapsed_secs  = int(time.time() - state["rules"].session_start)
    break_in_secs = max(0, 1200 - (elapsed_secs % 1200))
    break_pct     = int((1200 - break_in_secs) / 12)

    return jsonify({
        "running":      state["running"],
        "eye_status":   state["eye_status"],
        "is_open":      state["is_open"],
        "minutes":      stats["minutes"],
        "fatigue":      stats["fatigue"],
        "alerts_count": stats["alerts"],
        "blink_rate":   stats["blink_rate"],
        "break_in":     break_in_secs,
        "break_pct":    break_pct,
        "alerts":       alerts
    })

@app.route('/frame')
def frame():
    """Sends the current camera frame as JPEG"""
    with state["lock"]:
        f = state["frame"]
    if f is None:
        return "", 204
    _, buf = cv2.imencode('.jpg', f, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return Response(buf.tobytes(), mimetype='image/jpeg')

@app.route('/report')
def report():
    if not state["rules"]:
        return jsonify({"report": "No session data available."})
    return jsonify({"report": state["rules"].get_report()})

if __name__ == '__main__':
    print("EyeGuard running on http://localhost:5000")
    app.run(debug=False, threaded=True)
