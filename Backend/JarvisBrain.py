import os
import sys
import json
import datetime
import sqlite3
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# Import JARVIS components
from Backend.SystemControl import SystemController
from Backend.JarvisAutomation import Coder
from Backend.ImageGen import Main as ImageGenMain
from Backend.Logger import logger

# Context Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")

client = OpenAI(
    base_url="https://api.groq.com/openai/v1", 
    api_key=API_KEY
)


class JarvisDatabase:
    """Handles JARVIS memory and conversation history"""
    
    def __init__(self, db_path='Database/JARVIS.db'):
        self.db_path = db_path
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self.init_database()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                assistant TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            conn.commit()

    def add_memory(self, user_message, assistant_message=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO memory (user, assistant) VALUES (?, ?)', (user_message, assistant_message))
            conn.commit()
            return cursor.lastrowid

    def update_memory(self, memory_id, assistant_message):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE memory SET assistant = ? WHERE id = ?', (assistant_message, memory_id))
            conn.commit()

    def get_recent_memory(self, limit=8):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user, assistant FROM memory WHERE assistant IS NOT NULL ORDER BY timestamp ASC LIMIT ?', (limit,))
            messages = []
            for user_msg, assistant_msg in cursor.fetchall():
                messages.append({"role": "user", "content": user_msg})
                messages.append({"role": "assistant", "content": assistant_msg})
            return messages


class JarvisCore:
    """The central AI brain of JARVIS"""
    
    def __init__(self):
        self.db = JarvisDatabase()
        
        # Define OS Tools for LLM
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "control_system",
                    "description": "Execute OS level tasks: open/close apps, shutdown, search internet, open websites.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["open_app", "close_app", "search_internet", "open_website", "shutdown", "restart", "volume_adjust"],
                                "description": "System action to perform."
                            },
                            "target": {
                                "type": "string",
                                "description": "App name, website URL, or search query. (e.g., 'chrome', 'youtube.com', 'python tutorials')"
                            }
                        },
                        "required": ["action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_media",
                    "description": "Generate images from a prompt.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The image description."
                            }
                        },
                        "required": ["prompt"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_code",
                    "description": "Write a python script or code block.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "Coding request description."
                            }
                        },
                        "required": ["prompt"]
                    }
                }
            }
        ]
        
        self.system_prompt = """
You are JARVIS, an advanced, highly intelligent AI assistant designed by Tony Stark.
Your personality is professional, highly intelligent, concise, and occasionally British/polite. Address the user as "sir" occasionally.
Keep responses SHORT — maximum 1-2 sentences. Do not ramble. Do not explain what you are doing in detail.
You have tools to control the PC. ALWAYS use tools when the user asks to open an app, website, or search the internet. Never simulate or fake tool calls using text tags.
NEVER output raw function calls or XML tags like <function=...> in your response. Use your tools API properly.
Example:
User: "Jarvis open Chrome" -> Use control_system tool, reply: "Opening Chrome, sir."
User: "Jarvis search for weather" -> Use control_system tool, reply: "Searching now, sir."
"""

    def handle_tool(self, tool_call):
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        logger.command(f"Executing {name} with args: {args}")
        
        if name == "control_system":
            action = args.get("action")
            target = args.get("target", "")
            if action == "open_app":
                SystemController.open_application(target)
                return f"Opened {target}"
            elif action == "close_app":
                SystemController.close_application(target)
                return f"Closed {target}"
            elif action == "search_internet":
                SystemController.search_internet(target)
                return f"Searched for {target}"
            elif action == "open_website":
                SystemController.open_website(target)
                return f"Opened website {target}"
            elif action == "shutdown":
                SystemController.shutdown()
                return "Initiated shutdown"
            elif action == "restart":
                SystemController.restart()
                return "Initiated restart"
            elif action == "volume_adjust":
                SystemController.control_volume(target)
                return "Adjusted volume"
                
        elif name == "generate_media":
            ImageGenMain(args.get("prompt", ""))
            return "Image generated locally."
            
        elif name == "generate_code":
            Coder(args.get("prompt", ""))
            return "Code generated locally."
            
        return "Tool execution failed."

    def process_command(self, user_input: str) -> str:
        """Processes the command through the JARVIS brain"""
        logger.info(f"User Input: {user_input}")
        
        memory_id = self.db.add_memory(user_input)
        recent_memory = self.db.get_recent_memory()
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"Current Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
        ] + recent_memory + [{"role": "user", "content": user_input}]

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                max_tokens=200,
                temperature=0.5
            )
            
            resp_msg = response.choices[0].message
            
            if resp_msg.tool_calls:
                tool_results_msgs = []
                for tool_call in resp_msg.tool_calls:
                    res = self.handle_tool(tool_call)
                    tool_results_msgs.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": res
                    })
                
                messages.append({
                    "role": "assistant",
                    "content": resp_msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in resp_msg.tool_calls
                    ]
                })
                
                messages.extend(tool_results_msgs)
                
                final_response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    max_tokens=200,
                    temperature=0.5
                )
                answer = final_response.choices[0].message.content.strip()
            else:
                answer = resp_msg.content.strip()
            
            # Clean up any leaked function tags from the response
            import re
            answer = re.sub(r'<function=.*?</function>', '', answer, flags=re.DOTALL).strip()
            answer = re.sub(r'<function=.*?}>', '', answer, flags=re.DOTALL).strip()
            if not answer:
                answer = "Done, sir."
                
            self.db.update_memory(memory_id, answer)
            logger.info(f"Jarvis Output: {answer}")
            return answer
            
        except Exception as e:
            err = f"Brain error: {str(e)}"
            logger.error(err)
            self.db.update_memory(memory_id, err)
            return "I apologize sir, I encountered a temporary logic fault."
