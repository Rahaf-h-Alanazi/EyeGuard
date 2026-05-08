import time
import subprocess
import platform

class EyeRules:
    def __init__(self):
        self.session_start    = time.time()
        self.last_break       = time.time()
        self.last_blink_check = time.time()

        self.blink_count      = 0
        self.total_frames     = 0
        self.closed_frames    = 0
        self.alerts           = []

        self.BREAK_INTERVAL   = 20 * 60
        self.BLINK_CHECK      = 60
        self.MIN_BLINKS       = 10
        self.MAX_OPEN_SECS    = 5

        self.consecutive_open = 0
        self.FPS              = 15

    def send_notification(self, title, message):
        """Sends a popup above all windows — no permissions needed"""
        msg = message.replace("\n", " ").replace('"', "'")
        try:
            if platform.system() == "Darwin":
                subprocess.Popen([
                    'osascript', '-e',
                    f'tell app "System Events" to display dialog "{msg}" with title "{title}" buttons {{"OK"}} default button "OK"'
                ])
            elif platform.system() == "Windows":
                subprocess.Popen([
                    'powershell', '-Command',
                    f'[System.Windows.MessageBox]::Show("{msg}", "{title}")'
                ])
        except Exception:
            pass

    def update(self, is_open):
        """Receives eye state every frame and computes everything"""
        now = time.time()
        self.total_frames += 1

        if is_open:
            self.consecutive_open += 1
        else:
            if self.consecutive_open > 0:
                self.blink_count += 1
            self.consecutive_open = 0
            self.closed_frames   += 1

        alerts = []

        # Alert 1: 20-20-20 Rule
        if now - self.last_break >= self.BREAK_INTERVAL:
            alerts.append({
                "type":    "break",
                "title":   "EyeGuard — Time for a Break",
                "message": "You have been studying for 20 minutes.\nLook at something 20 feet away for 20 seconds.",
                "color":   (0, 165, 255)
            })
            self.last_break = now

        # Alert 2: Low blink rate
        if now - self.last_blink_check >= self.BLINK_CHECK:
            blinks_per_min = self.blink_count
            if blinks_per_min < self.MIN_BLINKS:
                alerts.append({
                    "type":    "blink",
                    "title":   "EyeGuard — Blink More",
                    "message": f"Only {blinks_per_min} blinks per minute detected. Normal is 15-20. Blink to prevent dry eyes.",
                    "color":   (255, 100, 0)
                })
            self.blink_count      = 0
            self.last_blink_check = now

        # Alert 3: Eyes open too long without blinking
        if self.consecutive_open >= self.FPS * self.MAX_OPEN_SECS:
            alerts.append({
                "type":    "staring",
                "title":   "EyeGuard — Blink Now",
                "message": "You have not blinked in 5 seconds. Close your eyes for 2-3 seconds.",
                "color":   (0, 0, 255)
            })
            self.consecutive_open = 0

        for alert in alerts:
            self.alerts.append({
                "time": time.strftime("%H:%M"),
                **alert
            })
            self.send_notification(alert["title"], alert["message"])

        return alerts

    def get_stats(self):
        """Returns session statistics"""
        elapsed    = time.time() - self.session_start
        fatigue    = int(self.closed_frames / max(self.total_frames, 1) * 100)
        minutes    = int(elapsed / 60)
        blink_rate = int(self.blink_count)

        return {
            "minutes":    minutes,
            "fatigue":    fatigue,
            "alerts":     len(self.alerts),
            "blink_rate": blink_rate
        }

    def get_report(self):
        """Returns end-of-session report"""
        stats   = self.get_stats()
        minutes = stats["minutes"]
        fatigue = stats["fatigue"]

        report  = "\n" + "="*45 + "\n"
        report += "           SESSION REPORT\n"
        report += "="*45 + "\n"
        report += f"  Duration:      {minutes} minutes\n"
        report += f"  Eye Fatigue:   {fatigue}%\n"
        report += f"  Total Alerts:  {stats['alerts']}\n"
        report += "-"*45 + "\n"

        if fatigue < 20:
            report += "  Status: Excellent — your eyes were well rested.\n"
        elif fatigue < 50:
            report += "  Status: Good session. Try to blink more.\n"
        else:
            report += "  Status: Your eyes were strained. Take more breaks.\n"

        report += "\n  Tips for next session:\n"
        report += "  - Follow the 20-20-20 rule\n"
        report += "  - Blink 15-20 times per minute\n"
        report += "  - Keep screen at arm's length\n"
        report += "  - Stay hydrated\n"
        report += "="*45 + "\n"

        return report
