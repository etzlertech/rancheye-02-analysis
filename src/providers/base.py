from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import base64
from PIL import Image
import io


@dataclass
class AnalysisResult:
    provider: str
    model: str
    raw_response: str
    parsed_data: Dict[str, Any]
    confidence: float
    tokens_used: int
    processing_time_ms: int
    error: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


@dataclass
class ImageData:
    image_bytes: bytes
    image_id: str
    camera_name: str
    captured_at: str
    

class BaseProvider(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    @abstractmethod
    async def analyze_image(
        self, 
        image_data: ImageData,
        prompt: str,
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 500
    ) -> AnalysisResult:
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        pass
    
    @abstractmethod
    def estimate_cost(self, tokens_used: int, model: str) -> float:
        pass
    
    def encode_image(self, image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def resize_image_if_needed(self, image_bytes: bytes, max_size_kb: int = 25) -> bytes:
        current_size_kb = len(image_bytes) / 1024
        if current_size_kb <= max_size_kb:
            return image_bytes
            
        img = Image.open(io.BytesIO(image_bytes))
        
        quality = 85
        while current_size_kb > max_size_kb and quality > 20:
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            image_bytes = buffer.getvalue()
            current_size_kb = len(image_bytes) / 1024
            quality -= 5
            
        return image_bytes