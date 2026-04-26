from requests import Session
from fastapi import WebSocket, WebSocketDisconnect
from chat.openrouter import openrouter_stream
from models import RAGDocument
from typing import Dict
import json
from sqlalchemy.orm import Session

async def chat_websocket(
    websocket: WebSocket, 
    role: str,
    llm_settings: dict,
    rag_systems: Dict,
    db: Session
    
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

                # ۱. ابتدا باید تنظیمات این گروه را از دیتابیس بخوانید
                # فرض بر این است که متغیر session دیتابیس شما db نام دارد
                rag_setting = db.query(RAGDocument).filter(RAGDocument.group_id == group_id).first()


                # ۲. مقدار top_k را مشخص کنید
                # اگر تنظیمی در دیتابیس وجود داشت، همان را استفاده کن، در غیر این صورت روی 3 تنظیم کن
                dynamic_top_k = rag_setting.top_k if rag_setting and rag_setting.top_k else 3
                print(f'🔍 RAG Enabled for Group {group_id} - Searching...')
                relevant_chunks = rag_systems[group_id].search(
                    query=prompt,
                     top_k=dynamic_top_k
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
            system_instruction = f""" تو یک درمانگر متخصص REBT هستی. وظیفه تو تحلیل متن کاربر و ارائه پاسخی صمیمی، یکپارچه و بدون اصطلاحات فنی است.

            **منطق اصلی برای تو (در تحلیل رعایت کن):**
            - اتفاق (A) علت مستقیم ناراحتی (C) نیست؛ بلکه باور (B) علت اصلی پیامد هیجانی است.
            - احساسات کاربر را هرگز انکار نکن (تأیید کن)، اما روی اصلاح یا تقویت باور (B) تمرکز کن.

            **دستورالعمل پاسخ‌دهی بر اساس نوع باور (B):**
            ۱. اگر باور منطقی (rB) است: احساسات طبیعی‌اش را تأیید کن و یک نتیجه‌گیری سازنده به او بده تا بتواند برای رسیدن به اهدافش اقدام کند.
            ۲. اگر باور غیرمنطقی (iB) است (بایدها یا فاجعه‌سازی): ابتدا با یک سؤال تأملی (که نیازی به جواب کاربر ندارد) باورش را به چالش بکش (مثلاً "با خودت فکر کن آیا واقعاً دنیا به آخر رسیده؟") و سپس **خودت مستقیماً** او را به سمت یک فلسفه جدید، منعطف و آرام‌بخش (E) هدایت کن.

            **الزامات خروجی (بسیار مهم):**
            - **پاسخ تو یک جمع‌بندی نهایی است.** به هیچ وجه در انتهای پیام سؤالی نپرس و کاربر را به ادامه چت دعوت نکن. پیام تو باید به تنهایی کامل، تسکین‌دهنده و پایان‌دهنده مکالمه باشد.
            - به هیچ وجه از کلمات فنی (مثل A، B، C، rB، iB، باور منطقی، خطای شناختی) استفاده نکن.
            - پاسخ باید روان، گرم، یکپارچه و به زبان فارسی محاوره‌ای/دوستانه باشد.

            **دانش استخراج شده از اسناد برای راهنمایی بیشتر:**
            {rag_context}
    

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
