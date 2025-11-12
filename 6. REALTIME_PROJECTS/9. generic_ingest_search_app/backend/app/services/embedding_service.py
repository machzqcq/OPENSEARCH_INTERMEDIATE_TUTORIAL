"""
Embedding model management service
"""
import logging
import time
import asyncio
from typing import List, Dict
from app.services.opensearch_service import OpenSearchService
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Manages embedding models deployment and tracking"""
    
    def __init__(self, os_service: OpenSearchService):
        self.os_service = os_service
        self.deployed_models: Dict[str, dict] = {}
    
    async def initialize_models(self):
        """Initialize and deploy embedding models"""
        logger.info("Initializing embedding models...")
        
        for model_config in settings.EMBEDDING_MODELS:
            try:
                logger.info(f"Deploying model: {model_config['name']}")
                model_info = await self._deploy_model(model_config)
                self.deployed_models[model_config['name']] = model_info
                logger.info(f"✓ Model {model_config['name']} deployed successfully")
            except Exception as e:
                logger.error(f"✗ Failed to deploy model {model_config['name']}: {e}")
        
        logger.info(f"Total models deployed: {len(self.deployed_models)}")
    
    async def _deploy_model(self, model_config: dict) -> dict:
        """Deploy a single embedding model"""
        # Register model
        register_body = {
            "name": model_config['model_name'],
            "version": model_config['version'],
            "model_format": "TORCH_SCRIPT"
        }
        
        register_response = self.os_service.register_model(register_body)
        task_id = register_response.get('task_id')
        
        # Wait for registration
        model_id = await self._wait_for_registration(task_id)
        
        # Deploy model
        try:
            self.os_service.deploy_model(model_id)
        except Exception as e:
            logger.warning(f"Deploy call error (may already be deploying): {e}")
        
        # Wait for deployment
        await self._wait_for_deployment(model_id)
        
        return {
            "model_id": model_id,
            "name": model_config['name'],
            "dimension": model_config['dimension'],
            "description": model_config['description'],
            "status": "DEPLOYED"
        }
    
    async def _wait_for_registration(self, task_id: str, timeout: int = 300) -> str:
        """Wait for model registration to complete"""
        start_time = time.time()
        
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Model registration timeout for task {task_id}")
            
            task_status = self.os_service.get_task_status(task_id)
            state = task_status.get('state')
            
            if state == 'COMPLETED':
                model_id = task_status.get('model_id')
                logger.info(f"Model registered with ID: {model_id}")
                return model_id
            elif state == 'FAILED':
                error = task_status.get('error', 'Unknown error')
                raise Exception(f"Model registration failed: {error}")
            
            await asyncio.sleep(5)
    
    async def _wait_for_deployment(self, model_id: str, timeout: int = 300):
        """Wait for model deployment to complete"""
        start_time = time.time()
        
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Model deployment timeout for {model_id}")
            
            status_response = self.os_service.get_model_status(model_id)
            state = status_response.get('model_state')
            
            if state == 'DEPLOYED':
                logger.info(f"Model {model_id} deployed successfully")
                return
            elif state == 'FAILED':
                raise Exception(f"Model deployment failed for {model_id}")
            
            await asyncio.sleep(5)
    
    def get_available_models(self) -> List[dict]:
        """Get list of available deployed models"""
        return [
            {
                "model_id": info["model_id"],
                "name": info["name"],
                "dimension": info["dimension"],
                "description": info["description"],
                "status": info["status"]
            }
            for info in self.deployed_models.values()
        ]
    
    def get_model_by_name(self, name: str) -> dict:
        """Get model info by name"""
        return self.deployed_models.get(name)
    
    def get_model_dimension(self, model_id: str) -> int:
        """Get model dimension by model_id"""
        for model_info in self.deployed_models.values():
            if model_info["model_id"] == model_id:
                return model_info["dimension"]
        raise ValueError(f"Model {model_id} not found")
