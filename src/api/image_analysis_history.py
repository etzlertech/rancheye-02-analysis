"""
API endpoint for viewing analysis history for any image
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db.supabase_client import SupabaseClient
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/images", tags=["image-history"])

# Initialize Supabase client
supabase = SupabaseClient(
    url=os.getenv('SUPABASE_URL'),
    key=os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
)


@router.get("/{image_id}/analysis-history")
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


@router.get("/{image_id}/analysis-history/{session_id}")
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