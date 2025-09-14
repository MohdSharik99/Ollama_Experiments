from fastapi import FastAPI, File, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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
# Chat endpoint (streaming)
# ------------------------------
@app.post("/api/chat")
async def chat(data: ChatRequest = Body(...)):
    """
    Chat endpoint that uses Ollama.
    If a document is uploaded, it will be used as context.
    Otherwise, it will respond based on the user prompt only.
    Uses StreamingResponse for token-by-token output.
    """
    global DOCUMENT_CONTEXT, CONVERSATION_HISTORY
    user_input = data.prompt

    # Build messages for Ollama
    messages = [
        {"role": "system", "content": "You are DeepCoder, a helpful coding assistant."}
    ]

    if DOCUMENT_CONTEXT:
        messages.append({
            "role": "system",
            "content": f"The user has uploaded a document. Use the following text as context when answering questions:\n\n{DOCUMENT_CONTEXT}"
        })

    # Add conversation history
    messages += CONVERSATION_HISTORY
    # Add current user prompt
    messages.append({"role": "user", "content": user_input})

    def generate():
        full_text = ""
        try:
            for partial in ollama.chat(model="deepseek-coder:6.7b", messages=messages, stream=True):
                if hasattr(partial, "message") and partial.message.content:
                    chunk = partial.message.content
                    full_text += chunk
                    yield chunk  # send chunk immediately to client
            # Save conversation history once finished
            CONVERSATION_HISTORY.append({"role": "user", "content": user_input})
            CONVERSATION_HISTORY.append({"role": "assistant", "content": full_text})
        except Exception as e:
            yield f"⚠️ Error: {str(e)}"

    return StreamingResponse(generate(), media_type="text/plain")
