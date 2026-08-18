# 🧑‍🏫 Code Tutor Bot

An AI chatbot that teaches code **line by line**. Upload a file or paste
code, pick your level and language, and it walks you through every
block like a patient tutor — plus complexity analysis, a bug/quality
review, a comprehension quiz, and a follow-up Q&A chat grounded in
your actual code.

## Features

| Feature | What it does |
|---|---|
| 📖 Line-by-line teaching | Splits code into logical blocks, explains each, step-through UI with Prev/Next |
| ⏱️ Complexity analysis | Time/space Big-O per function, with justification |
| 🐛 Bug & improvement review | Prioritized (Critical/Moderate/Minor) code review |
| 🧠 Quiz Me | Auto-generated comprehension quiz with instant feedback and score |
| 💬 Ask Questions | Follow-up chat grounded in the uploaded code |
| 🌐 Bilingual | Explanations in English, Bengali (বাংলা), or both |
| 🎚️ Level slider | Absolute Beginner → Advanced |
| 📥 Export | Download the whole session as a Markdown report |
| 🔁 Swappable provider | Groq (default, free & fast) or Mistral — one line in `.env` |

## Setup

### 1. Get a free API key
- **Groq** (default, recommended): https://console.groq.com/keys
- **Mistral** (optional alternative): https://console.mistral.ai/api-keys

### 2. Configure your `.env`
Rename `.env.example` to `.env` and paste your key in. **Never commit
this file** — `.gitignore` already excludes it.

```
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
```

### 3. Install & run

**Windows (Command Prompt)** — avoids the PowerShell execution-policy
issue with venv activation:
```cmd
cd code-explainer-bot
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
streamlit run app.py
```

**Windows (Git Bash)**:
```bash
cd code-explainer-bot
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
streamlit run app.py
```

**macOS / Linux**:
```bash
cd code-explainer-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Switching to Mistral

Just change two lines in `.env`:
```
LLM_PROVIDER=mistral
MISTRAL_API_KEY=your_key_here
```
No code changes needed — `llm_client.py` routes to whichever provider
`LLM_PROVIDER` names.

## Project structure

```
code-explainer-bot/
├── app.py            # Streamlit UI — all 6 tabs/features
├── llm_client.py      # Unified Groq/Mistral API wrapper
├── utils.py           # Language detection, chunking, Markdown export
├── requirements.txt
├── .env.example        # Template — copy to .env and fill in your key
└── .gitignore
```

## Notes on the model choice

Groq deprecated `llama-3.1-8b-instant` / `llama-3.3-70b-versatile` for
new integrations, so this defaults to `openai/gpt-oss-120b` (Groq's
current recommended general-purpose model). If you hit rate limits on
the free tier, drop to `openai/gpt-oss-20b` in `.env` — it's faster
and lighter, at a small quality cost for very large files.

## Ideas for extending this further
- Cache line-by-line explanations by file hash so re-uploading the same file doesn't re-call the API
- Add a "diff mode" — paste two versions of a function and explain what changed and why
- Voice narration of explanations (e.g. via a free TTS API)
- A GitHub URL input to explain a whole repo file by file
