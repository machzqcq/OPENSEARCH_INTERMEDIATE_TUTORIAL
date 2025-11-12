"""
OpenSearch service for managing connections and operations
"""
import logging
from opensearchpy import OpenSearch
from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenSearchService:
    """OpenSearch client wrapper with common operations"""
    
    def __init__(self):
        """Initialize OpenSearch client"""
        self.client = self._create_client()
        self._configure_cluster()
    
    def _create_client(self) -> OpenSearch:
        """Create and return OpenSearch client"""
        cluster_url = {
            'host': settings.OPENSEARCH_HOST,
            'port': settings.OPENSEARCH_PORT
        }
        
        client = OpenSearch(
            hosts=[cluster_url],
            http_auth=(settings.OPENSEARCH_USERNAME, settings.OPENSEARCH_PASSWORD),
            use_ssl=settings.OPENSEARCH_USE_SSL,
            verify_certs=settings.OPENSEARCH_VERIFY_CERTS,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
            timeout=300
        )
        
        logger.info(f"OpenSearch client created for {settings.OPENSEARCH_HOST}:{settings.OPENSEARCH_PORT}")
        return client
    
    def _configure_cluster(self):
        """Configure cluster settings"""
        try:
            cluster_settings = {
                "persistent": {
                    "plugins.ml_commons.trusted_connector_endpoints_regex": "^https://api\\.openai\\.com/.*$",
                    "plugins.ml_commons.only_run_on_ml_node": "false",
                    "plugins.ml_commons.memory_feature_enabled": "true"
                }
            }
            self.client.cluster.put_settings(body=cluster_settings)
            logger.info("Cluster settings configured")
        except Exception as e:
            logger.warning(f"Failed to configure cluster settings: {e}")
    
    def check_health(self) -> dict:
        """Check cluster health"""
        return self.client.cluster.health()
    
    def index_exists(self, index_name: str) -> bool:
        """Check if index exists"""
        return self.client.indices.exists(index=index_name)
    
    def create_index(self, index_name: str, body: dict):
        """Create index with mappings and settings"""
        return self.client.indices.create(index=index_name, body=body)
    
    def delete_index(self, index_name: str):
        """Delete index"""
        if self.index_exists(index_name):
            return self.client.indices.delete(index=index_name)
    
    def bulk_index(self, body: list, index_name: str, pipeline_id: str = None):
        """Bulk index documents"""
        params = {}
        if pipeline_id:
            params['pipeline'] = pipeline_id
            logger.info(f"Bulk indexing to {index_name} with pipeline: {pipeline_id}")
        else:
            logger.info(f"Bulk indexing to {index_name} without pipeline")
        
        result = self.client.bulk(body=body, index=index_name, params=params)
        
        if result.get('errors'):
            logger.error(f"Bulk indexing had errors: {result}")
        else:
            logger.debug(f"Bulk indexing successful: {len(body)//2} documents")
        
        return result
    
    def search(self, index_name: str, body: dict):
        """Execute search query"""
        return self.client.search(index=index_name, body=body)
    
    def create_ingest_pipeline(self, pipeline_id: str, body: dict):
        """Create ingest pipeline"""
        return self.client.ingest.put_pipeline(id=pipeline_id, body=body)
    
    def get_ingest_pipeline(self, pipeline_id: str):
        """Get ingest pipeline"""
        return self.client.ingest.get_pipeline(id=pipeline_id)
    
    def delete_ingest_pipeline(self, pipeline_id: str):
        """Delete ingest pipeline"""
        return self.client.ingest.delete_pipeline(id=pipeline_id)
    
    def create_search_pipeline(self, pipeline_id: str, body: dict):
        """Create search pipeline"""
        return self.client.transport.perform_request(
            'PUT',
            f'/_search/pipeline/{pipeline_id}',
            body=body
        )
    
    def get_all_indices(self) -> list:
        """Get all indices"""
        try:
            indices = self.client.cat.indices(format='json')
            return [idx['index'] for idx in indices if not idx['index'].startswith('.')]
        except Exception as e:
            logger.error(f"Failed to get indices: {e}")
            return []
    
    def refresh_index(self, index_name: str):
        """Refresh index"""
        return self.client.indices.refresh(index=index_name)
    
    def register_model(self, body: dict):
        """Register ML model"""
        return self.client.transport.perform_request(
            'POST',
            '/_plugins/_ml/models/_register',
            body=body
        )
    
    def get_model_status(self, model_id: str):
        """Get model status"""
        return self.client.transport.perform_request(
            'GET',
            f'/_plugins/_ml/models/{model_id}'
        )
    
    def deploy_model(self, model_id: str):
        """Deploy model"""
        return self.client.transport.perform_request(
            'POST',
            f'/_plugins/_ml/models/{model_id}/_deploy'
        )
    
    def get_task_status(self, task_id: str):
        """Get task status"""
        return self.client.transport.perform_request(
            'GET',
            f'/_plugins/_ml/tasks/{task_id}'
        )
    
    def register_agent(self, body: dict):
        """Register agent"""
        return self.client.transport.perform_request(
            'POST',
            '/_plugins/_ml/agents/_register',
            body=body
        )
    
    def execute_agent(self, agent_id: str, body: dict):
        """Execute agent"""
        return self.client.transport.perform_request(
            'POST',
            f'/_plugins/_ml/agents/{agent_id}/_execute',
            body=body
        )
    
    def create_connector(self, body: dict):
        """Create connector"""
        return self.client.transport.perform_request(
            'POST',
            '/_plugins/_ml/connectors/_create',
            body=body
        )
    
    def register_model_group(self, body: dict):
        """Register model group"""
        return self.client.transport.perform_request(
            'POST',
            '/_plugins/_ml/model_groups/_register',
            body=body
        )
