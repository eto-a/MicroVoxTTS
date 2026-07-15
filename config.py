import os
from pydantic import BaseModel
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY", "your-secret-api-key")
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "2"))

# Base directory for storing models
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

# Base URL for downloading Piper models from HuggingFace
PIPER_HF_BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"

class VoiceModel(BaseModel):
    path: str
    name: str
    
    @property
    def onnx_url(self) -> str:
        return f"{PIPER_HF_BASE_URL}/{self.path}.onnx"
    
    @property
    def json_url(self) -> str:
        return f"{PIPER_HF_BASE_URL}/{self.path}.onnx.json"
        
    @property
    def onnx_filename(self) -> str:
        return f"{self.name}.onnx"
        
    @property
    def json_filename(self) -> str:
        return f"{self.name}.onnx.json"

# Supported voices
VOICES: Dict[str, VoiceModel] = {
    "en": VoiceModel(
        path="en/en_US/lessac/medium/en_US-lessac-medium",
        name="en_US-lessac-medium"
    ),
    "ru": VoiceModel(
        path="ru/ru_RU/dmitri/medium/ru_RU-dmitri-medium",
        name="ru_RU-dmitri-medium"
    ),
    "pl": VoiceModel(
        path="pl/pl_PL/gosia/medium/pl_PL-gosia-medium",
        name="pl_PL-gosia-medium"
    )
}
