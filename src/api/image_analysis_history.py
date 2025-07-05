"""
API endpoint for viewing analysis history for any image
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db.supabase_client import SupabaseClient
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api", tags=["image-history"])

# Initialize Supabase client
supabase = SupabaseClient(
    url=os.getenv('SUPABASE_URL'),
    key=os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
)


@router.get("/analysis-history")
async def get_all_analysis_history(
    limit: int = 100,
    offset: int = 0,
    analysis_type: str = None,
    model_provider: str = None,
    camera_name: str = None
) -> Dict[str, Any]:
    """
    Get analysis history for all images with filtering options
    Returns analysis logs with image information and thumbnails
    """
    try:
        # Build query - first get the analysis logs
        query = supabase.client.table('ai_analysis_logs').select('*')
        
        # Apply filters
        if analysis_type:
            query = query.eq('analysis_type', analysis_type)
        if model_provider:
            query = query.eq('model_provider', model_provider)
        if camera_name:
            query = query.eq('camera_name', camera_name)
            
        # Add pagination and ordering
        query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
        
        response = query.execute()
        analyses = response.data if response.data else []
        
        # Get unique image IDs from the analyses
        image_ids = list(set(a['image_id'] for a in analyses if a.get('image_id')))
        
        # Fetch image data separately
        image_data = {}
        if image_ids:
            images_response = supabase.client.table('spypoint_images').select(
                'image_id, storage_path, camera_name, downloaded_at'
            ).in_('image_id', image_ids).execute()
            
            for img in (images_response.data or []):
                image_data[img['image_id']] = img
        
        # Get total count for pagination
        count_query = supabase.client.table('ai_analysis_logs').select('*', count='exact')
        if analysis_type:
            count_query = count_query.eq('analysis_type', analysis_type)
        if model_provider:
            count_query = count_query.eq('model_provider', model_provider)
        if camera_name:
            count_query = count_query.eq('camera_name', camera_name)
        
        count_response = count_query.execute()
        total_count = count_response.count if hasattr(count_response, 'count') else len(analyses)
        
        # Process results to include image URLs and group by session
        processed_results = []
        sessions_map = {}
        
        for analysis in analyses:
            # Add image info from our lookup
            if analysis.get('image_id') and analysis['image_id'] in image_data:
                img_info = image_data[analysis['image_id']]
                # Generate the full image URL from storage path
                storage_path = img_info.get('storage_path')
                if storage_path:
                    # Construct the public URL for the image
                    analysis['image_url'] = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/{storage_path}"
                else:
                    analysis['image_url'] = analysis.get('image_url')
                analysis['camera_name'] = img_info.get('camera_name') or analysis.get('camera_name')
                analysis['captured_at'] = img_info.get('downloaded_at')
            else:
                analysis['image_url'] = analysis.get('image_url')
                analysis['captured_at'] = None
            
            # Group by session if applicable
            session_id = analysis.get('session_id')
            if session_id:
                if session_id not in sessions_map:
                    sessions_map[session_id] = {
                        'session_id': session_id,
                        'image_id': analysis['image_id'],
                        'image_url': analysis['image_url'],
                        'camera_name': analysis['camera_name'],
                        'captured_at': analysis['captured_at'],
                        'created_at': analysis['created_at'],
                        'analysis_type': analysis['analysis_type'],
                        'prompt_text': analysis['prompt_text'],
                        'custom_prompt': analysis['custom_prompt'],
                        'models': [],
                        'total_cost': 0,
                        'total_tokens': 0
                    }
                
                sessions_map[session_id]['models'].append({
                    'model_provider': analysis['model_provider'],
                    'model_name': analysis['model_name'],
                    'success': analysis['analysis_successful'],
                    'confidence': analysis.get('confidence'),
                    'tokens_used': analysis.get('tokens_used'),
                    'estimated_cost': analysis.get('estimated_cost'),
                    'processing_time_ms': analysis.get('processing_time_ms'),
                    'quality_rating': analysis.get('quality_rating'),
                    'user_notes': analysis.get('user_notes')
                })
                
                sessions_map[session_id]['total_cost'] += analysis.get('estimated_cost', 0) or 0
                sessions_map[session_id]['total_tokens'] += analysis.get('tokens_used', 0) or 0
            else:
                # Standalone analysis
                processed_results.append({
                    'id': analysis['id'],
                    'image_id': analysis['image_id'],
                    'image_url': analysis['image_url'],
                    'camera_name': analysis['camera_name'],
                    'captured_at': analysis['captured_at'],
                    'created_at': analysis['created_at'],
                    'analysis_type': analysis['analysis_type'],
                    'model_provider': analysis['model_provider'],
                    'model_name': analysis['model_name'],
                    'analysis_successful': analysis['analysis_successful'],
                    'confidence': analysis.get('confidence'),
                    'tokens_used': analysis.get('tokens_used'),
                    'estimated_cost': analysis.get('estimated_cost'),
                    'processing_time_ms': analysis.get('processing_time_ms'),
                    'prompt_text': analysis.get('prompt_text'),
                    'custom_prompt': analysis.get('custom_prompt'),
                    'quality_rating': analysis.get('quality_rating'),
                    'user_notes': analysis.get('user_notes'),
                    'notes_updated_at': analysis.get('notes_updated_at'),
                    'parsed_response': analysis.get('parsed_response'),
                    'is_session': False
                })
        
        # Add sessions to results
        for session in sessions_map.values():
            processed_results.append({
                **session,
                'is_session': True
            })
        
        # Sort by created_at
        processed_results.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Get summary stats
        stats_response = supabase.client.table('ai_analysis_logs').select(
            'analysis_successful, estimated_cost'
        ).execute()
        
        all_analyses = stats_response.data if stats_response.data else []
        total_cost = sum(a.get('estimated_cost', 0) or 0 for a in all_analyses)
        successful_count = sum(1 for a in all_analyses if a.get('analysis_successful'))
        
        return {
            'analyses': processed_results[:limit],
            'total_count': total_count,
            'page_size': limit,
            'offset': offset,
            'summary': {
                'total_analyses': len(all_analyses),
                'successful_analyses': successful_count,
                'failed_analyses': len(all_analyses) - successful_count,
                'total_cost': round(total_cost, 6)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images/{image_id}/analysis-history")
async def get_image_analysis_history(image_id: str) -> Dict[str, Any]:
    """
    Get complete analysis history for a specific image
    Returns all AI analysis attempts for this image
    """
    try:
        # Get all analysis logs for this image
        response = supabase.client.table('ai_analysis_logs').select(
            '*'
        ).eq('image_id', image_id).order('created_at', desc=True).execute()
        
        analyses = response.data if response.data else []
        
        # Group by session_id to identify multi-model comparisons
        sessions = {}
        standalone = []
        
        for analysis in analyses:
            session_id = analysis.get('session_id')
            if session_id:
                if session_id not in sessions:
                    sessions[session_id] = {
                        'session_id': session_id,
                        'created_at': analysis['created_at'],
                        'analysis_type': analysis['analysis_type'],
                        'models': [],
                        'prompt_text': analysis['prompt_text'],
                        'custom_prompt': analysis['custom_prompt']
                    }
                sessions[session_id]['models'].append({
                    'model_provider': analysis['model_provider'],
                    'model_name': analysis['model_name'],
                    'success': analysis['analysis_successful'],
                    'confidence': analysis.get('confidence'),
                    'tokens_used': analysis.get('tokens_used'),
                    'input_tokens': analysis.get('input_tokens'),
                    'output_tokens': analysis.get('output_tokens'),
                    'estimated_cost': analysis.get('estimated_cost'),
                    'error_message': analysis.get('error_message'),
                    'processing_time_ms': analysis.get('processing_time_ms')
                })
            else:
                standalone.append(analysis)
        
        # Convert sessions dict to list
        session_list = list(sessions.values())
        
        # Calculate summary statistics
        total_analyses = len(analyses)
        total_cost = sum(a.get('estimated_cost', 0) or 0 for a in analyses)
        successful_analyses = sum(1 for a in analyses if a.get('analysis_successful'))
        
        # Get unique analysis types used
        analysis_types = list(set(a['analysis_type'] for a in analyses))
        
        # Get unique models used
        models_used = list(set(f"{a['model_provider']}/{a['model_name']}" for a in analyses))
        
        return {
            'image_id': image_id,
            'total_analyses': total_analyses,
            'successful_analyses': successful_analyses,
            'failed_analyses': total_analyses - successful_analyses,
            'total_cost': round(total_cost, 6),
            'analysis_types': analysis_types,
            'models_used': models_used,
            'multi_model_sessions': session_list,
            'standalone_analyses': standalone,
            'all_analyses': analyses  # Raw data if needed
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images/{image_id}/analysis-history/{session_id}")
async def get_session_details(image_id: str, session_id: str) -> Dict[str, Any]:
    """
    Get detailed results for a specific analysis session
    """
    try:
        # Get all analyses for this session
        response = supabase.client.table('ai_analysis_logs').select(
            '*'
        ).eq('image_id', image_id).eq('session_id', session_id).order('created_at').execute()
        
        analyses = response.data if response.data else []
        
        if not analyses:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Build detailed response
        return {
            'session_id': session_id,
            'image_id': image_id,
            'created_at': analyses[0]['created_at'],
            'analysis_type': analyses[0]['analysis_type'],
            'prompt_text': analyses[0]['prompt_text'],
            'custom_prompt': analyses[0]['custom_prompt'],
            'model_results': [
                {
                    'model_provider': a['model_provider'],
                    'model_name': a['model_name'],
                    'success': a['analysis_successful'],
                    'confidence': a.get('confidence'),
                    'raw_response': a.get('raw_response'),
                    'parsed_response': a.get('parsed_response'),
                    'tokens_used': a.get('tokens_used'),
                    'input_tokens': a.get('input_tokens'),
                    'output_tokens': a.get('output_tokens'),
                    'estimated_cost': a.get('estimated_cost'),
                    'error_message': a.get('error_message'),
                    'processing_time_ms': a.get('processing_time_ms')
                } for a in analyses
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Pydantic models for request validation
class UpdateRatingRequest(BaseModel):
    quality_rating: int
    
    class Config:
        json_schema_extra = {
            "example": {"quality_rating": 4}
        }


class UpdateNotesRequest(BaseModel):
    user_notes: str
    
    class Config:
        json_schema_extra = {
            "example": {"user_notes": "Good detection but missed one animal in background"}
        }


@router.patch("/analysis/{analysis_id}/rating")
async def update_analysis_rating(analysis_id: str, request: UpdateRatingRequest) -> Dict[str, Any]:
    """
    Update the quality rating for a specific analysis
    Rating must be between 1 and 5
    """
    try:
        # Validate rating
        if request.quality_rating < 1 or request.quality_rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        # Update the rating
        response = supabase.client.table('ai_analysis_logs').update({
            'quality_rating': request.quality_rating,
            'notes_updated_at': datetime.utcnow().isoformat()
        }).eq('id', analysis_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            'success': True,
            'analysis_id': analysis_id,
            'quality_rating': request.quality_rating,
            'updated_at': datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/analysis/{analysis_id}/notes")
async def update_analysis_notes(analysis_id: str, request: UpdateNotesRequest) -> Dict[str, Any]:
    """
    Update the user notes for a specific analysis
    """
    try:
        # Update the notes
        response = supabase.client.table('ai_analysis_logs').update({
            'user_notes': request.user_notes,
            'notes_updated_at': datetime.utcnow().isoformat()
        }).eq('id', analysis_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            'success': True,
            'analysis_id': analysis_id,
            'user_notes': request.user_notes,
            'updated_at': datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))