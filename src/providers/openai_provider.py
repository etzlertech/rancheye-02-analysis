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
            print(f"Image encoded successfully. Base64 length: {len(base64_image)}")
            
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
            
            # Only use json mode for models that support it
            create_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Add JSON mode only for supported models
            if model in ["gpt-4-turbo-preview", "gpt-4-turbo", "gpt-4o", "gpt-4o-2024-05-13"]:
                create_params["response_format"] = {"type": "json_object"}
            
            response = await self.client.chat.completions.create(**create_params)
            
            raw_response = response.choices[0].message.content
            
            # Capture detailed token usage
            tokens_used = response.usage.total_tokens
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            
            print(f"OpenAI token usage - Input: {input_tokens}, Output: {output_tokens}, Total: {tokens_used}")
            
            # Log the response for debugging
            print(f"OpenAI raw response: {raw_response[:500]}...")
            
            # Clean the response - remove markdown code blocks if present
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]  # Remove ```
            
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Remove trailing ```
            
            cleaned_response = cleaned_response.strip()
            
            try:
                parsed_data = json.loads(cleaned_response)
                confidence = parsed_data.get('confidence', 0.5)
            except json.JSONDecodeError:
                # Try one more time with just extracting JSON from the response
                import re
                # Look for JSON object - match from first { to last }
                json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                if json_match:
                    try:
                        parsed_data = json.loads(json_match.group())
                        confidence = parsed_data.get('confidence', 0.5)
                    except:
                        parsed_data = {"error": "Failed to parse JSON response", "raw": raw_response}
                        confidence = 0.0
                else:
                    parsed_data = {"error": "Failed to parse JSON response", "raw": raw_response}
                    confidence = 0.0
                print(f"JSON decode error. Raw response: {raw_response}")
                
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return AnalysisResult(
                provider="openai",
                model=model,
                raw_response=raw_response,
                parsed_data=parsed_data,
                confidence=confidence,
                tokens_used=tokens_used,
                processing_time_ms=processing_time_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"OpenAI API Error: {str(e)}"
            print(f"Error in OpenAI provider: {error_msg}")
            
            return AnalysisResult(
                provider="openai",
                model=model,
                raw_response=error_msg,
                parsed_data={"error": error_msg},
                confidence=0.0,
                tokens_used=0,
                processing_time_ms=processing_time_ms,
                error=error_msg
            )
    
    def get_supported_models(self) -> List[str]:
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4-vision-preview"
        ]
    
    def estimate_cost(self, tokens_used: int, model: str) -> float:
        # OpenAI pricing (official 2024 rates - average of input/output per 1M tokens)
        cost_per_1k_tokens = {
            "gpt-4o": 0.010,           # $5.00 input + $15.00 output average = $10.00 per 1M
            "gpt-4o-mini": 0.000375,   # $0.15 input + $0.60 output average = $0.375 per 1M
            "gpt-4-turbo": 0.03,       # Legacy pricing
            "gpt-4-vision-preview": 0.03  # Legacy pricing
        }
        
        rate = cost_per_1k_tokens.get(model, 0.03)
        return (tokens_used / 1000) * rate