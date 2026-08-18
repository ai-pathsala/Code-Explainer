"""
llm_client.py
--------------
Thin wrapper around Groq and Mistral chat-completion APIs.
Both are OpenAI-compatible REST APIs, so one function handles both —
the active provider is chosen via the LLM_PROVIDER setting.

Nothing here ever asks the user for a key at runtime. Keys are read
from (in order of priority):
  1. st.secrets   — used automatically on Streamlit Community Cloud,
                     where you paste keys into the app's Secrets panel
  2. .env / os.environ — used for local runs (loaded via python-dotenv)
No code changes are needed to move between local and cloud — just set
the values in whichever place applies.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()


def _get_setting(key: str, default: str = "") -> str:
    """Checks Streamlit secrets first (cloud deploys), then env vars (local .env)."""
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass  # st.secrets raises if no secrets.toml exists at all — that's fine locally
    return os.getenv(key, default)


# ---- Provider configuration (never hardcoded — see _get_setting above) ----
PROVIDER = _get_setting("LLM_PROVIDER", "groq").strip().lower()

GROQ_API_KEY = _get_setting("GROQ_API_KEY", "")
GROQ_MODEL = _get_setting("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

MISTRAL_API_KEY = _get_setting("MISTRAL_API_KEY", "")
MISTRAL_MODEL = _get_setting("MISTRAL_MODEL", "mistral-large-latest")
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"


class LLMError(RuntimeError):
    pass


def active_provider_info():
    """Returns a small dict describing the currently configured provider."""
    if PROVIDER == "groq":
        return {"provider": "Groq", "model": GROQ_MODEL, "key_present": bool(GROQ_API_KEY)}
    elif PROVIDER == "mistral":
        return {"provider": "Mistral", "model": MISTRAL_MODEL, "key_present": bool(MISTRAL_API_KEY)}
    else:
        return {"provider": PROVIDER, "model": "unknown", "key_present": False}


def chat_completion(messages, temperature=0.3, max_tokens=2000, json_mode=False):
    """
    messages: list of {"role": "system"|"user"|"assistant", "content": str}
    json_mode: if True, asks the API to return a valid JSON object only.
    Returns the assistant's text content (str).
    """
    if PROVIDER == "groq":
        if not GROQ_API_KEY:
            raise LLMError(
                "GROQ_API_KEY is missing. Add it to your .env file (see .env.example)."
            )
        url, model, key = GROQ_URL, GROQ_MODEL, GROQ_API_KEY
    elif PROVIDER == "mistral":
        if not MISTRAL_API_KEY:
            raise LLMError(
                "MISTRAL_API_KEY is missing. Add it to your .env file (see .env.example)."
            )
        url, model, key = MISTRAL_URL, MISTRAL_MODEL, MISTRAL_API_KEY
    else:
        raise LLMError(f"Unknown LLM_PROVIDER '{PROVIDER}'. Use 'groq' or 'mistral'.")

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=90)
    except requests.exceptions.RequestException as e:
        raise LLMError(f"Network error calling {PROVIDER}: {e}") from e

    if resp.status_code != 200:
        raise LLMError(f"{PROVIDER} API error {resp.status_code}: {resp.text[:500]}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise LLMError(f"Unexpected response shape from {PROVIDER}: {data}") from e


def chat_completion_json(messages, temperature=0.2, max_tokens=3000):
    """Same as chat_completion but parses and returns JSON (dict/list)."""
    raw = chat_completion(messages, temperature=temperature, max_tokens=max_tokens, json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Some models wrap JSON in markdown fences despite instructions — strip and retry.
        cleaned = raw.strip().strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
        return json.loads(cleaned)
