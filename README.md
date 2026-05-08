# EyeGuard — AI Eye Protection for Students & Professionals

EyeGuard is a real-time AI-powered eye health monitor that runs silently in the background while you study or work. It detects eye fatigue, tracks blinking, and reminds you to follow the **20-20-20 rule** — so you never have to think about your eye health again.

---

## The Problem

When we stare at screens, we blink **60-70% less** than normal. This causes:
- Dry eyes
- Eye strain and fatigue
- Blurred vision
- Headaches

Most people don't notice until it's too late.

---

## The Solution — 20-20-20 Rule, Automated

> Every **20 minutes** — Look at something **20 feet away** — For **20 seconds**

EyeGuard enforces this rule automatically using your webcam and AI:

| Feature | Description |
|---|---|
| Eye Detection | Detects open/closed eyes in real time |
| Fatigue Tracking | Measures how long your eyes stay open |
| Smart Alerts | Reminds you to rest every 20 minutes |
| Blink Reminder | Alerts you when you are not blinking enough |
| Session Report | Full report at the end of each session |

---

## Getting Started

### Requirements
- Python 3.10+
- Webcam
- Mac / Windows / Linux

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/eye-guard.git
cd eye-guard

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run EyeGuard
python3 eye_hf.py
```

### First Run
The AI model (~343MB) will download automatically on first run. This only happens once.

---

## How It Works

```
Webcam captures your face
        |
OpenCV detects your eyes
        |
AI model checks: open or closed?
        |
Tracks blink rate + screen time
        |
Smart alerts when you need a break
        |
Session report when you are done
```

---

## Controls

| Key | Action |
|---|---|
| Q | Quit and show session report |

---

## Session Report Example

```
=============================================
           SESSION REPORT
=============================================
  Duration:      45 min
  Eye Fatigue:   12%
  Total Alerts:  3
---------------------------------------------
  Status: Great session!

  Tips for next session:
  - Follow the 20-20-20 rule
  - Blink 15-20 times per minute
  - Keep screen at arm's length
  - Stay hydrated
=============================================
```

---

## The Science Behind It

- **20-20-20 Rule** — Recommended by ophthalmologists worldwide
- **Blink rate** — Normal: 15-20 blinks/min. Screen users average 5-7 blinks/min
- **AI Model** — dima806/closed_eyes_image_detection trained on thousands of eye images

---

## Privacy

Your camera feed never leaves your device. All processing happens locally on your machine. No data is stored or transmitted.

---

## Contributing

Pull requests are welcome. If you have ideas to improve EyeGuard, open an issue or submit a PR.

---

## License

MIT License — free to use, modify, and share.

---

Made to protect your eyes.
