from fastapi import FastAPI, HTTPException, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json
import os
import sys
import uuid
import time
from functools import lru_cache

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db.supabase_client import SupabaseClient
from src.services.analysis_service import AnalysisService
from src.task_processor import TaskProcessor
from src.providers.base import ImageData
from dotenv import load_dotenv
from src.api.image_analysis_history import router as history_router


load_dotenv()

app = FastAPI(title="RanchEye Analysis API", version="1.0.0")

# Include routers
app.include_router(history_router)

# Mount static files
static_dir = Path(__file__).parent.parent.parent / "static"
react_build_dir = static_dir / "dist"

# In production, serve React build files
if react_build_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(react_build_dir / "assets")), name="assets")
else:
    # In development, serve original static files
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
supabase = SupabaseClient(
    url=os.getenv('SUPABASE_URL'),
    key=os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
)
analysis_service = AnalysisService(supabase)
task_processor = TaskProcessor()

# Simple in-memory cache for signed URLs
url_cache = {}
CACHE_DURATION = 3300  # 55 minutes (less than 1 hour expiration)

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()


# Pydantic models
class AnalysisConfig(BaseModel):
    name: str
    camera_name: Optional[str] = None
    analysis_type: str
    model_provider: str
    model_name: str
    prompt_template: str
    threshold: float = 0.8
    alert_cooldown_minutes: int = 60
    secondary_provider: Optional[str] = None
    secondary_model: Optional[str] = None
    tiebreaker_provider: Optional[str] = None
    tiebreaker_model: Optional[str] = None


class AnalysisRequest(BaseModel):
    image_id: str
    config_id: Optional[str] = None


class PromptTemplate(BaseModel):
    name: str
    description: Optional[str] = None
    prompt_text: str
    analysis_type: str
    tags: Optional[List[str]] = None
    model_optimized_for: Optional[List[str]] = None


class SavePromptRequest(BaseModel):
    name: str
    description: Optional[str] = None
    prompt_text: str
    analysis_type: str
    save_as_default: bool = False
    tags: Optional[List[str]] = None


# API Endpoints
@app.get("/")
async def root():
    # Debug paths
    print(f"Looking for React build at: {react_build_dir}")
    print(f"React index exists: {(react_build_dir / 'index.html').exists()}")
    print(f"Static dir: {static_dir}")
    print(f"Static dir exists: {static_dir.exists()}")
    if static_dir.exists():
        print(f"Static dir contents: {list(static_dir.iterdir())}")
        if react_build_dir.exists():
            print(f"React build dir contents: {list(react_build_dir.iterdir())}")
    
    # Serve React build
    react_index = react_build_dir / "index.html"
    if react_index.exists():
        print(f"Serving React app from: {react_index}")
        return FileResponse(str(react_index))
    
    # If no React build, try serving ANY index.html in static
    static_index = static_dir / "index.html"
    if static_index.exists():
        print(f"Serving static index from: {static_index}")
        return FileResponse(str(static_index))
    
    # Last resort: old HTML
    html_file = static_dir / "index-old.html"
    if html_file.exists():
        print(f"Serving old HTML from: {html_file}")
        return FileResponse(str(html_file))
    
    # If no UI found, return API status
    return {"message": "RanchEye Analysis API", "status": "running", "ui": "not found", "react_dir": str(react_build_dir), "static_dir": str(static_dir)}


@app.get("/health")
async def health_check():
    # Check environment variables
    env_status = {
        "SUPABASE_URL": bool(os.getenv('SUPABASE_URL')),
        "SUPABASE_KEY": bool(os.getenv('SUPABASE_KEY')),
        "SUPABASE_SERVICE_ROLE_KEY": bool(os.getenv('SUPABASE_SERVICE_ROLE_KEY')),
    }
    
    # Try to connect to Supabase
    db_status = "unknown"
    storage_status = "unknown"
    try:
        # Simple query to test connection
        response = supabase.client.table('spypoint_images').select('id').limit(1).execute()
        db_status = "connected"
        
        # Test storage access
        try:
            # List files in bucket to test storage access
            storage_files = supabase.client.storage.from_('spypoint-images').list(limit=1)
            storage_status = f"connected (found {len(storage_files)} files)"
        except Exception as e:
            storage_status = f"error: {str(e)}"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "env_vars": env_status,
        "database": db_status,
        "storage": storage_status
    }


@app.get("/api/configs")
async def get_configs(active_only: bool = True):
    try:
        if active_only:
            configs = await supabase.get_active_configs()
        else:
            response = supabase.client.table('analysis_configs').select('*').execute()
            configs = response.data
        return {"configs": configs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/configs")
async def create_config(config: AnalysisConfig):
    try:
        response = supabase.client.table('analysis_configs').insert(
            config.dict()
        ).execute()
        return {"config": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/configs/{config_id}")
async def update_config(config_id: str, config: AnalysisConfig):
    try:
        response = supabase.client.table('analysis_configs').update(
            config.dict()
        ).eq('id', config_id).execute()
        return {"config": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/configs/{config_id}")
async def delete_config(config_id: str):
    try:
        supabase.client.table('analysis_configs').update(
            {"active": False}
        ).eq('id', config_id).execute()
        return {"message": "Config deactivated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/images/recent")
async def get_recent_images(limit: int = 20, thumbnail: bool = False):
    try:
        print(f"Fetching recent images with limit: {limit}, thumbnail: {thumbnail}")
        import time
        start_time = time.time()
        
        # Fetch images from database
        response = supabase.client.table('spypoint_images').select('*').order(
            'downloaded_at', desc=True
        ).limit(limit).execute()
        
        images = response.data
        print(f"Found {len(images)} images in {time.time() - start_time:.2f}s")
        
        # Generate signed URLs in parallel using asyncio
        url_start_time = time.time()
        
        async def generate_signed_url(image):
            """Generate signed URL for a single image"""
            if not image.get('storage_path'):
                return image
            
            # Check cache first
            cache_key = f"{image['image_id']}:{image['storage_path']}"
            cached_url = url_cache.get(cache_key)
            
            if cached_url and cached_url['expires'] > time.time():
                image['image_url'] = cached_url['url']
                return image
                
            try:
                # Run the sync Supabase client in a thread to avoid blocking
                import asyncio
                # Ensure storage path doesn't have leading slash
                storage_path = image['storage_path'].lstrip('/')
                signed_url = await asyncio.to_thread(
                    supabase.client.storage.from_('spypoint-images').create_signed_url,
                    storage_path,
                    3600  # 1 hour expiration
                )
                if signed_url and 'signedURL' in signed_url:
                    url = signed_url['signedURL']
                    image['image_url'] = url
                    # Cache the URL
                    url_cache[cache_key] = {
                        'url': url,
                        'expires': time.time() + CACHE_DURATION
                    }
                else:
                    print(f"No signed URL returned for {image['image_id']}: {signed_url}")
                    image['image_url'] = f"/api/images/{image['image_id']}/preview"
            except Exception as e:
                print(f"Error generating signed URL for {image['image_id']}: {type(e).__name__}: {str(e)}")
                # Use preview endpoint as fallback
                image['image_url'] = f"/api/images/{image['image_id']}/preview"
            
            return image
        
        # Generate all URLs concurrently
        import asyncio
        tasks = [generate_signed_url(image) for image in images]
        await asyncio.gather(*tasks)
        
        # Count how many URLs were cached vs generated
        cached_count = sum(1 for img in images if img.get('image_url') and 
                          f"{img['image_id']}:{img.get('storage_path', '')}" in url_cache)
        
        print(f"URLs: {cached_count} cached, {len(images) - cached_count} generated in {time.time() - url_start_time:.2f}s")
        print(f"Total request time: {time.time() - start_time:.2f}s")
        
        # Add cache headers to response
        response = JSONResponse(content={"images": images})
        response.headers["Cache-Control"] = "public, max-age=30"
        return response
    except Exception as e:
        print(f"Error fetching images: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/images/{image_id}/debug")
async def debug_image_url(image_id: str):
    """Debug endpoint to check image URL generation"""
    try:
        # Get image metadata
        image_metadata = await supabase.get_image_metadata(image_id)
        if not image_metadata:
            return {"error": "Image not found", "image_id": image_id}
        
        result = {
            "image_id": image_id,
            "storage_path": image_metadata.get('storage_path'),
            "has_storage_path": bool(image_metadata.get('storage_path')),
            "image_url_in_db": image_metadata.get('image_url', 'None')
        }
        
        # Try to generate signed URL
        if image_metadata.get('storage_path'):
            try:
                storage_path = image_metadata['storage_path'].lstrip('/')
                signed_url = supabase.client.storage.from_('spypoint-images').create_signed_url(
                    storage_path,
                    3600
                )
                result['signed_url_generated'] = bool(signed_url and 'signedURL' in signed_url)
                result['signed_url'] = signed_url.get('signedURL') if signed_url else None
                result['signed_url_raw'] = signed_url
            except Exception as e:
                result['signed_url_error'] = f"{type(e).__name__}: {str(e)}"
        
        return result
    except Exception as e:
        return {"error": str(e), "image_id": image_id}


@app.get("/api/images/{image_id}/preview")
async def get_image_preview(image_id: str):
    """Get image preview/thumbnail"""
    try:
        # Get image metadata
        image_metadata = await supabase.get_image_metadata(image_id)
        if not image_metadata:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Try to get image from URL if available
        if 'image_url' in image_metadata and image_metadata['image_url']:
            # Redirect to the image URL
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=image_metadata['image_url'])
        
        # Otherwise try to download from storage
        try:
            image_bytes = await supabase.download_image(image_metadata['storage_path'])
            from fastapi.responses import Response
            return Response(content=image_bytes, media_type="image/jpeg")
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Image not accessible: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis/results")
async def get_analysis_results(
    image_id: Optional[str] = None,
    limit: int = 50
):
    try:
        query = supabase.client.table('image_analysis_results').select('*')
        
        if image_id:
            query = query.eq('image_id', image_id)
            
        response = query.order('created_at', desc=True).limit(limit).execute()
        return {"results": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analysis/analyze")
async def analyze_image(request: AnalysisRequest):
    try:
        # Create analysis tasks
        if request.config_id:
            # Analyze with specific config
            task_data = {
                'image_id': request.image_id,
                'config_id': request.config_id,
                'priority': 10,  # High priority for manual requests
                'status': 'pending'
            }
            response = supabase.client.table('analysis_tasks').insert(task_data).execute()
            task_id = response.data[0]['id']
        else:
            # Create tasks for all applicable configs
            count = await supabase.create_analysis_tasks_for_image(request.image_id)
            if count == 0:
                raise HTTPException(status_code=400, detail="No applicable configs found")
            task_id = None
        
        # Broadcast update
        await manager.broadcast({
            "type": "task_created",
            "image_id": request.image_id,
            "task_id": task_id
        })
        
        return {"message": "Analysis started", "task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/pending")
async def get_pending_tasks():
    try:
        tasks = await supabase.get_pending_tasks(limit=100)
        return {"tasks": tasks, "count": len(tasks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts")
async def get_alerts(unacknowledged_only: bool = True):
    try:
        query = supabase.client.table('analysis_alerts').select('*')
        
        if unacknowledged_only:
            query = query.is_('acknowledged_at', 'null')
            
        response = query.order('created_at', desc=True).limit(50).execute()
        return {"alerts": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    try:
        supabase.client.table('analysis_alerts').update({
            'acknowledged_at': datetime.utcnow().isoformat(),
            'acknowledged_by': 'web_user'
        }).eq('id', alert_id).execute()
        return {"message": "Alert acknowledged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analysis/test")
async def test_analysis(request: dict):
    """Run a test analysis on an image from storage"""
    try:
        image_id = request.get('image_id')
        analysis_type = request.get('analysis_type', 'general')
        custom_prompt = request.get('custom_prompt', '')
        selected_models = request.get('selected_models', ['openai-gpt-4o-mini'])
        compare_models = request.get('compare_models', False)
        
        if not image_id:
            raise HTTPException(status_code=400, detail="image_id required")
        
        # Get image metadata
        image_metadata = await supabase.get_image_metadata(image_id)
        if not image_metadata:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Download image from storage
        try:
            image_bytes = await supabase.download_image(image_metadata['storage_path'])
        except Exception as e:
            # If storage path fails, try the image URL
            if 'image_url' in image_metadata:
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_metadata['image_url'])
                    image_bytes = response.content
            else:
                raise HTTPException(status_code=500, detail=f"Cannot download image: {str(e)}")
        
        # Create ImageData object
        from src.providers.base import ImageData
        image_data = ImageData(
            image_bytes=image_bytes,
            image_id=image_metadata['image_id'],
            camera_name=image_metadata['camera_name'],
            captured_at=image_metadata.get('downloaded_at', '')
        )
        
        # Create a temporary config for this test
        test_config = {
            'analysis_type': analysis_type,
            'model_provider': 'openai',
            'model_name': 'gpt-4o-mini',
            'prompt_template': custom_prompt if custom_prompt else get_test_prompt(analysis_type),
            'primary_provider': 'openai',
            'primary_model': 'gpt-4o-mini'
        }
        
        # Generate session ID for grouping related analyses
        session_id = str(uuid.uuid4())
        
        # Check if we should compare models
        if compare_models or len(selected_models) > 1:
            results = []
            
            # Model configurations
            model_configs = {
                'openai-gpt-4o-mini': {
                    'provider': 'openai',
                    'model': 'gpt-4o-mini',
                    'api_key': os.getenv('OPENAI_API_KEY')
                },
                'openai-gpt-4o': {
                    'provider': 'openai',
                    'model': 'gpt-4o',
                    'api_key': os.getenv('OPENAI_API_KEY')
                },
                'gemini-1.5-flash': {
                    'provider': 'gemini',
                    'model': 'gemini-1.5-flash',
                    'api_key': os.getenv('GEMINI_API_KEY')
                },
                'gemini-2.0-flash': {
                    'provider': 'gemini',
                    'model': 'gemini-2.0-flash-exp',
                    'api_key': os.getenv('GEMINI_API_KEY')
                },
                'gemini-2.5-pro': {
                    'provider': 'gemini',
                    'model': 'gemini-2.5-pro',
                    'api_key': os.getenv('GEMINI_API_KEY')
                }
            }
            
            # Run analysis for each selected model
            for model_id in selected_models:
                if model_id in model_configs:
                    model_info = model_configs[model_id]
                    if model_info['api_key']:
                        model_config = test_config.copy()
                        model_config.update({
                            'model_provider': model_info['provider'],
                            'model_name': model_info['model'],
                            'primary_provider': model_info['provider'],
                            'primary_model': model_info['model']
                        })
                        
                        try:
                            result = await analysis_service.analyze_with_dual_models(
                                image_data,
                                model_config,
                                model_info['api_key'],
                                session_id=session_id,
                                user_initiated=True
                            )
                            
                            # Save additional analysis log for this model
                            formatted_result = format_model_result(result, model_config, analysis_type)
                            primary_result = result.get('primary_result')
                            if primary_result:
                                await save_test_analysis_log(
                                    image_metadata, analysis_type, custom_prompt,
                                    model_info['provider'], model_info['model'],
                                    primary_result.raw_response, result['final_result'],
                                    formatted_result.get('confidence', 0),
                                    primary_result.processing_time_ms,
                                    primary_result.tokens_used, session_id,
                                    None,  # error_message
                                    primary_result.input_tokens,
                                    primary_result.output_tokens
                                )
                            
                            results.append(formatted_result)
                        except Exception as e:
                            error_msg = str(e)
                            results.append({
                                'model_provider': model_info['provider'],
                                'model_name': model_info['model'],
                                'error': error_msg,
                                'analysis_type': analysis_type
                            })
                            
                            # Save error log
                            await save_test_analysis_log(
                                image_metadata, analysis_type, custom_prompt,
                                model_info['provider'], model_info['model'],
                                error_msg, {}, 0, 0, 0, session_id, error_msg,
                                None, None  # input_tokens, output_tokens
                            )
                    else:
                        results.append({
                            'model_provider': model_info['provider'],
                            'model_name': model_info['model'],
                            'error': f"API key not configured for {model_info['provider']}",
                            'analysis_type': analysis_type
                        })
            
            # Broadcast stats update after saving all analyses
            try:
                stats = await get_analysis_stats()
                await manager.broadcast({
                    "type": "stats_update",
                    "data": stats["stats"],
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                print(f"Failed to broadcast stats update: {e}")
            
            return {
                'compare_mode': True,
                'results': results,
                'analysis_type': analysis_type,
                'image': image_metadata,
                'session_id': session_id
            }
        
        # Single model analysis
        model_id = selected_models[0] if selected_models else 'openai-gpt-4o-mini'
        model_configs = {
            'openai-gpt-4o-mini': {
                'provider': 'openai',
                'model': 'gpt-4o-mini',
                'api_key': os.getenv('OPENAI_API_KEY')
            },
            'openai-gpt-4o': {
                'provider': 'openai',
                'model': 'gpt-4o',
                'api_key': os.getenv('OPENAI_API_KEY')
            },
            'gemini-1.5-flash': {
                'provider': 'gemini',
                'model': 'gemini-1.5-flash',
                'api_key': os.getenv('GEMINI_API_KEY')
            },
            'gemini-2.0-flash': {
                'provider': 'gemini',
                'model': 'gemini-2.0-flash-exp',
                'api_key': os.getenv('GEMINI_API_KEY')
            },
            'gemini-2.5-pro': {
                'provider': 'gemini',
                'model': 'gemini-2.5-pro',
                'api_key': os.getenv('GEMINI_API_KEY')
            }
        }
        
        if model_id not in model_configs:
            raise HTTPException(status_code=400, detail=f"Unknown model: {model_id}")
            
        model_info = model_configs[model_id]
        if not model_info['api_key']:
            raise HTTPException(status_code=500, detail=f"API key not configured for {model_info['provider']}")
        
        # Update config with selected model
        test_config.update({
            'model_provider': model_info['provider'],
            'model_name': model_info['model'],
            'primary_provider': model_info['provider'],
            'primary_model': model_info['model']
        })
        
        # Run analysis
        result = await analysis_service.analyze_with_dual_models(
            image_data,
            test_config,
            model_info['api_key'],
            session_id=session_id,
            user_initiated=True
        )
        
        # Format response for frontend
        primary_result = result.get('primary_result')
        if primary_result:
            # Log the raw response for debugging
            print(f"Analysis completed. Raw response: {primary_result.raw_response[:200]}...")
            print(f"Parsed data: {result['final_result']}")
            
            # Ensure we have a valid result
            final_result = result['final_result']
            if not final_result or (isinstance(final_result, dict) and len(final_result) == 0):
                # Try to parse the raw response if final_result is empty
                try:
                    import json
                    final_result = json.loads(primary_result.raw_response)
                except:
                    final_result = {
                        'error': 'Failed to parse AI response',
                        'raw_response': primary_result.raw_response[:500]
                    }
            
            # Save comprehensive analysis log
            await save_test_analysis_log(
                image_metadata, analysis_type, custom_prompt,
                test_config['model_provider'], test_config['model_name'],
                primary_result.raw_response, final_result,
                final_result.get('confidence', 0.95) if isinstance(final_result, dict) else 0.95,
                primary_result.processing_time_ms,
                primary_result.tokens_used, session_id,
                None,  # error_message
                primary_result.input_tokens,
                primary_result.output_tokens
            )
            
            # Broadcast stats update after saving analysis
            try:
                stats = await get_analysis_stats()
                await manager.broadcast({
                    "type": "stats_update",
                    "data": stats["stats"],
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                print(f"Failed to broadcast stats update: {e}")
            
            return {
                'analysis_type': analysis_type,
                'confidence': final_result.get('confidence', 0.95) if isinstance(final_result, dict) else 0.95,
                'model_provider': test_config['model_provider'],
                'model_name': test_config['model_name'],
                'result': final_result,
                'tokens_used': primary_result.tokens_used,
                'input_tokens': primary_result.input_tokens,
                'output_tokens': primary_result.output_tokens,
                'processing_time_ms': primary_result.processing_time_ms,
                'raw_response': primary_result.raw_response,  # Include for debugging
                'session_id': session_id
            }
        else:
            # Save error log for failed analysis
            await save_test_analysis_log(
                image_metadata, analysis_type, custom_prompt,
                test_config['model_provider'], test_config['model_name'],
                'Analysis failed - no result returned', {}, 0, 0, 0, session_id,
                'Analysis failed - no result returned',
                None, None  # input_tokens, output_tokens
            )
            
            return {
                'analysis_type': analysis_type,
                'confidence': 0,
                'model_provider': test_config['model_provider'],
                'model_name': test_config['model_name'],
                'result': {'error': 'Analysis failed - no result returned'},
                'tokens_used': 0,
                'processing_time_ms': 0,
                'session_id': session_id
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prompt-templates")
async def get_prompt_templates(analysis_type: Optional[str] = None):
    """Get all prompt templates, optionally filtered by analysis type"""
    try:
        query = supabase.client.table('custom_prompt_templates').select('*')
        
        if analysis_type:
            query = query.eq('analysis_type', analysis_type)
        
        response = query.order('is_default', desc=True).order('usage_count', desc=True).execute()
        return {"templates": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/prompt-templates/{template_id}")
async def get_prompt_template(template_id: str):
    """Get a specific prompt template by ID"""
    try:
        response = supabase.client.table('custom_prompt_templates').select('*').eq('id', template_id).single().execute()
        return {"template": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/prompt-templates")
async def save_prompt_template(request: SavePromptRequest):
    """Save a new prompt template or update default"""
    try:
        if request.save_as_default:
            # Update existing default template
            response = supabase.client.table('custom_prompt_templates').update({
                'prompt_text': request.prompt_text,
                'description': request.description,
                'tags': request.tags
            }).eq('analysis_type', request.analysis_type).eq('is_default', True).execute()
            
            if response.data:
                return {"message": "Default template updated", "template": response.data[0]}
            else:
                # No existing default, create new one
                template_data = {
                    'name': f"Default {request.analysis_type.replace('_', ' ').title()}",
                    'description': request.description,
                    'prompt_text': request.prompt_text,
                    'analysis_type': request.analysis_type,
                    'is_default': True,
                    'is_system': False,
                    'tags': request.tags
                }
                response = supabase.client.table('custom_prompt_templates').insert(template_data).execute()
                return {"message": "Default template created", "template": response.data[0]}
        else:
            # Create new custom template
            template_data = {
                'name': request.name,
                'description': request.description,
                'prompt_text': request.prompt_text,
                'analysis_type': request.analysis_type,
                'is_default': False,
                'is_system': False,
                'tags': request.tags
            }
            response = supabase.client.table('custom_prompt_templates').insert(template_data).execute()
            return {"message": "Custom template created", "template": response.data[0]}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/prompt-templates/{template_id}")
async def update_prompt_template(template_id: str, template: PromptTemplate):
    """Update an existing prompt template"""
    try:
        update_data = {
            'name': template.name,
            'description': template.description,
            'prompt_text': template.prompt_text,
            'analysis_type': template.analysis_type,
            'tags': template.tags,
            'model_optimized_for': template.model_optimized_for
        }
        
        response = supabase.client.table('custom_prompt_templates').update(update_data).eq('id', template_id).execute()
        return {"message": "Template updated", "template": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/prompt-templates/{template_id}")
async def delete_prompt_template(template_id: str):
    """Delete a prompt template (cannot delete system defaults)"""
    try:
        # Check if it's a system default template
        response = supabase.client.table('custom_prompt_templates').select('is_system, is_default').eq('id', template_id).single().execute()
        
        if response.data['is_system'] and response.data['is_default']:
            raise HTTPException(status_code=400, detail="Cannot delete system default templates")
        
        supabase.client.table('custom_prompt_templates').delete().eq('id', template_id).execute()
        return {"message": "Template deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/prompt-templates/{template_id}/set-default")
async def set_default_template(template_id: str):
    """Set a template as the default for its analysis type"""
    try:
        # Use the database function to ensure only one default per analysis type
        supabase.client.rpc('set_default_template', {'template_id': template_id}).execute()
        return {"message": "Template set as default"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/prompt-templates/{template_id}/increment-usage")
async def increment_template_usage(template_id: str):
    """Increment usage count for a template"""
    try:
        supabase.client.rpc('increment_prompt_usage', {'template_id': template_id}).execute()
        return {"message": "Usage incremented"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/setup-custom-prompts")
async def setup_custom_prompt_templates():
    """Setup custom prompt templates table (admin only)"""
    try:
        # Check if table already exists by trying a simple query
        try:
            supabase.client.table('custom_prompt_templates').select('id').limit(1).execute()
            return {"message": "Custom prompt templates table already exists", "status": "already_exists"}
        except Exception:
            # Table doesn't exist, we need to create it
            pass
        
        # Try to create the table with basic schema
        # Note: This is a simplified version. Full schema should be run manually in Supabase
        basic_sql = """
        CREATE TABLE IF NOT EXISTS custom_prompt_templates (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            description TEXT,
            prompt_text TEXT NOT NULL,
            analysis_type TEXT NOT NULL,
            is_default BOOLEAN DEFAULT FALSE,
            is_system BOOLEAN DEFAULT FALSE,
            created_by TEXT DEFAULT 'web_user',
            usage_count INTEGER DEFAULT 0,
            last_used_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
        
        # Since we can't execute raw SQL through Supabase client directly,
        # we'll return instructions for manual setup
        return {
            "message": "Custom prompt templates table needs to be created manually",
            "status": "manual_setup_required",
            "instructions": [
                "1. Go to your Supabase dashboard",
                "2. Navigate to SQL Editor",
                "3. Run the SQL from database/custom_prompt_templates.sql",
                "4. Or contact your administrator to set up the database"
            ],
            "sql_file": "database/custom_prompt_templates.sql"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def format_model_result(result: dict, config: dict, analysis_type: str) -> dict:
    """Format analysis result for a specific model"""
    primary_result = result.get('primary_result')
    if primary_result:
        final_result = result['final_result']
        if not final_result or (isinstance(final_result, dict) and len(final_result) == 0):
            try:
                import json
                final_result = json.loads(primary_result.raw_response)
            except:
                final_result = {
                    'error': 'Failed to parse AI response',
                    'raw_response': primary_result.raw_response[:500]
                }
        
        return {
            'analysis_type': analysis_type,
            'confidence': final_result.get('confidence', 0.95) if isinstance(final_result, dict) else 0.95,
            'model_provider': config['model_provider'],
            'model_name': config['model_name'],
            'result': final_result,
            'tokens_used': primary_result.tokens_used,
            'input_tokens': primary_result.input_tokens,
            'output_tokens': primary_result.output_tokens,
            'processing_time_ms': primary_result.processing_time_ms,
            'raw_response': primary_result.raw_response
        }
    else:
        return {
            'analysis_type': analysis_type,
            'confidence': 0,
            'model_provider': config['model_provider'],
            'model_name': config['model_name'],
            'result': {'error': 'Analysis failed - no result returned'},
            'tokens_used': 0,
            'processing_time_ms': 0
        }


async def save_test_analysis_log(
    image_data,
    analysis_type: str,
    prompt: str,
    model_provider: str,
    model_name: str,
    raw_response: str,
    parsed_response: Dict[str, Any],
    confidence: float,
    processing_time_ms: int,
    tokens_used: int,
    session_id: str,
    error_message: Optional[str] = None,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None
) -> Optional[str]:
    """Save comprehensive log for test analysis"""
    try:
        # Calculate cost if we have token counts
        estimated_cost = 0.0
        if input_tokens and output_tokens:
            estimated_cost = calculate_token_cost(model_name, input_tokens, output_tokens)
        elif tokens_used:
            # Estimate with 30/70 split if we only have total
            estimated_cost = calculate_token_cost(
                model_name,
                int(tokens_used * 0.3),
                int(tokens_used * 0.7)
            )
        
        return await supabase.save_ai_analysis_log(
            image_id=image_data['image_id'],
            image_url=image_data.get('image_url'),
            camera_name=image_data.get('camera_name'),
            captured_at=image_data.get('downloaded_at') or image_data.get('captured_at'),
            analysis_type=analysis_type,
            prompt_text=prompt,
            custom_prompt=True,  # Test analyses always use custom/modified prompts
            model_provider=model_provider,
            model_name=model_name,
            raw_response=raw_response,
            parsed_response=parsed_response,
            confidence=confidence,
            analysis_successful=error_message is None,
            error_message=error_message,
            processing_time_ms=processing_time_ms,
            tokens_used=tokens_used,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=estimated_cost,
            session_id=session_id,
            user_initiated=True,  # Test analyses are always user-initiated
            notes=f"Test analysis via web interface"
        )
    except Exception as e:
        logger.error(f"Failed to save test analysis log: {e}")
        return None


def get_test_prompt(analysis_type: str) -> str:
    """Get prompt template for test analysis types"""
    prompts = {
        'gate_detection': '''You are analyzing a trail camera image from a ranch. Look for any gates in the image and determine their status.

Analyze the image and respond ONLY with valid JSON in this exact format:
{
  "gate_visible": true or false,
  "gate_open": true or false (null if no gate visible),
  "confidence": 0.0 to 1.0,
  "reasoning": "Detailed explanation of what you see in the image and why you made this decision",
  "visual_evidence": "Specific visual details that support your conclusion (e.g., gate posts, hinges, gaps, shadows)"
}''',
        'door_detection': '''You are analyzing a trail camera image from a ranch or building. Look for any doors in the image and determine their status.

Analyze the image and respond ONLY with valid JSON in this exact format:
{
  "door_visible": true or false,
  "door_open": true or false (null if no door visible),
  "opening_percentage": 0 to 100 (estimated percentage the door is open, 0=fully closed, 100=fully open, null if not visible),
  "door_type": "barn door" or "regular door" or "sliding door" or "garage door" or "other" (null if not visible),
  "confidence": 0.0 to 1.0,
  "reasoning": "Detailed explanation of what you see and how you determined the door status",
  "visual_evidence": "Specific visual details like door frame, hinges, opening gap, shadows, interior visibility"
}''',
        'water_level': '''You are analyzing a trail camera image from a ranch. Look for water troughs, tanks, or containers and assess the water level.

Analyze the image and respond ONLY with valid JSON in this exact format:
{
  "water_visible": true or false,
  "water_level": "FULL" or "ADEQUATE" or "LOW" or "EMPTY" (null if no water container visible),
  "percentage_estimate": 0 to 100 (null if not applicable),
  "confidence": 0.0 to 1.0,
  "reasoning": "Detailed explanation of your water level assessment",
  "visual_evidence": "Specific details about water color, reflections, container fill line, or moisture marks"
}''',
        'animal_detection': '''You are analyzing a trail camera image from a ranch. Identify any animals in the image.

Analyze the image and respond ONLY with valid JSON in this exact format:
{
  "animals_detected": true or false,
  "animals": [
    {
      "species": "specific animal name",
      "count": number of this species visible,
      "type": "livestock" or "wildlife",
      "confidence": 0.0 to 1.0,
      "location": "where in the image (e.g., left foreground, center background)",
      "behavior": "what the animal is doing (e.g., grazing, walking, resting)"
    }
  ],
  "confidence": 0.0 to 1.0,
  "reasoning": "Detailed explanation of how you identified each animal",
  "visual_evidence": "Specific features used for identification (e.g., body shape, coloring, size)"
}''',
        'feed_bin_status': '''You are analyzing a trail camera image from a ranch. Look for feed bins, feeders, or hay storage and assess their status.

Analyze the image and respond ONLY with valid JSON in this exact format:
{
  "feeder_visible": true or false,
  "feed_level": "FULL" or "ADEQUATE" or "LOW" or "EMPTY" (null if no feeder visible),
  "percentage_estimate": 0 to 100 (null if not applicable),
  "confidence": 0.0 to 1.0,
  "reasoning": "Detailed explanation of your feed level assessment",
  "visual_evidence": "Specific details about feed visibility, bin shadows, or fill indicators",
  "concerns": "Any maintenance issues, damage, or other concerns noticed (null if none)"
}'''
    }
    return prompts.get(analysis_type, prompts['animal_detection'])


def calculate_token_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost based on actual token counts"""
    # Pricing per 1M tokens (as of 2024)
    costs = {
        'gpt-4o-mini': { 'input': 0.15, 'output': 0.60 },
        'gpt-4o': { 'input': 5.00, 'output': 15.00 },
        'gpt-4-turbo': { 'input': 10.00, 'output': 30.00 },
        'gpt-4-vision-preview': { 'input': 10.00, 'output': 30.00 },
        'gemini-1.5-flash': { 'input': 0.10, 'output': 0.40 },
        'gemini-2.0-flash-exp': { 'input': 0.00, 'output': 0.00 },
        'gemini-2.5-pro': { 'input': 1.25, 'output': 10.00 }
    }
    
    model_cost = costs.get(model_name, { 'input': 0, 'output': 0 })
    input_cost = (input_tokens / 1_000_000) * model_cost['input']
    output_cost = (output_tokens / 1_000_000) * model_cost['output']
    
    return input_cost + output_cost


@app.get("/api/stats/summary")
async def get_analysis_stats():
    try:
        # Get various statistics
        now = datetime.utcnow()
        today = now.date()
        week_ago = now - timedelta(days=7)
        
        # Total analyses today
        today_results = supabase.client.table('image_analysis_results').select(
            'id', count='exact'
        ).gte('created_at', today.isoformat()).execute()
        
        # Total analyses this week
        week_results = supabase.client.table('image_analysis_results').select(
            'id', count='exact'
        ).gte('created_at', week_ago.isoformat()).execute()
        
        # Active alerts
        active_alerts = supabase.client.table('analysis_alerts').select(
            'id', count='exact'
        ).is_('acknowledged_at', 'null').execute()
        
        # Pending tasks
        pending_tasks = supabase.client.table('analysis_tasks').select(
            'id', count='exact'
        ).eq('status', 'pending').execute()
        
        # Cost tracking from AI analysis logs
        # Helper function to calculate cost from records
        def calculate_period_cost(records):
            total_cost = 0.0
            for record in records:
                # First check if we have a pre-calculated estimated_cost
                if record.get('estimated_cost'):
                    total_cost += record['estimated_cost']
                # Otherwise calculate from tokens
                elif record.get('input_tokens') and record.get('output_tokens'):
                    # Use actual token counts
                    cost = calculate_token_cost(
                        record['model_name'], 
                        record['input_tokens'], 
                        record['output_tokens']
                    )
                    total_cost += cost
                elif record.get('tokens_used'):
                    # Estimate with 30/70 split
                    cost = calculate_token_cost(
                        record.get('model_name', 'gpt-4o-mini'),
                        int(record['tokens_used'] * 0.3),
                        int(record['tokens_used'] * 0.7)
                    )
                    total_cost += cost
            return total_cost
        
        # Get today's costs
        today_str = today.isoformat()
        tomorrow_str = (today + timedelta(days=1)).isoformat()
        
        today_logs = supabase.client.table('ai_analysis_logs').select(
            'model_name, input_tokens, output_tokens, tokens_used, estimated_cost'
        ).gte('created_at', today_str).lt('created_at', tomorrow_str).execute()
        
        today_cost = calculate_period_cost(today_logs.data if today_logs.data else [])
        
        # Get this week's costs
        week_logs = supabase.client.table('ai_analysis_logs').select(
            'model_name, input_tokens, output_tokens, tokens_used, estimated_cost'
        ).gte('created_at', week_ago.isoformat()).execute()
        
        week_cost = calculate_period_cost(week_logs.data if week_logs.data else [])
        
        # Get all-time costs
        all_time_logs = supabase.client.table('ai_analysis_logs').select(
            'model_name, input_tokens, output_tokens, tokens_used, estimated_cost'
        ).execute()
        
        all_time_cost = calculate_period_cost(all_time_logs.data if all_time_logs.data else [])
        
        # Log for debugging
        print(f"Cost calculation - Today: ${today_cost:.4f}, Week: ${week_cost:.4f}, All-time: ${all_time_cost:.4f}")
        print(f"Today logs count: {len(today_logs.data) if today_logs.data else 0}")
        print(f"Week logs count: {len(week_logs.data) if week_logs.data else 0}")
        print(f"All-time logs count: {len(all_time_logs.data) if all_time_logs.data else 0}")
        
        return {
            "stats": {
                "analyses_today": today_results.count or 0,
                "analyses_week": week_results.count or 0,
                "active_alerts": active_alerts.count or 0,
                "pending_tasks": pending_tasks.count or 0,
                "cost_today": round(today_cost, 6),
                "cost_week": round(week_cost, 6),
                "cost_all_time": round(all_time_cost, 6)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/costs/check")
async def check_costs_in_db():
    """Check what costs are actually in the database"""
    try:
        # Get today's logs
        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)
        
        today_logs = supabase.client.table('ai_analysis_logs').select(
            'id, created_at, model_name, tokens_used, input_tokens, output_tokens, estimated_cost'
        ).gte('created_at', today.isoformat()).lt('created_at', tomorrow.isoformat()).order('created_at', desc=True).limit(10).execute()
        
        # Check if columns exist
        sample_log = today_logs.data[0] if today_logs.data else {}
        
        return {
            'database_check': {
                'today_records': len(today_logs.data) if today_logs.data else 0,
                'has_input_tokens_column': 'input_tokens' in sample_log,
                'has_output_tokens_column': 'output_tokens' in sample_log,
                'has_estimated_cost_column': 'estimated_cost' in sample_log,
            },
            'recent_logs': today_logs.data if today_logs.data else [],
            'instructions': {
                'if_missing_columns': 'Run the SQL in database/ALTER_TABLE_add_tokens.sql in Supabase SQL Editor',
                'sql_to_run': """
                    ALTER TABLE ai_analysis_logs 
                    ADD COLUMN IF NOT EXISTS input_tokens INTEGER;
                    
                    ALTER TABLE ai_analysis_logs 
                    ADD COLUMN IF NOT EXISTS output_tokens INTEGER;
                """
            }
        }
    except Exception as e:
        return {'error': str(e)}


@app.get("/api/stats/debug")
async def debug_cost_calculation():
    """Debug endpoint to check cost calculation"""
    try:
        # Get all AI analysis logs
        all_logs = supabase.client.table('ai_analysis_logs').select(
            'id, created_at, model_name, input_tokens, output_tokens, tokens_used, estimated_cost'
        ).order('created_at', desc=True).limit(10).execute()
        
        # Calculate costs for each record
        debug_info = []
        for log in (all_logs.data or []):
            record_info = {
                'id': log['id'],
                'created_at': log['created_at'],
                'model_name': log.get('model_name', 'unknown'),
                'input_tokens': log.get('input_tokens'),
                'output_tokens': log.get('output_tokens'),
                'tokens_used': log.get('tokens_used'),
                'estimated_cost': log.get('estimated_cost'),
                'calculated_cost': 0
            }
            
            # Calculate cost
            if log.get('input_tokens') and log.get('output_tokens'):
                record_info['calculated_cost'] = calculate_token_cost(
                    log.get('model_name', 'gpt-4o-mini'),
                    log['input_tokens'],
                    log['output_tokens']
                )
                record_info['cost_method'] = 'exact_tokens'
            elif log.get('tokens_used'):
                record_info['calculated_cost'] = calculate_token_cost(
                    log.get('model_name', 'gpt-4o-mini'),
                    int(log['tokens_used'] * 0.3),
                    int(log['tokens_used'] * 0.7)
                )
                record_info['cost_method'] = 'estimated_split'
            else:
                record_info['cost_method'] = 'no_token_data'
            
            debug_info.append(record_info)
        
        # Get summary stats
        stats = await get_analysis_stats()
        
        return {
            'current_stats': stats['stats'],
            'recent_logs': debug_info,
            'total_records': len(all_logs.data) if all_logs.data else 0
        }
    except Exception as e:
        return {'error': str(e)}


@app.post("/api/upload/analyze")
async def upload_and_analyze(
    file: UploadFile = File(...),
    camera_name: str = "Manual Upload",
    analysis_type: str = "gate_detection"
):
    try:
        # Read image
        contents = await file.read()
        
        # Create temporary image data
        image_data = ImageData(
            image_bytes=contents,
            image_id=f"upload-{datetime.utcnow().timestamp()}",
            camera_name=camera_name,
            captured_at=datetime.utcnow().isoformat()
        )
        
        # Get appropriate config
        configs = await supabase.get_active_configs()
        config = next(
            (c for c in configs if c['analysis_type'] == analysis_type),
            None
        )
        
        if not config:
            raise HTTPException(status_code=400, detail="No config found for analysis type")
        
        # Run analysis directly
        api_keys = {
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY')
        }
        
        results = await analysis_service.analyze_with_dual_models(
            image_data,
            config,
            api_keys.get(config['model_provider'].upper() + '_API_KEY'),
            api_keys.get(config.get('secondary_provider', '').upper() + '_API_KEY'),
            api_keys.get(config.get('tiebreaker_provider', '').upper() + '_API_KEY')
        )
        
        return {
            "analysis": results['final_result'],
            "confidence": results['final_result'].get('confidence', 0),
            "agreement": results['agreement'],
            "tiebreaker_used": results['tiebreaker_used']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and wait for messages
            data = await websocket.receive_text()
            
            # Echo back or handle commands
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Background task to broadcast updates
async def broadcast_updates():
    while True:
        try:
            # Get current stats
            stats = await get_analysis_stats()
            
            # Broadcast to all connected clients
            await manager.broadcast({
                "type": "stats_update",
                "data": stats["stats"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            await asyncio.sleep(10)  # Update every 10 seconds
        except Exception as e:
            print(f"Broadcast error: {e}")
            await asyncio.sleep(30)


# Start background tasks on startup
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_updates())


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)