import cv2
import time
from PIL import Image
from transformers import pipeline
from rules import EyeRules

# ===== تحميل الموديل =====
print("Loading AI model...")
pipe = pipeline("image-classification", model="dima806/closed_eyes_image_detection")
print("Model ready!")

# ===== كاشف الوجه والعين =====
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade  = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# ===== قواعد 20-20-20 =====
rules = EyeRules()

# ===== تشغيل الكاميرا =====
cap = cv2.VideoCapture(1)
print("EyeGuard is running — press Q to quit\n")

# ===== متغيرات التنبيه =====
active_alert    = None
alert_start     = 0
ALERT_DURATION  = 4  # ثواني يظهر التنبيه

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h_frame, w_frame = frame.shape[:2]
    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100,100))

    eye_status = "No face"
    color      = (128,128,128)
    is_open    = None
    score      = 0

    for (x, y, w, h) in faces:
        roi_gray  = gray[y:y+h//2, x:x+w]
        roi_color = frame[y:y+h//2, x:x+w]
        eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 10, minSize=(25,25))

        if len(eyes) >= 1:
            eyes = sorted(eyes, key=lambda e: e[2]*e[3], reverse=True)
            open_count       = 0
            closed_count_eye = 0

            for (ex, ey, ew, eh) in eyes[:2]:
                eye_img = roi_color[ey:ey+eh, ex:ex+ew]
                if eye_img.size > 0 and eye_img.shape[0] > 10:
                    eye_img_r = cv2.resize(eye_img, (128,128))
                    pil_img   = Image.fromarray(cv2.cvtColor(eye_img_r, cv2.COLOR_BGR2RGB))
                    result    = pipe(pil_img)
                    label     = result[0]["label"]
                    score     = result[0]["score"] * 100
                    eye_open  = "open" in label.lower()
                    eye_color = (0,200,0) if eye_open else (0,0,255)
                    cv2.rectangle(roi_color, (ex,ey), (ex+ew,ey+eh), eye_color, 2)
                    if eye_open:
                        open_count += 1
                    else:
                        closed_count_eye += 1

            is_open    = closed_count_eye == 0
            eye_status = f"{'Open' if is_open else 'CLOSED'} ({score:.0f}%)"
            color      = (0,200,0) if is_open else (0,0,255)

        elif len(faces) > 0:
            is_open    = False
            eye_status = "CLOSED"
            color      = (0,0,255)

        cv2.rectangle(frame, (x,y), (x+w,y+h), (255,200,0), 2)

    # ===== تحديث القواعد =====
    if is_open is not None:
        alerts = rules.update(is_open)
        if alerts and not active_alert:
            active_alert = alerts[0]
            alert_start  = time.time()

    # ===== الإحصائيات =====
    stats     = rules.get_stats()
    elapsed   = stats["minutes"]
    fatigue   = stats["fatigue"]
    bar_w     = int(w_frame * 0.4)
    bar_fill  = int(bar_w * fatigue / 100)
    bar_color = (0,200,0) if fatigue < 40 else (0,165,255) if fatigue < 70 else (0,0,255)

    # خلفية شفافة
    overlay = frame.copy()
    cv2.rectangle(overlay, (0,0), (340,160), (0,0,0), -1)
    cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

    cv2.putText(frame, f"Eye: {eye_status}",            (10,30),  cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(frame, f"Session: {elapsed} min",       (10,60),  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)
    cv2.putText(frame, f"Fatigue: {fatigue}%",          (10,90),  cv2.FONT_HERSHEY_SIMPLEX, 0.6, bar_color, 1)
    cv2.putText(frame, f"Alerts: {stats['alerts']}",    (10,120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,150,255), 1)

    # وقت الاستراحة الجاية
    next_break = max(0, 20 - elapsed % 20)
    cv2.putText(frame, f"Next break: {next_break} min", (10,148), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)

    # شريط الإجهاد
    cv2.rectangle(frame, (10,155), (10+bar_w,165), (50,50,50), -1)
    cv2.rectangle(frame, (10,155), (10+bar_fill,165), bar_color, -1)

    # ===== عرض التنبيه =====
    if active_alert:
        elapsed_alert = time.time() - alert_start
        if elapsed_alert < ALERT_DURATION:
            # خلفية التنبيه
            alert_overlay = frame.copy()
            cv2.rectangle(alert_overlay, (w_frame//2-220, h_frame//2-60),
                         (w_frame//2+220, h_frame//2+70), (20,20,20), -1)
            cv2.addWeighted(alert_overlay, 0.8, frame, 0.2, 0, frame)

            # نص التنبيه
            alert_color = active_alert["color"]
            cv2.putText(frame, active_alert["title"],
                       (w_frame//2-200, h_frame//2-20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, alert_color, 2)

            lines = active_alert["message"].split("\n")
            for i, line in enumerate(lines):
                cv2.putText(frame, line,
                           (w_frame//2-200, h_frame//2+20+i*30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,255), 1)
        else:
            active_alert = None

    cv2.imshow("EyeGuard 👁", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ===== تقرير نهاية الجلسة =====
cap.release()
cv2.destroyAllWindows()
print(rules.get_report())
