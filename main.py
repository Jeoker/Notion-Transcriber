import os
import shutil
import tempfile
import secrets
import base64
import binascii
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services import ai_service, notion_service

app = FastAPI(title="AI Logger")

class BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth if env vars are not set
        username = os.getenv("AUTH_USERNAME")
        password = os.getenv("AUTH_PASSWORD")
        
        if not username or not password:
            return await call_next(request)

        # Helper to send 401
        def unauthorized():
            return Response(
                headers={"WWW-Authenticate": "Basic"},
                status_code=401,
                content="Unauthorized"
            )

        auth_header = request.headers.get("Authorization")
        if not auth_header:
             return unauthorized()

        try:
            scheme, credentials = auth_header.split()
            if scheme.lower() != 'basic':
                return unauthorized()
                
            decoded = base64.b64decode(credentials).decode("ascii")
            u, p = decoded.split(":", 1)
            
            # Use secrets.compare_digest to prevent timing attacks
            is_correct_username = secrets.compare_digest(u, username)
            is_correct_password = secrets.compare_digest(p, password)
            
            if not (is_correct_username and is_correct_password):
                 return unauthorized()
                 
        except (ValueError, binascii.Error):
            return unauthorized()

        return await call_next(request)

app.add_middleware(BasicAuthMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.post("/api/process-audio")
async def process_audio(
    audio: UploadFile = File(...),
    mode: str = Form(...)
):
    try:
        # Determine suffix from original filename or default to .webm
        suffix = os.path.splitext(audio.filename)[1] if audio.filename else ".webm"
        if not suffix:
            suffix = ".webm"

        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
            shutil.copyfileobj(audio.file, temp_audio)
            temp_path = temp_audio.name
            
        # DEBUG: Save a copy to debug_uploads to verify audio content
        # debug_dir = "debug_uploads"
        # os.makedirs(debug_dir, exist_ok=True)
        # import time
        # timestamp = int(time.time())
        # debug_path = os.path.join(debug_dir, f"upload_{timestamp}{suffix}")
        # shutil.copy(temp_path, debug_path)
        # print(f"DEBUG: Saved audio to {debug_path}")

        try:  
            # Transcribe
            transcription = ai_service.transcribe_audio(temp_path)
            
            if not transcription or not transcription.strip():
                 return {
                    "transcription": "",
                    "draft": {}
                }

            print(f"DEBUG: Transcription: {transcription[:200]}... (Total length: {len(transcription)})")
            
            # Process based on mode
            if mode == "event":
                draft = ai_service.process_event_text(transcription)
            elif mode == "idea":
                draft = ai_service.process_idea_text(transcription)
            else:
                raise HTTPException(status_code=400, detail="Invalid mode. Must be 'event' or 'idea'.")
                
            return {
                "transcription": transcription,
                "draft": draft
            }
            
        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class SaveRequest(BaseModel):
    mode: str
    data: Dict[str, Any]

@app.post("/api/save-entry")
async def save_entry(request: SaveRequest):
    try:
        if request.mode == "event":
            result = notion_service.create_event(request.data)
        elif request.mode == "idea":
            result = notion_service.create_journal(request.data)
        else:
            raise HTTPException(status_code=400, detail="Invalid mode")
            
        return {"status": "success", "result": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files (Frontend)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
