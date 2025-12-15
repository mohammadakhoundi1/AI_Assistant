import httpx
import json

URL = "https://openrouter.ai/api/v1/chat/completions"


async def openrouter_stream(prompt: str, role: str, llm_settings: dict):
    

    api_key = llm_settings.get("api_key")
    model = llm_settings.get("model_name", "openai/gpt-4o-mini")
    temperature = llm_settings.get("temperature", 0.4)
    max_tokens = llm_settings.get("max_tokens", 457)

    if not api_key:
        yield "❌ API key is missing"
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",

        # ✅ OpenRouter REQUIRED
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "Student Dashboard",
    }

    payload = {
        "model": model,
        "stream": True,
        "temperature": temperature,
        "max_tokens": max_tokens,
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
            headers=headers,
            json=payload
        ) as response:

            # 🔴 non-200 response
            if response.status_code != 200:
                raw = await response.aread()
                yield (
                    f"\n❌ OpenRouter HTTP {response.status_code}\n"
                    f"{raw.decode(errors='ignore')}\n"
                )
                return

            async for line in response.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue

                data = line.replace("data:", "").strip()

                if data == "[DONE]":
                    break

                try:
                    chunk = json.loads(data)

                    # 🔴 OpenRouter structured error
                    if "error" in chunk:
                        yield (
                            "\n❌ OpenRouter Error:\n"
                            f"{json.dumps(chunk['error'], indent=2, ensure_ascii=False)}\n"
                        )
                        return

                    choice = chunk.get("choices", [{}])[0]
                    delta = choice.get("delta", {})

                    if "content" in delta:
                        yield delta["content"]

                except json.JSONDecodeError as e:
                    yield f"\n❌ JSON PARSE ERROR: {e}\nRAW: {data}\n"
