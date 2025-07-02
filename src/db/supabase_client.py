from supabase import create_client, Client
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import aiohttp
import asyncio


logger = logging.getLogger(__name__)


class SupabaseClient:
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)
        self.storage_bucket = "spypoint-images"
        
    async def get_analysis_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.client.table('analysis_tasks').select('*').eq('id', task_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None
    
    async def get_analysis_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.client.table('analysis_configs').select('*').eq('id', config_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Error getting config {config_id}: {e}")
            return None
    
    async def get_image_metadata(self, image_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.client.table('spypoint_images').select('*').eq('image_id', image_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Error getting image metadata {image_id}: {e}")
            return None
    
    async def download_image(self, storage_path: str) -> bytes:
        try:
            # Generate signed URL for private bucket access
            signed_url = self.client.storage.from_(self.storage_bucket).create_signed_url(
                storage_path,
                expires_in=300  # 5 minutes
            )
            
            # Download image bytes
            async with aiohttp.ClientSession() as session:
                async with session.get(signed_url['signedURL']) as response:
                    return await response.read()
                    
        except Exception as e:
            logger.error(f"Error downloading image {storage_path}: {e}")
            raise
    
    async def update_task_status(
        self, 
        task_id: str, 
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if status == 'processing':
                update_data['started_at'] = datetime.utcnow().isoformat()
            elif status == 'completed':
                update_data['completed_at'] = datetime.utcnow().isoformat()
            elif status == 'failed' and error_message:
                update_data['error_message'] = error_message
                update_data['retry_count'] = self.client.table('analysis_tasks').select('retry_count').eq('id', task_id).single().execute().data['retry_count'] + 1
            
            self.client.table('analysis_tasks').update(update_data).eq('id', task_id).execute()
            return True
            
        except Exception as e:
            logger.error(f"Error updating task status {task_id}: {e}")
            return False
    
    async def save_analysis_result(self, result_data: Dict[str, Any]) -> Optional[str]:
        try:
            response = self.client.table('image_analysis_results').insert(result_data).execute()
            return response.data[0]['id']
        except Exception as e:
            logger.error(f"Error saving analysis result: {e}")
            return None
    
    async def create_alert(self, alert_data: Dict[str, Any]) -> Optional[str]:
        try:
            response = self.client.table('analysis_alerts').insert(alert_data).execute()
            return response.data[0]['id']
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return None
    
    async def get_pending_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            response = self.client.table('analysis_tasks').select('*').eq(
                'status', 'pending'
            ).order('priority', desc=True).order('scheduled_at').limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error getting pending tasks: {e}")
            return []
    
    async def get_active_configs(self, camera_name: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            query = self.client.table('analysis_configs').select('*').eq('active', True)
            
            if camera_name:
                # Get configs for specific camera or configs that apply to all cameras
                query = query.or_(f'camera_name.eq.{camera_name},camera_name.is.null')
            
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Error getting active configs: {e}")
            return []
    
    async def create_analysis_tasks_for_image(self, image_id: str) -> int:
        try:
            # Get image metadata to find camera name
            image = await self.get_image_metadata(image_id)
            if not image:
                return 0
            
            # Get applicable configs
            configs = await self.get_active_configs(image['camera_name'])
            
            # Create tasks
            tasks_created = 0
            for config in configs:
                task_data = {
                    'image_id': image_id,
                    'config_id': config['id'],
                    'priority': 5,
                    'status': 'pending'
                }
                
                try:
                    self.client.table('analysis_tasks').insert(task_data).execute()
                    tasks_created += 1
                except Exception as e:
                    # Likely duplicate task, ignore
                    logger.debug(f"Task creation failed (likely duplicate): {e}")
            
            return tasks_created
            
        except Exception as e:
            logger.error(f"Error creating tasks for image {image_id}: {e}")
            return 0
    
    async def check_cache(
        self, 
        image_hash: str, 
        analysis_type: str,
        provider: str,
        model: str
    ) -> Optional[Dict[str, Any]]:
        try:
            response = self.client.table('analysis_cache').select('*').eq(
                'image_hash', image_hash
            ).eq('analysis_type', analysis_type).eq(
                'model_provider', provider
            ).eq('model_name', model).single().execute()
            
            if response.data:
                # Check if cache is still valid
                expires_at = datetime.fromisoformat(response.data['expires_at'].replace('Z', '+00:00'))
                if expires_at > datetime.utcnow():
                    return response.data
                    
            return None
            
        except Exception:
            return None
    
    async def save_to_cache(
        self,
        image_hash: str,
        analysis_type: str,
        provider: str,
        model: str,
        result: Dict[str, Any],
        confidence: float,
        cache_hours: int = 24
    ) -> None:
        try:
            cache_data = {
                'image_hash': image_hash,
                'analysis_type': analysis_type,
                'model_provider': provider,
                'model_name': model,
                'result': result,
                'confidence': confidence,
                'expires_at': (datetime.utcnow() + timedelta(hours=cache_hours)).isoformat()
            }
            
            self.client.table('analysis_cache').upsert(cache_data).execute()
            
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
    
    async def update_cost_tracking(
        self,
        provider: str,
        model: str,
        tokens_used: int,
        estimated_cost: float
    ) -> None:
        try:
            today = datetime.utcnow().date().isoformat()
            
            # Try to get existing record
            response = self.client.table('analysis_costs').select('*').eq(
                'date', today
            ).eq('model_provider', provider).eq('model_name', model).single().execute()
            
            if response.data:
                # Update existing record
                update_data = {
                    'analysis_count': response.data['analysis_count'] + 1,
                    'tokens_used': response.data['tokens_used'] + tokens_used,
                    'estimated_cost': response.data['estimated_cost'] + estimated_cost
                }
                self.client.table('analysis_costs').update(update_data).eq('id', response.data['id']).execute()
            else:
                # Create new record
                self.client.table('analysis_costs').insert({
                    'date': today,
                    'model_provider': provider,
                    'model_name': model,
                    'analysis_count': 1,
                    'tokens_used': tokens_used,
                    'estimated_cost': estimated_cost
                }).execute()
                
        except Exception as e:
            logger.error(f"Error updating cost tracking: {e}")
    
    async def save_ai_analysis_log(
        self,
        image_id: str,
        image_url: Optional[str],
        camera_name: Optional[str],
        captured_at: Optional[str],
        analysis_type: str,
        prompt_text: str,
        custom_prompt: bool,
        model_provider: str,
        model_name: str,
        raw_response: str,
        parsed_response: Optional[Dict[str, Any]],
        confidence: Optional[float],
        analysis_successful: bool,
        error_message: Optional[str],
        processing_time_ms: Optional[int],
        tokens_used: Optional[int],
        config_id: Optional[str] = None,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_initiated: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        model_temperature: float = 0.3,
        max_tokens: int = 500,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        estimated_cost: Optional[float] = None
    ) -> Optional[str]:
        """Save comprehensive AI analysis log entry"""
        try:
            log_data = {
                'image_id': image_id,
                'image_url': image_url,
                'camera_name': camera_name,
                'captured_at': captured_at,
                'analysis_type': analysis_type,
                'prompt_text': prompt_text,
                'custom_prompt': custom_prompt,
                'model_provider': model_provider,
                'model_name': model_name,
                'model_temperature': model_temperature,
                'max_tokens': max_tokens,
                'raw_response': raw_response,
                'parsed_response': parsed_response,
                'confidence': confidence,
                'analysis_successful': analysis_successful,
                'error_message': error_message,
                'processing_time_ms': processing_time_ms,
                'tokens_used': tokens_used,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'estimated_cost': estimated_cost,
                'config_id': config_id,
                'task_id': task_id,
                'session_id': session_id,
                'user_initiated': user_initiated,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'notes': notes,
                'tags': tags
            }
            
            # Remove None values to avoid inserting nulls unnecessarily
            log_data = {k: v for k, v in log_data.items() if v is not None}
            
            response = self.client.table('ai_analysis_logs').insert(log_data).execute()
            return response.data[0]['id']
            
        except Exception as e:
            logger.error(f"Error saving AI analysis log: {e}")
            return None
    
    async def get_recent_ai_analysis_logs(
        self,
        limit: int = 50,
        user_initiated_only: bool = False,
        analysis_type: Optional[str] = None,
        model_provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent AI analysis logs with optional filtering"""
        try:
            query = self.client.table('ai_analysis_logs').select('*')
            
            if user_initiated_only:
                query = query.eq('user_initiated', True)
            
            if analysis_type:
                query = query.eq('analysis_type', analysis_type)
                
            if model_provider:
                query = query.eq('model_provider', model_provider)
            
            response = query.order('created_at', desc=True).limit(limit).execute()
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting AI analysis logs: {e}")
            return []
    
    async def get_analysis_cost_summary(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get cost summary from AI analysis logs"""
        try:
            query = self.client.table('ai_analysis_logs').select(
                'model_provider,model_name,estimated_cost,tokens_used,created_at'
            )
            
            if start_date:
                query = query.gte('created_at', start_date)
            if end_date:
                query = query.lte('created_at', end_date)
            
            response = query.execute()
            
            # Calculate summary statistics
            total_cost = sum(log.get('estimated_cost', 0) or 0 for log in response.data)
            total_tokens = sum(log.get('tokens_used', 0) or 0 for log in response.data)
            total_analyses = len(response.data)
            
            # Group by provider
            by_provider = {}
            for log in response.data:
                provider = log.get('model_provider', 'unknown')
                if provider not in by_provider:
                    by_provider[provider] = {
                        'count': 0,
                        'total_cost': 0,
                        'total_tokens': 0
                    }
                by_provider[provider]['count'] += 1
                by_provider[provider]['total_cost'] += log.get('estimated_cost', 0) or 0
                by_provider[provider]['total_tokens'] += log.get('tokens_used', 0) or 0
            
            return {
                'total_analyses': total_analyses,
                'total_cost': total_cost,
                'total_tokens': total_tokens,
                'avg_cost_per_analysis': total_cost / max(total_analyses, 1),
                'by_provider': by_provider
            }
            
        except Exception as e:
            logger.error(f"Error getting cost summary: {e}")
            return {
                'total_analyses': 0,
                'total_cost': 0,
                'total_tokens': 0,
                'avg_cost_per_analysis': 0,
                'by_provider': {}
            }