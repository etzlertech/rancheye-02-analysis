#!/usr/bin/env python3
import os
import sys
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.db.supabase_client import SupabaseClient
from src.providers.openai_provider import OpenAIProvider
from src.providers.base import ImageData
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


async def test_openai_provider():
    """Test the OpenAI provider with a sample prompt"""
    print("\n=== Testing OpenAI Provider ===")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment")
        return False
    
    provider = OpenAIProvider(api_key)
    
    # Create a test image (1x1 black pixel)
    test_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x00\x00\x02\x00\x01E(\x96\x18\x00\x00\x00\x00IEND\xaeB`\x82'
    
    image_data = ImageData(
        image_bytes=test_image,
        image_id="test-001",
        camera_name="Test Camera",
        captured_at="2024-01-01T12:00:00Z"
    )
    
    prompt = """This is a test image. Please respond with the following JSON:
{
  "test_successful": true,
  "confidence": 1.0,
  "message": "OpenAI provider is working correctly"
}"""
    
    try:
        result = await provider.analyze_image(image_data, prompt, "gpt-4o-mini")
        print(f"Success: {result.parsed_data}")
        print(f"Tokens used: {result.tokens_used}")
        print(f"Processing time: {result.processing_time_ms}ms")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False


async def test_supabase_connection():
    """Test Supabase connection and basic operations"""
    print("\n=== Testing Supabase Connection ===")
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        print("ERROR: SUPABASE_URL or SUPABASE_KEY not found in environment")
        return False
    
    try:
        client = SupabaseClient(url, key)
        
        # Test getting configs
        configs = await client.get_active_configs()
        print(f"Found {len(configs)} active configurations")
        
        # Test getting pending tasks
        tasks = await client.get_pending_tasks(limit=5)
        print(f"Found {len(tasks)} pending tasks")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False


async def test_image_analysis():
    """Test analyzing an actual image from the database"""
    print("\n=== Testing Image Analysis ===")
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    client = SupabaseClient(url, key)
    
    # Get a recent image
    try:
        response = client.client.table('spypoint_images').select('*').order(
            'captured_at', desc=True
        ).limit(1).execute()
        
        if not response.data:
            print("No images found in database")
            return False
        
        image_meta = response.data[0]
        print(f"Found image: {image_meta['image_id']} from {image_meta['camera_name']}")
        
        # Download the image
        print("Downloading image...")
        image_bytes = await client.download_image(image_meta['storage_path'])
        print(f"Downloaded {len(image_bytes)/1024:.1f}KB image")
        
        # Test with gate detection
        provider = OpenAIProvider(os.getenv('OPENAI_API_KEY'))
        
        image_data = ImageData(
            image_bytes=image_bytes,
            image_id=image_meta['image_id'],
            camera_name=image_meta['camera_name'],
            captured_at=image_meta['captured_at']
        )
        
        prompt = """Analyze this ranch camera image and determine if a gate is visible. If a gate is visible, determine if it is OPEN or CLOSED.

Respond with a JSON object containing:
{
  "gate_visible": boolean,
  "gate_open": boolean (null if no gate visible),
  "confidence": float between 0-1,
  "reasoning": "brief explanation of what you see"
}"""
        
        print("Analyzing image...")
        result = await provider.analyze_image(image_data, prompt, "gpt-4o-mini")
        
        print(f"\nAnalysis Result:")
        print(f"Gate visible: {result.parsed_data.get('gate_visible')}")
        print(f"Gate open: {result.parsed_data.get('gate_open')}")
        print(f"Confidence: {result.parsed_data.get('confidence')}")
        print(f"Reasoning: {result.parsed_data.get('reasoning')}")
        print(f"Tokens used: {result.tokens_used}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False


async def main():
    print("Ranch Eye Analysis System - Test Suite")
    print("=" * 40)
    
    tests = [
        test_supabase_connection(),
        test_openai_provider(),
        test_image_analysis()
    ]
    
    results = await asyncio.gather(*tests)
    
    print("\n" + "=" * 40)
    print("Test Results:")
    print(f"Supabase Connection: {'PASS' if results[0] else 'FAIL'}")
    print(f"OpenAI Provider: {'PASS' if results[1] else 'FAIL'}")
    print(f"Image Analysis: {'PASS' if results[2] else 'FAIL'}")
    
    all_passed = all(results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))