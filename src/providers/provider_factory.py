from typing import Optional
from .base import BaseProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider


class ProviderFactory:
    @staticmethod
    def create_provider(provider_name: str, api_key: Optional[str] = None) -> BaseProvider:
        providers = {
            "openai": OpenAIProvider,
            "gemini": GeminiProvider,
        }
        
        provider_class = providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unsupported provider: {provider_name}")
            
        if not api_key:
            raise ValueError(f"API key required for {provider_name}")
            
        return provider_class(api_key)