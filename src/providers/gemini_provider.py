import google.generativeai as genai
import json
import time
from typing import Dict, Any, List
from .base import BaseProvider, AnalysisResult, ImageData
from PIL import Image
import io


class GeminiProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        genai.configure(api_key=api_key)
        
    async def analyze_image(
        self, 
        image_data: ImageData,
        prompt: str,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.3,
        max_tokens: int = 500
    ) -> AnalysisResult:
        start_time = time.time()
        
        try:
            # Initialize the model
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "response_mime_type": "application/json"
            }
            
            model_instance = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config
            )
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data.image_bytes))
            
            # Prepare the prompt with context
            full_prompt = f"""Camera: {image_data.camera_name}
Time: {image_data.captured_at}

{prompt}

Remember to respond with valid JSON only."""
            
            # Generate content
            response = model_instance.generate_content([full_prompt, image])
            
            raw_response = response.text
            
            # Estimate tokens (Gemini doesn't provide exact count)
            tokens_used = len(full_prompt.split()) + len(raw_response.split()) * 2
            
            try:
                parsed_data = json.loads(raw_response)
                confidence = parsed_data.get('confidence', 0.5)
            except json.JSONDecodeError:
                parsed_data = {"error": "Failed to parse JSON response", "raw": raw_response}
                confidence = 0.0
                
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return AnalysisResult(
                provider="gemini",
                model=model,
                raw_response=raw_response,
                parsed_data=parsed_data,
                confidence=confidence,
                tokens_used=tokens_used,
                processing_time_ms=processing_time_ms
            )
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            return AnalysisResult(
                provider="gemini",
                model=model,
                raw_response="",
                parsed_data={},
                confidence=0.0,
                tokens_used=0,
                processing_time_ms=processing_time_ms,
                error=str(e)
            )
    
    def get_supported_models(self) -> List[str]:
        return [
            "gemini-1.5-flash",
            "gemini-1.5-pro", 
            "gemini-2.0-flash-exp",
            "gemini-2.5-pro",
            "gemini-pro-vision"
        ]
    
    def estimate_cost(self, tokens_used: int, model: str) -> float:
        # Gemini pricing (approximate)
        cost_per_1k_tokens = {
            "gemini-1.5-flash": 0.00035,     # $0.35 per 1M tokens
            "gemini-1.5-pro": 0.00125,       # $1.25 per 1M tokens
            "gemini-2.0-flash-exp": 0.0,     # Free during preview
            "gemini-2.5-pro": 0.007,         # $7.00 per 1M tokens (estimated)
            "gemini-pro-vision": 0.00125     # Same as 1.5 pro
        }
        
        rate = cost_per_1k_tokens.get(model, 0.00125)
        return (tokens_used / 1000) * rate