import os
import requests
import wave
import logging
from piper.voice import PiperVoice
from config import MODELS_DIR, VOICES, VoiceModel

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize models dir
if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR)

# Cache for loaded voices
_loaded_voices = {}

def download_file(url: str, dest_path: str):
    logger.info(f"Downloading {url} to {dest_path}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logger.info("Download complete.")
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}", exc_info=True)
        raise RuntimeError(f"Failed to download model file: {e}")

def ensure_model_exists(lang: str) -> VoiceModel:
    if lang not in VOICES:
        raise ValueError(f"Language '{lang}' is not supported.")
        
    voice = VOICES[lang]
    onnx_path = os.path.join(MODELS_DIR, voice.onnx_filename)
    json_path = os.path.join(MODELS_DIR, voice.json_filename)
    
    if not os.path.exists(onnx_path):
        download_file(voice.onnx_url, onnx_path)
    
    if not os.path.exists(json_path):
        download_file(voice.json_url, json_path)
        
    return voice

def get_voice(lang: str) -> PiperVoice:
    if lang in _loaded_voices:
        return _loaded_voices[lang]
        
    try:
        voice_config = ensure_model_exists(lang)
        onnx_path = os.path.join(MODELS_DIR, voice_config.onnx_filename)
        
        # Load Piper model
        logger.info(f"Loading model for language '{lang}'...")
        voice = PiperVoice.load(onnx_path)
        _loaded_voices[lang] = voice
        return voice
    except Exception as e:
        logger.error(f"Error loading voice for '{lang}': {e}", exc_info=True)
        raise RuntimeError(f"Could not load TTS model for {lang}: {e}")

def synthesize_audio(text: str, lang: str, output_path: str):
    try:
        voice = get_voice(lang)
        
        with wave.open(output_path, "wb") as wav_file:
            # Set default parameters so wave doesn't crash on close if phonemization fails
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(voice.config.sample_rate)
            
            logger.debug(f"Synthesizing text: '{text[:50]}...'")
            voice.synthesize(text, wav_file)
            logger.debug("Synthesis successful.")
    except Exception as e:
        logger.error(f"TTS Synthesis failed: {e}", exc_info=True)
        raise RuntimeError(f"TTS Synthesis failed: {str(e)}")

