import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

URL = "https://openrouter.ai/api/v1/chat/completions"
print("OPENROUTER_API_KEY =",OPENROUTER_API_KEY)


HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "text/event-stream",

    # ✅ OpenRouter REQUIRED
    "HTTP-Referer": "http://localhost:5173",
    "X-Title": "Student Dashboard",
}

async def openrouter_stream(prompt: str, role: str):
    payload = {
        "model": "openai/gpt-4o-mini",
        "stream": True,
        "temperature": 0.4,
        "max_tokens": 4096,
        "messages": [
            {
                "role": "system",
                "content": f"You are a Persian educational assistant for {role}."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            URL,
            headers=HEADERS,
            json=payload
        ) as response:

            # 🔴 IMPORTANT: non-200 response
            if response.status_code != 200:
                raw = await response.aread()
                yield (
                    f"\n❌ OpenRouter HTTP {response.status_code}\n"
                    f"{raw.decode(errors='ignore')}\n"
                )
                return

            async for line in response.aiter_lines():
                if not line:
                    continue

                if not line.startswith("data:"):
                    
                    continue

                data = line.replace("data:", "").strip()

                if data == "[DONE]":
                    break

                try:
                    chunk = json.loads(data)

                    # 🔴 REAL OpenRouter error object
                    if "error" in chunk:
                        yield (
                            "\n❌ OpenRouter Error:\n"
                            f"{json.dumps(chunk['error'], indent=2, ensure_ascii=False)}\n"
                        )
                        return

                    # ✅ normal streaming token
                    choice = chunk.get("choices", [{}])[0]
                    delta = choice.get("delta", {})

                    if "content" in delta:
                        yield delta["content"]

                except json.JSONDecodeError as e:
                    yield f"\n❌ JSON PARSE ERROR: {e}\nRAW: {data}\n"
