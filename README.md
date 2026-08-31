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

## Deploying to Render (Docker)

This repo includes a `Dockerfile` and `.dockerignore` for container
deployment. `.env` is excluded from the image on purpose — Render
injects your keys as environment variables at runtime instead, the
same way Streamlit Cloud uses Secrets. `llm_client.py`'s `_get_setting()`
already falls back to `os.getenv(...)`, so this works with zero code changes.

1. Push this folder (including `Dockerfile` and `.dockerignore`) to a GitHub repo
2. On https://dashboard.render.com, **New → Web Service**, connect the repo
3. Render should auto-detect the `Dockerfile`; if asked, set:
   - **Environment**: Docker
   - **Region/Instance**: your choice (free tier works fine for testing)
4. Under **Environment → Environment Variables**, add the same keys as your `.env`:
   | Key | Value |
   |---|---|
   | `LLM_PROVIDER` | `groq` |
   | `GROQ_API_KEY` | `gsk_xxxxxxxxxxxxxxxxxxxx` |
   | `GROQ_MODEL` | `openai/gpt-oss-120b` |

   Do **not** set `PORT` — Render sets it automatically and the
   Dockerfile's `CMD` reads it.
5. Deploy. Render builds the image from the Dockerfile and starts the container.

To test the same image locally first:
```bash
docker build -t code-tutor-bot .
docker run -p 8501:8501 -e GROQ_API_KEY=gsk_xxx -e LLM_PROVIDER=groq code-tutor-bot
```
Then open `http://localhost:8501`.

## Deploying to Streamlit Community Cloud

`.env` is gitignored on purpose, so it never reaches the server. Use
Streamlit's built-in **Secrets** panel instead — `llm_client.py`
already checks `st.secrets` first, so no code changes are needed.

1. Push this folder to a GitHub repo (`.env` won't be included — that's correct)
2. On https://share.streamlit.io, create a new app pointing at `app.py`
3. In the app's **Settings → Secrets**, paste the same keys as your `.env`, in TOML format:
   ```toml
   LLM_PROVIDER = "groq"
   GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxxxxxx"
   GROQ_MODEL = "openai/gpt-oss-120b"
   ```
4. Deploy. That's it — locally it reads `.env`, on Cloud it reads Secrets, same code either way.

You never need to create a `secrets.toml` file yourself — Streamlit
Cloud generates and stores it for you from what you paste into the
Secrets panel. (If you ever want to test cloud-style secrets locally,
you *can* create `.streamlit/secrets.toml` with the same TOML — it's
already in `.gitignore` too.)

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
