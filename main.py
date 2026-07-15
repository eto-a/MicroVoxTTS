import os
import tempfile
import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from fastapi.responses import FileResponse
from pydantic import BaseModel
from config import VOICES, API_KEY, MAX_CONCURRENT_REQUESTS
from tts_engine import synthesize_audio

app = FastAPI(title="MicroVoxTTS", description="Lightweight TTS for VPS", version="1.0")

# Security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header != API_KEY:
        raise HTTPException(status_code=403, detail="Could not validate API KEY")
    return api_key_header

# Concurrency control
tts_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

class TTSRequest(BaseModel):
    text: str
    lang: str = "ru"

def remove_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Error removing temp file {path}: {e}")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "MicroVoxTTS is running", "supported_languages": list(VOICES.keys())}

@app.post("/api/v1/tts")
async def tts_generate(request: TTSRequest, background_tasks: BackgroundTasks, api_key: str = Depends(get_api_key)):
    if request.lang not in VOICES:
        raise HTTPException(status_code=400, detail=f"Language '{request.lang}' is not supported. Supported: {list(VOICES.keys())}")
        
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
        
    try:
        # Acquire semaphore before doing CPU-intensive work
        async with tts_semaphore:
            # Create a temporary file to store the WAV
            fd, temp_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd) # Close the file descriptor, we just need the path
            
            # Since synthesize_audio is synchronous and CPU-bound, run it in a threadpool
            # to not block the asyncio event loop
            await asyncio.to_thread(synthesize_audio, request.text, request.lang, temp_path)
            
        # Add background task to delete the file after it has been sent
        background_tasks.add_task(remove_file, temp_path)
        
        return FileResponse(
            temp_path, 
            media_type="audio/wav", 
            filename="speech.wav"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
