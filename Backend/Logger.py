import os
import datetime

class JarvisLogger:
    def __init__(self, log_file="jarvis_activity.log"):
        # Store in Database folder
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Database")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_path = os.path.join(self.log_dir, log_file)

    def _write_log(self, level, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(log_entry)
        
        # Also print to stdout so Eel can capture it or console can see it
        print(f"JARVIS_LOG|{level}|{message}")

    def info(self, message):
        self._write_log("INFO", message)

    def error(self, message):
        self._write_log("ERROR", message)

    def command(self, user_command):
        self._write_log("COMMAND", user_command)

# Global instance setup
logger = JarvisLogger()
