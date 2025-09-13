from fastapi import FastAPI, File, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from io import BytesIO
from docx import Document
import PyPDF2
import ollama  # Make sure you have the Ollama SDK installed and configured

# ------------------------------
# FastAPI app
# ------------------------------
app = FastAPI(title="Document Chat API")

# ------------------------------
# CORS settings
# ------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------
# Global variables
# ------------------------------
DOCUMENT_CONTEXT = ""
CONVERSATION_HISTORY = []

# ------------------------------
# Pydantic model for chat input
# ------------------------------
class ChatRequest(BaseModel):
    prompt: str

# ------------------------------
# Upload document endpoint
# ------------------------------
@app.post("/api/upload")
async def upload_doc(file: UploadFile = File(...)):
    """
    Upload .txt, .docx, or .pdf and store text content.
    """
    global DOCUMENT_CONTEXT, CONVERSATION_HISTORY
    content = await file.read()
    filename = file.filename.lower()

    if filename.endswith(".docx"):
        doc = Document(BytesIO(content))
        text = "\n".join([p.text for p in doc.paragraphs])
    elif filename.endswith(".pdf"):
        pdf_reader = PyPDF2.PdfReader(BytesIO(content))
        text = "\n".join([page.extract_text() or "" for page in pdf_reader.pages])
    else:
        text = content.decode("utf-8")

    DOCUMENT_CONTEXT = text
    CONVERSATION_HISTORY.clear()  # Reset conversation when a new document is uploaded

    return {
        "message": f"Document '{file.filename}' uploaded successfully!",
        "length": len(text)
    }

# ------------------------------
# Chat endpoint
# ------------------------------
@app.post("/api/chat")
async def chat(data: ChatRequest = Body(...)):
    """
    Chat endpoint that uses Ollama.
    If a document is uploaded, it will be used as context.
    Otherwise, it will respond based on the user prompt only.
    Always uses streaming mode.
    """
    global DOCUMENT_CONTEXT, CONVERSATION_HISTORY
    user_input = data.prompt

    # Build messages for Ollama
    messages = [{"role": "system", "content": "You are DeepCoder, a helpful coding assistant."}]

    if DOCUMENT_CONTEXT:
        messages.append({
            "role": "user",
            "content": f"Here is the document text:\n{DOCUMENT_CONTEXT}\n\nNow, answer my question based on this document."
        })

    # Add conversation history
    messages += CONVERSATION_HISTORY
    # Add current user prompt
    messages.append({"role": "user", "content": user_input})

    try:
        # Always streaming
        response_stream = ollama.chat(model="deepseek-coder:6.7b", messages=messages, stream=True)
        full_text = ""
        for partial in response_stream:
            if hasattr(partial, "message") and partial.message.content:
                full_text += partial.message.content

        assistant_reply = full_text

        # Save conversation history
        CONVERSATION_HISTORY.append({"role": "user", "content": user_input})
        CONVERSATION_HISTORY.append({"role": "assistant", "content": assistant_reply})

        return {"response": assistant_reply}

    except Exception as e:
        return {"error": str(e)}
