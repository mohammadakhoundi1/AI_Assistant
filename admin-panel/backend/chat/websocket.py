from fastapi import WebSocket, WebSocketDisconnect
from chat.openrouter import openrouter_stream
import json

async def chat_websocket(websocket: WebSocket, role: str):
    await websocket.accept()

    try:
        prompt = await websocket.receive_text()

        sent_anything = False

        async for token in openrouter_stream(prompt, role):
            sent_anything = True
            # ✅ ارسال توکن به صورت JSON
            await websocket.send_json({
                "type": "token",
                "content": token
            })

        if not sent_anything:
            # ✅ ارسال خطا به صورت JSON
            await websocket.send_json({
                "type": "error",
                "content": "❌ پاسخی از مدل دریافت نشد"
            })

        # ✅ سیگنال پایان به صورت JSON
        await websocket.send_json({
            "type": "end"
        })

    except WebSocketDisconnect:
        print("client disconnected")

    finally:
        await websocket.close()
