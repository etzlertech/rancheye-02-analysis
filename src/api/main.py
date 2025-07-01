from fastapi import FastAPI, HTTPException, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
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

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db.supabase_client import SupabaseClient
from src.services.analysis_service import AnalysisService
from src.task_processor import TaskProcessor
from src.providers.base import ImageData
from dotenv import load_dotenv


load_dotenv()

app = FastAPI(title="RanchEye Analysis API", version="1.0.0")

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
    try:
        # Simple query to test connection
        response = supabase.client.table('spypoint_images').select('id').limit(1).execute()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "env_vars": env_status,
        "database": db_status
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
async def get_recent_images(limit: int = 20):
    try:
        print(f"Fetching recent images with limit: {limit}")
        response = supabase.client.table('spypoint_images').select('*').order(
            'downloaded_at', desc=True
        ).limit(limit).execute()
        print(f"Found {len(response.data)} images")
        return {"images": response.data}
    except Exception as e:
        print(f"Error fetching images: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        
        # Get API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Run analysis directly
        result = await analysis_service.analyze_with_dual_models(
            image_data,
            test_config,
            api_key
        )
        
        # Format response for frontend
        primary_result = result.get('primary_result')
        if primary_result:
            return {
                'analysis_type': analysis_type,
                'confidence': result['final_result'].get('confidence', 0.95),
                'model_provider': test_config['model_provider'],
                'model_name': test_config['model_name'],
                'result': result['final_result'],
                'tokens_used': primary_result.tokens_used,
                'processing_time_ms': primary_result.processing_time_ms
            }
        else:
            return {
                'analysis_type': analysis_type,
                'confidence': 0,
                'model_provider': test_config['model_provider'],
                'model_name': test_config['model_name'],
                'result': {'error': 'Analysis failed'},
                'tokens_used': 0,
                'processing_time_ms': 0
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_test_prompt(analysis_type: str) -> str:
    """Get prompt template for test analysis types"""
    prompts = {
        'gate_detection': 'Analyze this trail camera image and determine if a gate is visible. If a gate is visible, determine if it is OPEN or CLOSED. Provide detailed reasoning for your decision. Respond with JSON: {"gate_visible": boolean, "gate_open": boolean, "confidence": float between 0-1, "reasoning": "detailed explanation of what you see and why you made this decision", "visual_evidence": "specific visual details that support your conclusion"}',
        'water_level': 'Analyze this trail camera image for water troughs or containers. Estimate the water level and provide detailed reasoning. Respond with JSON: {"water_visible": boolean, "water_level": "FULL|ADEQUATE|LOW|EMPTY", "percentage_estimate": number 0-100, "confidence": float between 0-1, "reasoning": "detailed explanation of your assessment", "visual_evidence": "specific visual details about water color, reflections, container fill level"}',
        'animal_detection': 'Analyze this trail camera image for any animals. Provide detailed information about each animal detected. Respond with JSON: {"animals_detected": boolean, "animals": [{"species": "name", "count": number, "type": "livestock|wildlife", "confidence": float, "location": "where in image", "behavior": "what they are doing"}], "reasoning": "detailed explanation of identifications", "visual_evidence": "specific features used for identification"}',
        'feed_bin_status': 'Analyze this trail camera image for feed bins or feeders. Assess the feed level and condition. Respond with JSON: {"feeder_visible": boolean, "feed_level": "FULL|ADEQUATE|LOW|EMPTY", "percentage_estimate": number 0-100, "confidence": float between 0-1, "reasoning": "detailed explanation of assessment", "visual_evidence": "specific visual details about feed visibility and bin condition", "concerns": "any issues noticed"}'
    }
    return prompts.get(analysis_type, prompts['animal_detection'])


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
        
        # Cost tracking
        costs = supabase.client.table('analysis_costs').select(
            'estimated_cost'
        ).gte('date', today.isoformat()).execute()
        
        today_cost = sum(c['estimated_cost'] for c in costs.data) if costs.data else 0
        
        return {
            "stats": {
                "analyses_today": today_results.count or 0,
                "analyses_week": week_results.count or 0,
                "active_alerts": active_alerts.count or 0,
                "pending_tasks": pending_tasks.count or 0,
                "cost_today": round(today_cost, 4)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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