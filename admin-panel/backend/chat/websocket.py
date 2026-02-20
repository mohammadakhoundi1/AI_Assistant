from fastapi import WebSocket, WebSocketDisconnect
from chat.openrouter import openrouter_stream
from typing import Dict
import json

async def chat_websocket(
    websocket: WebSocket, 
    role: str,
    llm_settings: dict,
    rag_systems: Dict[int, 'RAGSystem'] = None
):
    """
    WebSocket Handler with RAG support (only for Group 7)
    """
    await websocket.accept()
    print(f'📡 WebSocket Connected - Role: {role}')
    print(f'⚙️ LLM Settings: {llm_settings}')

    try:
        # --- [Universal JSON Receive & Backwards Text Fallback] ---
        try:
            data = await websocket.receive_json()
        except Exception:
            text_data = await websocket.receive_text()
            try:
                data = json.loads(text_data)
            except Exception:
                data = {"prompt": text_data, "group_id": None}

        prompt = data.get("prompt")
        group_id = data.get("group_id")

        print(f'💬 User Prompt: {prompt[:100]}...')
        print(f'👥 Group ID from client: {group_id} | Role: {role}')

        # Final group_id fallback if missing (from ws path/role)
        if group_id is None and role.startswith("group_"):
            try:
                group_id = int(role.split("_")[1])
            except Exception:
                group_id = None

        # ----------- RAG Context Build (GROUP 7 ONLY) -------------
        rag_context = None
        if rag_systems and group_id == 7 and group_id in rag_systems:
            try:
                print(f'🔍 RAG Enabled for Group {group_id} - Searching...')
                relevant_chunks = rag_systems[group_id].search(
                    query=prompt,
                    # top_k=1
                )
                if relevant_chunks:
                    rag_context = "\n\n---\n\n".join(relevant_chunks)
                    print(f'✅ Found {len(relevant_chunks)} documents')
                    print('relevant chunks',relevant_chunks)

                    await websocket.send_json({
                        "type": "info",
                        "content": f"📚 {len(relevant_chunks)} سند مرتبط پیدا شد و به پاسخ اضافه می‌شود..."
                    })
                else:
                    print('⚠️ No relevant chunks found')
                    await websocket.send_json({
                        "type": "info",
                        "content": "ℹ️ سند مرتبطی پیدا نشد، پاسخ بدون استفاده از اسناد داده می‌شود."
                    })
            except Exception as e:
                print(f'❌ RAG Error: {e}')
                await websocket.send_json({
                    "type": "warning",
                    "content": f"⚠️ خطا در جستجوی اسناد: {str(e)}"
                })

        # ----------- PROMPT Finalization --------------------
        final_prompt = prompt

        if rag_context:
            system_instruction = f"""شما یک دستیار هوشمند هستید که باید بر اساس اسناد و اطلاعات زیر به سوال کاربر پاسخ دهید.

            📚 **اطلاعات مرتبط از اسناد:**

            {rag_context}

            ---

            🎯 **دستورالعمل‌ها:**
            -  از اطلاعات موجود در اسناد بالا استفاده کنید
            - اگر پاسخ در اسناد نیست، صریحاً بگویید که "این اطلاعات در اسناد موجود نیست"
            - پاسخ را به زبان فارسی و کامل بدهید
           

            ---

            ❓ **سوال کاربر:**
            {prompt}"""
            final_prompt = system_instruction
            print('📝 RAG Context added to prompt')
            print('final prompt',final_prompt)

        # ----------- CALL LLM STREAM -----------------------
        sent_anything = False
        async for token in openrouter_stream(final_prompt, role, llm_settings):
            sent_anything = True
            await websocket.send_json({
                "type": "token",
                "content": token
            })

        if not sent_anything:
            await websocket.send_json({
                "type": "error",
                "content": "❌ پاسخی از مدل دریافت نشد"
            })

        await websocket.send_json({"type": "end"})
        print('✅ Response completed successfully')

    except WebSocketDisconnect:
        print("🔌 Client disconnected")

    except Exception as e:
        print(f"❌ WebSocket Error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "content": f"❌ خطای سرور: {str(e)}"
            })
        except:
            pass

    finally:
        try:
            await websocket.close()
            print('🔒 WebSocket closed')
        except:
            pass
