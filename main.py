from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from google import genai  # ← الـ import الصحيح للـ SDK الجديد
import os
import shutil
from typing import List
import uvicorn

app = FastAPI(title="🧬 Dr. GeneX API - Persistent Session")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# استخدمي environment variable مش hard-code الـ key (أمان أكتر على السيرفر)
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY غير موجود في الـ environment variables!")

client = genai.Client(api_key=API_KEY)

chat_history = []

uploaded_files_dir = "uploads"
os.makedirs(uploaded_files_dir, exist_ok=True)


@app.get("/")
async def root():
    return {"message": "🧬 Dr. GeneX API شغال - السيشن مفتوحة تلقائي"}


@app.post("/chat")
async def chat(user_input: str):
    global chat_history
    chat_history.append({"role": "user", "content": user_input})

    # آخر 6 رسائل بس عشان الـ context ما يبقاش طويل أوي
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history[-6:]])

    prompt = f"""
أنت دكتور جين إكس، كوتش جيني ودود جدًا.
رد بالعامية المصرية لو اليوزر كتب عامية، فصحى لو فصحى، إنجليزي لو إنجليزي.
استخدم إيموجي طبيعي.
ادمج نصايح أكل ورياضة وصحة نفسية.
ممنوع تشخيص طبي أبدًا، دايمًا قول استشر طبيب.
الذاكرة السابقة:
{history_text}
السؤال الجديد: {user_input}
"""

    try:
        # الطريقة الصحيحة في الـ SDK الجديد
        response = client.models.generate_content(
            model="models/gemini-1.5-flash",  # أو gemini-1.5-pro أو أي موديل تاني
            contents=[{"role": "user", "parts": [{"text": prompt}]}]
        )
        reply = response.candidates[0].content.parts[0].text.strip()

        chat_history.append({"role": "assistant", "content": reply})
        return {"reply": reply, "history_length": len(chat_history)}

    except Exception as e:
        return {"error": str(e)}


@app.post("/upload")
async def upload_file(files: List[UploadFile] = File(...)):
    saved_files = []
    for file in files:
        file_path = os.path.join(uploaded_files_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(f"تم رفع: {file.filename} بنجاح")
    return {"status": "success", "files": saved_files}


@app.get("/history")
async def get_history():
    return {"history": chat_history}


if __name__ == "__main__":
    print("🚀 Dr. GeneX API شغال - السيشن مفتوحة تلقائي وهتفضل كده طول الوقت")
    uvicorn.run(app, host="0.0.0.0", port=8000)