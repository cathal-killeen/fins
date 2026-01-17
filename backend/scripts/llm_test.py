"""
Simple LLM connectivity test using current settings.
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.ai_service import llm_service


async def main() -> None:
    messages = [
        {
            "role": "user",
            "content": (
                "Return a JSON object with a single key named 'ok' set to true. "
                "Return JSON only, no markdown or code fences."
            ),
        }
    ]
    try:
        response = await llm_service.complete(messages, temperature=0.0, max_tokens=64)
    except Exception as exc:
        print(f"LLM test failed: {exc}")
        raise

    print("LLM test response (raw):")
    print(repr(response))

    normalized = response.strip()
    if normalized.startswith("```"):
        normalized = normalized.strip("`")
        if normalized.lower().startswith("json"):
            normalized = normalized[4:].lstrip()

    # Best-effort JSON parse for quick verification.
    try:
        parsed = json.loads(normalized)
        print("Parsed JSON:", parsed)
    except json.JSONDecodeError:
        print("Warning: response was not valid JSON.")


if __name__ == "__main__":
    asyncio.run(main())
