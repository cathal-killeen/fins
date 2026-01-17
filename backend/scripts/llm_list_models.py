"""
List available models for the configured LLM provider.
"""

import json
import os
import sys

import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings


def list_gemini(api_key: str) -> None:
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()

    data = response.json()
    models = data.get("models", [])
    if not models:
        print("No models returned.")
        print(json.dumps(data, indent=2))
        return

    print("Available models (Gemini):")
    for model in models:
        name = model.get("name")
        methods = model.get("supportedGenerationMethods", [])
        print(f"- {name} (methods: {', '.join(methods) if methods else 'none'})")


def list_openai(api_key: str) -> None:
    base = settings.LLM_API_BASE or "https://api.openai.com/v1"
    response = httpx.get(
        f"{base}/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30.0,
    )
    response.raise_for_status()
    data = response.json()
    models = data.get("data", [])

    if not models:
        print("No models returned.")
        print(json.dumps(data, indent=2))
        return

    print("Available models (OpenAI):")
    for model in models:
        model_id = model.get("id")
        if model_id:
            print(f"- {model_id}")


def list_ollama() -> None:
    base = settings.LLM_API_BASE or "http://localhost:11434"
    response = httpx.get(f"{base}/api/tags", timeout=30.0)
    response.raise_for_status()
    data = response.json()
    models = data.get("models", [])

    if not models:
        print("No models returned.")
        print(json.dumps(data, indent=2))
        return

    print("Available models (Ollama):")
    for model in models:
        name = model.get("name")
        if name:
            print(f"- {name}")


def main() -> None:
    provider = (settings.LLM_PROVIDER or "").lower()
    api_key = settings.LLM_API_KEY

    if provider in {"google", "gemini"}:
        if not api_key:
            raise SystemExit("LLM_API_KEY is not set.")
        list_gemini(api_key)
        return

    if provider == "openai":
        if not api_key:
            raise SystemExit("LLM_API_KEY is not set.")
        list_openai(api_key)
        return

    if provider == "ollama":
        list_ollama()
        return

    print(f"Model listing is not implemented for provider: {provider}")
    print("Supported providers: google/gemini, openai, ollama")
    print("If you're using a custom API base, set LLM_API_BASE in backend/.env.")


if __name__ == "__main__":
    main()
