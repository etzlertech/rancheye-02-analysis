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
        max_tokens: int = 1000  # Increased for better responses
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
            
            # Check if response was blocked or incomplete
            if not response.text:
                error_msg = "Empty response from Gemini"
                if hasattr(response, 'prompt_feedback'):
                    error_msg += f" - Prompt feedback: {response.prompt_feedback}"
                raise Exception(error_msg)
            
            raw_response = response.text
            print(f"Gemini {model} raw response: {raw_response}")
            
            # Check if Gemini provides token usage info
            input_tokens = None
            output_tokens = None
            if hasattr(response, 'usage_metadata'):
                # Gemini API may provide token counts
                usage = response.usage_metadata
                if hasattr(usage, 'prompt_token_count'):
                    input_tokens = usage.prompt_token_count
                if hasattr(usage, 'candidates_token_count'):
                    output_tokens = usage.candidates_token_count
                tokens_used = (input_tokens or 0) + (output_tokens or 0)
                print(f"Gemini token usage - Input: {input_tokens}, Output: {output_tokens}")
            else:
                # Fallback to estimation if no usage metadata
                tokens_used = len(full_prompt.split()) + len(raw_response.split()) * 2
                print(f"Gemini estimated tokens: {tokens_used}")
            
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
                print(f"Gemini JSON decode error. Raw response: {raw_response}")
                
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return AnalysisResult(
                provider="gemini",
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
        # Gemini pricing (official 2024 rates per 1M tokens)
        cost_per_1k_tokens = {
            "gemini-1.5-flash": 0.00025,     # $0.10 input + $0.40 output average = $0.25 per 1M
            "gemini-1.5-pro": 0.00125,       # Legacy model pricing
            "gemini-2.0-flash-exp": 0.0,     # Free during preview
            "gemini-2.5-pro": 0.005625,      # $1.25 input + $10.00 output average = $5.625 per 1M
            "gemini-pro-vision": 0.00125     # Legacy model pricing
        }
        
        rate = cost_per_1k_tokens.get(model, 0.00125)
        return (tokens_used / 1000) * rate