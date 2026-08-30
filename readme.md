# 🦅 Jarvis Falcon AI Assistant

> **High-performance AI assistant integrating Falcon LLM inference, local speech recognition, database logging, and web command interface.**

---

## ✨ Features

- 🦅 **Falcon LLM Integration**
  - Connects to Falcon LLM / HuggingFace Inference models for low-latency reasoning and chat responses.
- 🎙️ **Speech & Audio Pipeline**
  - Integrated speech recognition and pyttsx3 text-to-speech audio feedback.
- 🗄️ **Local Database & History**
  - Local database tracking chat interactions, system activity, and user preferences.
- 🌐 **Web Control Dashboard** (`web/`)
  - Web UI for monitoring assistant status and issuing voice/text commands.

---

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **Speech**: `SpeechRecognition`, `pyttsx3`, `PyAudio`
- **Backend API**: Flask / Express (Web interface)
- **AI Gateway**: HuggingFace API / Falcon LLM

---

## 🚀 Getting Started

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Omkar4812x/Jarvis-Falcon.git
   cd Jarvis-Falcon
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   HUGGINGFACE_API_KEY=your_huggingface_key_here
   ```

4. **Run Jarvis Falcon**:
   ```bash
   python Jarvis.py
   ```

---

## 📄 License

Distributed under the MIT License.
