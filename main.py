import os
import tempfile
import asyncio
import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)
import enum
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

# Dynamic Enum for Swagger UI dropdown
SupportedLangs = enum.Enum("SupportedLangs", {k: k for k in VOICES.keys()})

class TTSRequest(BaseModel):
    text: str
    lang: SupportedLangs = "ru"

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
    lang_val = request.lang.value if hasattr(request.lang, 'value') else request.lang
    
    if lang_val not in VOICES:
        raise HTTPException(status_code=400, detail=f"Language '{lang_val}' is not supported. Supported: {list(VOICES.keys())}")
        
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
        
    try:
        # Acquire semaphore before doing CPU-intensive work
        async with tts_semaphore:
            # Create a temporary file to store the WAV
            fd_wav, temp_wav_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd_wav)
            
            # Since synthesize_audio is synchronous and CPU-bound, run it in a threadpool
            await asyncio.to_thread(synthesize_audio, request.text, lang_val, temp_wav_path)
            
            # Convert WAV to MP3
            fd_mp3, temp_mp3_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd_mp3)
            
            import subprocess
            subprocess.run([
                'ffmpeg', '-y', '-i', temp_wav_path,
                '-codec:a', 'libmp3lame', '-qscale:a', '2',
                temp_mp3_path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        # Add background task to delete the files after sending
        background_tasks.add_task(remove_file, temp_wav_path)
        background_tasks.add_task(remove_file, temp_mp3_path)
        
        return FileResponse(
            temp_mp3_path, 
            media_type="audio/mpeg", 
            filename="speech.mp3"
        )
    except Exception as e:
        logger.error(f"Error processing TTS request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
