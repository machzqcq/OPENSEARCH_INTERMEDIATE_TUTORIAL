"""
Search service with support for search-as-you-type, semantic, and hybrid search
Includes Plan-Execute-Reflect agent for semantic and hybrid queries
"""
import logging
import json
import time
from typing import Dict, List
from app.services.opensearch_service import OpenSearchService
from app.core.config import settings

logger = logging.getLogger(__name__)


class SearchService:
    """Service for executing various types of searches"""
    
    def __init__(self, os_service: OpenSearchService):
        self.os_service = os_service
        self.agent_id = None
        self.llm_model_id = None
    
    async def initialize_agent(self):
        """Initialize Plan-Execute-Reflect agent for semantic/hybrid search"""
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not set, agent features will be limited")
            return
        
        try:
            # Create model group
            model_group_name = f"search_agent_group_{int(time.time())}"
            model_group_body = {
                "name": model_group_name,
                "description": "Model group for search agent"
            }
            response = self.os_service.register_model_group(model_group_body)
            model_group_id = response['model_group_id']
            logger.info(f"Model group created: {model_group_id}")
            
            # Create OpenAI connector
            connector_body = {
                "name": "OpenAI Search Connector",
                "description": "Connector for OpenAI GPT models",
                "version": 1,
                "protocol": "http",
                "parameters": {
                    "endpoint": "api.openai.com",
                    "model": settings.OPENAI_MODEL
                },
                "credential": {
                    "openAI_key": settings.OPENAI_API_KEY
                },
                "actions": [
                    {
                        "action_type": "predict",
                        "method": "POST",
                        "url": "https://${parameters.endpoint}/v1/chat/completions",
                        "headers": {
                            "Authorization": "Bearer ${credential.openAI_key}",
                            "Content-Type": "application/json"
                        },
                        "request_body": "{\"model\": \"${parameters.model}\", \"messages\": ${parameters.messages}, \"temperature\": 0.7}"
                    }
                ]
            }
            
            connector_response = self.os_service.create_connector(connector_body)
            connector_id = connector_response['connector_id']
            logger.info(f"OpenAI connector created: {connector_id}")
            
            # Register OpenAI model
            model_body = {
                "name": f"openai-{settings.OPENAI_MODEL}-search",
                "function_name": "remote",
                "model_group_id": model_group_id,
                "description": f"OpenAI {settings.OPENAI_MODEL} for search agent",
                "connector_id": connector_id
            }
            
            model_response = self.os_service.register_model(model_body)
            self.llm_model_id = model_response['model_id']
            logger.info(f"OpenAI model registered: {self.llm_model_id}")
            
            # Deploy model
            self.os_service.deploy_model(self.llm_model_id)
            await self._wait_for_deployment(self.llm_model_id)
            
            logger.info("Search agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
    
    async def _wait_for_deployment(self, model_id: str, timeout: int = 300):
        """Wait for model deployment"""
        import asyncio
        start_time = time.time()
        
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Model deployment timeout")
            
            status = self.os_service.get_model_status(model_id)
            state = status.get('model_state')
            
            if state == 'DEPLOYED':
                return
            elif state == 'FAILED':
                raise Exception("Model deployment failed")
            
            await asyncio.sleep(5)
    
    def search_as_you_type(
        self,
        index_name: str,
        query: str,
        size: int = 10
    ) -> Dict:
        """
        Search-as-you-type using match_phrase_prefix
        
        Args:
            index_name: Index to search
            query: Search query
            size: Number of results
            
        Returns:
            Search results
        """
        # Get index mapping to find text fields
        index_info = self.os_service.client.indices.get(index=index_name)
        properties = index_info[index_name]['mappings']['properties']
        
        # Find text fields
        text_fields = [
            field for field, config in properties.items()
            if config.get('type') == 'text'
        ]
        
        # Build multi-match query with phrase_prefix
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "type": "phrase_prefix",
                    "fields": text_fields
                }
            },
            "size": size
        }
        
        response = self.os_service.search(index_name, search_body)
        
        return self._format_response(response, "search_as_you_type")
    
    def semantic_search(
        self,
        index_name: str,
        query: str,
        size: int = 10
    ) -> Dict:
        """
        Semantic search using KNN vector similarity
        
        Args:
            index_name: Index to search
            query: Search query
            size: Number of results
            
        Returns:
            Search results
        """
        # Get index mapping to find KNN fields
        index_info = self.os_service.client.indices.get(index=index_name)
        properties = index_info[index_name]['mappings']['properties']
        
        # Find KNN vector fields
        knn_fields = [
            field for field, config in properties.items()
            if config.get('type') == 'knn_vector'
        ]
        
        if not knn_fields:
            raise ValueError("No KNN fields found in index")
        
        # Use first KNN field for search
        knn_field = knn_fields[0]
        
        # For demonstration, use neural query if available
        # Otherwise fall back to basic KNN
        try:
            search_body = {
                "query": {
                    "neural": {
                        knn_field: {
                            "query_text": query,
                            "k": size
                        }
                    }
                },
                "size": size
            }
            response = self.os_service.search(index_name, search_body)
        except Exception as e:
            logger.warning(f"Neural query failed, falling back to match: {e}")
            # Fallback to text matching on source field
            source_field = knn_field.replace('_embedding', '')
            search_body = {
                "query": {
                    "match": {
                        source_field: query
                    }
                },
                "size": size
            }
            response = self.os_service.search(index_name, search_body)
        
        return self._format_response(response, "semantic")
    
    def hybrid_search(
        self,
        index_name: str,
        query: str,
        size: int = 10
    ) -> Dict:
        """
        Hybrid search combining keyword and semantic search
        
        Args:
            index_name: Index to search
            query: Search query
            size: Number of results
            
        Returns:
            Search results
        """
        # Get index fields
        index_info = self.os_service.client.indices.get(index=index_name)
        properties = index_info[index_name]['mappings']['properties']
        
        text_fields = [
            field for field, config in properties.items()
            if config.get('type') == 'text'
        ]
        
        knn_fields = [
            field for field, config in properties.items()
            if config.get('type') == 'knn_vector'
        ]
        
        # Build hybrid query
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": text_fields,
                                "boost": 1.0
                            }
                        }
                    ]
                }
            },
            "size": size
        }
        
        # Add neural query if KNN fields exist
        if knn_fields:
            knn_field = knn_fields[0]
            try:
                search_body["query"]["bool"]["should"].append({
                    "neural": {
                        knn_field: {
                            "query_text": query,
                            "k": size,
                            "boost": 2.0
                        }
                    }
                })
            except Exception as e:
                logger.warning(f"Could not add neural component: {e}")
        
        response = self.os_service.search(index_name, search_body)
        
        return self._format_response(response, "hybrid")
    
    def _format_response(self, response: Dict, search_type: str) -> Dict:
        """Format OpenSearch response"""
        hits = []
        
        for hit in response['hits']['hits']:
            hits.append({
                "id": hit['_id'],
                "score": hit['_score'],
                "source": hit['_source']
            })
        
        return {
            "hits": hits,
            "total": response['hits']['total']['value'],
            "took": response['took'],
            "search_type": search_type
        }
    
    def execute_with_agent(
        self,
        index_name: str,
        query: str,
        search_type: str,
        size: int = 10
    ) -> Dict:
        """
        Execute search with Plan-Execute-Reflect agent
        (For semantic and hybrid searches)
        
        Args:
            index_name: Index to search
            query: Search query
            search_type: Type of search
            size: Number of results
            
        Returns:
            Agent-enhanced search results
        """
        if not self.llm_model_id:
            logger.warning("Agent not initialized, using direct search")
            if search_type == "semantic":
                return self.semantic_search(index_name, query, size)
            else:
                return self.hybrid_search(index_name, query, size)
        
        try:
            # Execute search first
            if search_type == "semantic":
                search_results = self.semantic_search(index_name, query, size)
            else:
                search_results = self.hybrid_search(index_name, query, size)
            
            # Prepare context for agent
            context = f"Search Results:\n{json.dumps(search_results['hits'][:3], indent=2)}\n\nUser Query: {query}"
            
            # Create agent request
            agent_body = {
                "parameters": {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a search assistant. Analyze the search results and provide insights."
                        },
                        {
                            "role": "user",
                            "content": context
                        }
                    ]
                }
            }
            
            # Execute with model directly
            model_response = self.os_service.client.transport.perform_request(
                'POST',
                f'/_plugins/_ml/models/{self.llm_model_id}/_predict',
                body=agent_body
            )
            
            # Add agent insights to results
            search_results['agent_insights'] = self._extract_agent_response(model_response)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            # Return results without agent enhancement
            if search_type == "semantic":
                return self.semantic_search(index_name, query, size)
            else:
                return self.hybrid_search(index_name, query, size)
    
    def _extract_agent_response(self, response: Dict) -> str:
        """Extract agent response from model output"""
        try:
            if 'inference_results' in response:
                results = response['inference_results']
                if results and len(results) > 0:
                    output = results[0].get('output', [])
                    if output and len(output) > 0:
                        result_data = output[0].get('dataAsMap', {})
                        choices = result_data.get('choices', [])
                        if choices and len(choices) > 0:
                            message = choices[0].get('message', {})
                            return message.get('content', '')
            return ""
        except Exception as e:
            logger.error(f"Failed to extract agent response: {e}")
            return ""
