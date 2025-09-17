# Telegram Bot (Whisper + MarianMT + GoEmotions)

This project is a Telegram bot built with **python-telegram-bot**, which supports:

- 🎤 **Voice messages (English/Spanish)**:
  - Automatic **transcription** (Whisper).
  - Automatic **translation** (MarianMT).
  - **Emotion/intent detection** (GoEmotions).

- 💬 **Text messages (English/Spanish)**:
  - Automatic **translation** into the other language.

- 🌍 **i18n / Multilingual UI**:
  - Bot messages can be shown in English or Spanish.
  - Users can select the bot language with `/lang`.

---

## ⚙️ Requirements

- Python 3.10 or later
- [ffmpeg](https://ffmpeg.org/) installed (required for audio decoding)

On macOS (with Homebrew):

```bash
brew install ffmpeg
```

On Windows (using [Chocolatey](https://chocolatey.org/)):

```powershell
choco install ffmpeg
```

Or download from [ffmpeg.org/download](https://ffmpeg.org/download.html) and add it to your PATH.

---

## 📦 Installation


1. Create a virtual environment and activate it:

**macOS / Linux**
```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows CMD**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🚀 Usage

1. Export your Telegram token (from [@BotFather](https://t.me/BotFather)):

**macOS / Linux**
```bash
export TELEGRAM_TOKEN="123456789:ABC-YourTokenHere"
```

**Windows PowerShell**
```powershell
$env:TELEGRAM_TOKEN="123456789:ABC-YourTokenHere"
```

**Windows CMD**
```cmd
set TELEGRAM_TOKEN=123456789:ABC-YourTokenHere
```

2. Run the bot:

```bash
python bot.py
```

---

## 💡 Features

- `/start` → Welcome message  
- `/help` → Show available commands and features  
- `/about` → Bot information  
- `/lang` → Choose the bot interface language  

### Voice messages
Send a voice note (English or Spanish). The bot replies with:
1. **Transcription**
2. **Translation** (into the opposite language)
3. **Emotion detection**

### Text messages
Send text (English or Spanish). The bot replies with:
1. **Your text** with language info
2. **Translation** into the opposite language

---

## 📂 Project structure

```
.
├── bot.py               # Main bot class (BotApp)
├── README.md
└── utils/               # Helper modules
    ├── __init__.py
    ├── config.py        # Token and constants
    ├── i18n.py          # Translations and UI texts
    ├── asr_translate.py # Whisper + MarianMT helpers
    └── emotions.py      # GoEmotions helper
```

---

## 🧩 Tech stack

- [python-telegram-bot v21](https://docs.python-telegram-bot.org/)
- [faster-whisper](https://github.com/guillaumekln/faster-whisper)
- [Hugging Face MarianMT](https://huggingface.co/Helsinki-NLP/opus-mt-en-es)
- [GoEmotions (RoBERTa)](https://huggingface.co/SamLowe/roberta-base-go_emotions)
- [langdetect](https://pypi.org/project/langdetect/)
