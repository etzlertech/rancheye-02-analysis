import openai
from openai import AsyncOpenAI
import json
import time
from typing import Dict, Any, List
from .base import BaseProvider, AnalysisResult, ImageData


class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = AsyncOpenAI(api_key=api_key)
        
    async def analyze_image(
        self, 
        image_data: ImageData,
        prompt: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        max_tokens: int = 500
    ) -> AnalysisResult:
        start_time = time.time()
        
        try:
            base64_image = self.encode_image(image_data.image_bytes)
            
            messages = [
                {
                    "role": "system",
                    "content": "You are an AI assistant analyzing ranch camera images. Always respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Camera: {image_data.camera_name}\nTime: {image_data.captured_at}\n\n{prompt}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "low"  # Use low detail for 25KB images
                            }
                        }
                    ]
                }
            ]
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
            
            raw_response = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            try:
                parsed_data = json.loads(raw_response)
                confidence = parsed_data.get('confidence', 0.5)
            except json.JSONDecodeError:
                parsed_data = {"error": "Failed to parse JSON response", "raw": raw_response}
                confidence = 0.0
                
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return AnalysisResult(
                provider="openai",
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
                provider="openai",
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
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4-vision-preview"
        ]
    
    def estimate_cost(self, tokens_used: int, model: str) -> float:
        cost_per_1k_tokens = {
            "gpt-4o": 0.015,
            "gpt-4o-mini": 0.0006,
            "gpt-4-turbo": 0.03,
            "gpt-4-vision-preview": 0.03
        }
        
        rate = cost_per_1k_tokens.get(model, 0.03)
        return (tokens_used / 1000) * rate