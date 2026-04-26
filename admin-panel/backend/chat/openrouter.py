import httpx
import json


async def openrouter_stream(prompt: str, role: str, llm_settings: dict):
    """
    Streams LLM response using httpx with admin-configured settings
    """

    api_key = llm_settings.get("api_key")
    base_url = llm_settings.get("base_url", "https://api.gapgpt.app/v1")
    model = llm_settings.get("model_name", "gpt-4o")
    temperature = llm_settings.get("temperature", 0.4)
    max_tokens = llm_settings.get("max_tokens", 4096)

    if not api_key:
        yield "❌ API key is missing"
        return

    # ensure base_url ends clean, append chat completions path
    url = f"{base_url.rstrip('/')}/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
        "messages": [
            {"role": "system", "content": f"You are a Persian educational assistant for {role}."},
            {"role": "user", "content": prompt},
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    yield f"\n❌ خطا از سرور ({response.status_code}): {body.decode()}\n"
                    return

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    data = line[6:]  # strip "data: "

                    if data.strip() == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data)
                        content = chunk["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    except httpx.TimeoutException:
        yield "\n❌ زمان اتصال به سرور به پایان رسید\n"
    except Exception as e:
        yield f"\n❌ خطا در ارتباط با مدل: {str(e)}\n"
