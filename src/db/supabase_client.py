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