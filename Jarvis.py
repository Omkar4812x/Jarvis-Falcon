import os
import sys
import threading
import time
import psutil
import eel

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from Backend.JarvisBrain import JarvisCore
from Backend.VoiceInterface import ContinuousListener
from Backend.TTS import SpeakJarvis
from Backend.Logger import logger

# Initialize Core Systems
print("Initializing JARVIS Core Systems...")
brain = JarvisCore()
listener = ContinuousListener(wake_word="jarvis")

web_folder = os.path.join(current_dir, 'web')
eel.init(web_folder)

@eel.expose
def process_user_query(text: str):
    """Called from JS when user inputs text manually."""
    logger.info(f"UI Text Input: {text}")
    listener.pause()
    response = brain.process_command(text)
    
    # Speak the response
    SpeakJarvis(response)
    listener.resume()
    
    return response

def voice_callback(command_text: str):
    """Callback when voice listener captures a command after wake word"""
    if command_text:
        # Update UI about user speech
        try:
            eel.update_voice_transcript("User", f"Jarvis {command_text}")
        except:
            pass
            
        listener.pause()
        # Process through brain
        response = brain.process_command(command_text)
        
        # Update UI about AI response
        try:
            eel.update_voice_transcript("Jarvis", response)
            eel.update_activity_log(f"Processed command: {command_text}")
        except:
            pass
            
        # Speak response
        SpeakJarvis(response)
        listener.resume()

def background_listener_task():
    """Runs the continuous listener"""
    listener.listen_for_wake_word(voice_callback)

def system_stats_task():
    """Periodically emits system stats to the frontend"""
    while True:
        try:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            
            # Simple network speed emulation or actual
            net_io = psutil.net_io_counters()
            # Net speed delta requires holding state. For now, just send total MBs or dummy speed
            # We'll send dummy speed if not easily delta calculable to match UI requirement, 
            # or real % based if needed. Let's compute a basic diff.
            
            # For battery (if available)
            battery = psutil.sensors_battery()
            batt_percent = battery.percent if battery else 100
            
            stats = {
                "cpu": cpu,
                "ram": ram,
                "battery": batt_percent,
                "network": "Active"
            }
            
            # Call JS function
            eel.update_system_stats(stats)
        except Exception:
            pass
        time.sleep(2)

if __name__ == '__main__':
    logger.info("Starting JARVIS Desktop Assistant.")
    
    # Start background threads
    t1 = threading.Thread(target=background_listener_task, daemon=True)
    t2 = threading.Thread(target=system_stats_task, daemon=True)
    t1.start()
    t2.start()
    
    # Start Eel App
    try:
        eel.start('index.html', size=(1200, 800), block=True, host='localhost', port=0)
    except Exception as e:
        logger.error(f"Eel interface error: {e}")
