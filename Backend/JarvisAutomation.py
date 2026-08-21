import os
import re
import sys
import subprocess
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# JarvisAutomation — AI-powered task executor
# ---------------------------------------------------------------------------

class JarvisAutomation:
    """
    JARVIS code-execution engine.
    Uses Groq (Llama) to generate Python code for system tasks, then runs it.
    """

    def __init__(self):
        self._load_environment()
        self._initialize_client()
        self._setup_context()

    def _load_environment(self):
        load_dotenv()
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")

    def _initialize_client(self):
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=self.api_key
        )

    def _setup_context(self):
        self.messages = [
            {
                "role": "system",
                "content": (
                    "You are JARVIS, an advanced AI assistant. "
                    "You are a task executor that generates safe Python code to perform system operations."
                )
            },
            {
                "role": "system",
                "content": (
                    "Available modules: webbrowser, pyautogui, time, pyperclip, random, datetime, "
                    "tkinter, os, subprocess (use carefully), psutil for process management. "
                    "NEVER use input(). Always use default paths. Validate all operations before execution."
                )
            },
            # Few-shot examples
            {
                "role": "user",
                "content": "open Google Chrome"
            },
            {
                "role": "assistant",
                "content": (
                    "\n```python\n"
                    "import webbrowser\nimport time\n\n"
                    "webbrowser.open('https://www.google.com')\n"
                    "time.sleep(1)\nprint('Chrome opened successfully')\n"
                    "```"
                )
            },
            {
                "role": "user",
                "content": "close Google Chrome"
            },
            {
                "role": "assistant",
                "content": (
                    "\n```python\n"
                    "import psutil\nimport os\nimport time\n\n"
                    "try:\n"
                    "    for proc in psutil.process_iter(['pid', 'name']):\n"
                    "        if 'chrome' in proc.info['name'].lower():\n"
                    "            proc.terminate()\n"
                    "    time.sleep(2)\n"
                    "    print('Chrome closed successfully')\n"
                    "except Exception:\n"
                    "    if os.name == 'nt':\n"
                    "        os.system('taskkill /im chrome.exe /f')\n"
                    "```"
                )
            },
        ]

    # ------------------------------------------------------------------
    def execute_task(self, task: str) -> Optional[str]:
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=self.messages + [{"role": "user", "content": task}],
                max_tokens=1500,
                temperature=0.7,
                top_p=0.9
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return None

    def extract_code(self, response: str) -> Optional[str]:
        if not response:
            return None
        patterns = [
            r'```python\n(.*?)\n```',
            r'```\n(.*?)\n```',
            r'`([^`]+)`'
        ]
        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            if matches:
                return matches[0].strip()
        return None

    def validate_code(self, code: str) -> bool:
        dangerous = [
            r'rm\s+-rf', r'del\s+/[fFsS]', r'format\s+[cC]:',
            r'__import__\s*\(\s*["\']os["\']',
            r'eval\s*\(', r'exec\s*\(',
        ]
        for pattern in dangerous:
            if re.search(pattern, code, re.IGNORECASE):
                return False
        return True

    def run_code(self, code: str) -> str:
        if not code or not self.validate_code(code):
            return ""
        try:
            exec_globals = {
                '__builtins__': __builtins__,
                'print': print,
                'os': os,
                'time': __import__('time'),
                'webbrowser': __import__('webbrowser'),
                'psutil': __import__('psutil'),
            }
            exec(code, exec_globals)
        except Exception:
            pass
        return ""

    def run_task(self, task: str) -> str:
        if not task.strip():
            return ""
        response = self.execute_task(task)
        if not response:
            return ""
        code = self.extract_code(response)
        if not code:
            return ""
        self.run_code(code)
        return ""


# ---------------------------------------------------------------------------
# ContentGenerator — Uses Gemini to write articles / blogs / code to a file
# ---------------------------------------------------------------------------

class ContentGenerator:
    """Generates rich written content using Gemini and saves to Database/Content.txt."""

    def __init__(self, api_key=None):
        load_dotenv()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found. Please set it in .env")

        import google.generativeai as genai   # lazy import — avoid startup warning
        self.genai = genai
        genai.configure(api_key=self.api_key)

        self.generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        os.makedirs("Database", exist_ok=True)

    def generate_content(self, prompt: str, custom_config: dict = None) -> Optional[str]:
        config = {**self.generation_config, **(custom_config or {})}
        try:
            model = self.genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                generation_config=config,
                system_instruction=(
                    "You are JARVIS content module. Generate high-quality content based on the prompt. "
                    "Write articles, blogs, and code clearly and concisely. Use emojis where suitable."
                ),
            )
            chat = model.start_chat(history=[])
            response = chat.send_message(prompt)
            content = response.text

            filepath = os.path.join("Database", "Content.txt")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            self._open_file(filepath)
            return content
        except Exception as e:
            print(f"Content generation error: {e}")
            return None

    def _open_file(self, filepath: str):
        try:
            if os.name == 'nt':
                os.startfile(filepath)
            else:
                subprocess.call(('open', filepath))
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def Coder(topic: str):
    """Generate written content or code on a topic using Gemini."""
    generator = ContentGenerator()
    generator.generate_content(topic)


def RunTask(task: str):
    """Execute an automation task using Groq + code execution."""
    automation = JarvisAutomation()
    automation.run_task(task)
