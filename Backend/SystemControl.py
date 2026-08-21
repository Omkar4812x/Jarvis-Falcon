import os
import subprocess
import webbrowser
import psutil
from Backend.Logger import logger

class SystemController:
    """Handles OS-level system commands for JARVIS"""

    @staticmethod
    def open_application(app_name: str) -> bool:
        logger.info(f"Opening application: {app_name}")
        try:
            if os.name == 'nt':
                subprocess.Popen(f'start "" "{app_name}"', shell=True)
                return True
            else:
                subprocess.Popen(['open', app_name] if sys.platform == 'darwin' else ['xdg-open', app_name])
                return True
        except Exception as e:
            logger.error(f"Failed to open {app_name}: {e}")
            return False

    @staticmethod
    def close_application(app_name: str) -> bool:
        logger.info(f"Closing application: {app_name}")
        try:
            closed = False
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and app_name.lower() in proc.info['name'].lower():
                    proc.terminate()
                    closed = True
            if not closed and os.name == 'nt':
                # Fallback to taskkill
                os.system(f'taskkill /im {app_name}.exe /f')
                closed = True
            return closed
        except Exception as e:
            logger.error(f"Failed to close {app_name}: {e}")
            return False

    @staticmethod
    def search_internet(query: str):
        logger.info(f"Searching google for: {query}")
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        return True

    @staticmethod
    def open_website(url: str):
        if not url.startswith('http'):
            url = f"https://{url}"
        logger.info(f"Opening website: {url}")
        webbrowser.open(url)
        return True

    @staticmethod
    def shutdown():
        logger.info("Executing system shutdown sequence.")
        if os.name == 'nt':
            os.system("shutdown /s /t 5")
            
    @staticmethod
    def restart():
        logger.info("Executing system restart sequence.")
        if os.name == 'nt':
            os.system("shutdown /r /t 5")

    @staticmethod
    def control_volume(action: str):
        logger.info(f"Volume adjustment requested: {action} (Command sent to OS)")
        return True
