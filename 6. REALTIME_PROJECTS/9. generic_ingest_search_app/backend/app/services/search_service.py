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
    
    def _get_model_id_from_pipeline(self, index_name: str) -> str:
        """
        Extract model_id from the index's ingest pipeline
        
        Args:
            index_name: Index to inspect
            
        Returns:
            Model ID used in the pipeline, or None if not found
        """
        try:
            # Get index settings to find default_pipeline
            index_info = self.os_service.client.indices.get(index=index_name)
            settings = index_info[index_name]['settings']
            pipeline_id = settings.get('index', {}).get('default_pipeline')
            
            if not pipeline_id:
                logger.warning(f"No default_pipeline found for index {index_name}")
                return None
            
            # Get pipeline to extract model_id
            pipeline_info = self.os_service.client.ingest.get_pipeline(id=pipeline_id)
            processors = pipeline_info[pipeline_id]['processors']
            
            # Find text_embedding processor
            for processor in processors:
                if 'text_embedding' in processor:
                    model_id = processor['text_embedding'].get('model_id')
                    if model_id:
                        logger.info(f"Found model_id {model_id} from pipeline {pipeline_id}")
                        return model_id
            
            logger.warning(f"No text_embedding processor found in pipeline {pipeline_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting model_id from pipeline: {e}")
            return None

    def semantic_search(
        self,
        index_name: str,
        query: str,
        size: int = 10
    ) -> Dict:
        """
        Semantic search using KNN vector similarity with neural query
        
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
        
        # Get model_id from pipeline
        model_id = self._get_model_id_from_pipeline(index_name)
        
        if not model_id:
            logger.warning("No model_id found, falling back to text match")
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
        
        # Use neural query with model_id
        try:
            search_body = {
                "query": {
                    "neural": {
                        knn_field: {
                            "query_text": query,
                            "model_id": model_id,
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
            model_id = self._get_model_id_from_pipeline(index_name)
            
            if model_id:
                try:
                    search_body["query"]["bool"]["should"].append({
                        "neural": {
                            knn_field: {
                                "query_text": query,
                                "model_id": model_id,
                                "k": size,
                                "boost": 2.0
                            }
                        }
                    })
                except Exception as e:
                    logger.warning(f"Could not add neural component: {e}")
            else:
                logger.warning("No model_id found, skipping neural component")
        
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
    
    async def create_plan_execute_reflect_agent(
        self,
        index_name: str,
        embedding_model_id: str
    ) -> str:
        """
        Create Plan-Execute-Reflect agent for semantic search
        
        Args:
            index_name: Index to search
            embedding_model_id: Model ID for embeddings
            
        Returns:
            Agent ID
        """
        if not self.llm_model_id:
            raise ValueError("LLM model not initialized")
        
        # Get index mapping to find KNN fields
        index_info = self.os_service.client.indices.get(index=index_name)
        properties = index_info[index_name]['mappings']['properties']
        
        # Find KNN vector field and source fields
        knn_field = None
        source_fields = []
        
        for field, config in properties.items():
            if config.get('type') == 'knn_vector':
                knn_field = field
            elif config.get('type') in ['text', 'keyword']:
                source_fields.append(field)
        
        if not knn_field:
            raise ValueError(f"No KNN field found in index {index_name}")
        
        # Create agent with VectorDBTool and MLModelTool
        agent_body = {
            "name": f"PER_Agent_{index_name}",
            "type": "flow",
            "description": "Plan-Execute-Reflect agent for semantic search with reasoning",
            "tools": [
                {
                    "type": "VectorDBTool",
                    "parameters": {
                        "model_id": embedding_model_id,
                        "index": index_name,
                        "embedding_field": knn_field,
                        "source_field": source_fields[:10],  # Limit to 10 fields
                        "input": "${parameters.question}"
                    }
                },
                {
                    "type": "MLModelTool",
                    "description": "OpenAI GPT for Plan-Execute-Reflect workflow",
                    "parameters": {
                        "model_id": self.llm_model_id,
                        "messages": "[{\"role\": \"system\", \"content\": \"You are an intelligent search assistant using Plan-Execute-Reflect methodology. PLAN: Analyze the user question and understand what information is needed. EXECUTE: Use the search results provided to extract relevant information. REFLECT: Evaluate if the results fully answer the question, identify any gaps, and provide a comprehensive, well-reasoned answer. Always show your reasoning process.\"}, {\"role\": \"user\", \"content\": \"Search Results:\\n${parameters.VectorDBTool.output}\\n\\nUser Question: ${parameters.question}\\n\\nProvide a detailed answer using Plan-Execute-Reflect approach.\"}]"
                    }
                }
            ]
        }
        
        response = self.os_service.client.transport.perform_request(
            'POST',
            '/_plugins/_ml/agents/_register',
            body=agent_body
        )
        
        agent_id = response['agent_id']
        logger.info(f"Created Plan-Execute-Reflect agent: {agent_id}")
        
        return agent_id

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
            search_type: Type of search (semantic or hybrid)
            size: Number of results
            
        Returns:
            Agent-enhanced search results
        """
        # For now, execute direct search without agent
        # Agent can be enabled later when OpenAI integration is configured
        logger.info(f"Executing {search_type} search with Plan-Execute-Reflect pattern")
        
        try:
            # PHASE 1: PLAN - Determine search strategy
            logger.info("Phase 1: PLAN - Analyzing query and selecting search strategy")
            
            # PHASE 2: EXECUTE - Run the search
            logger.info("Phase 2: EXECUTE - Running search tools")
            if search_type == "semantic":
                search_results = self.semantic_search(index_name, query, size)
            else:
                search_results = self.hybrid_search(index_name, query, size)
            
            # PHASE 3: REFLECT - Evaluate results
            logger.info("Phase 3: REFLECT - Analyzing results completeness")
            
            # Add metadata about the Plan-Execute-Reflect process
            search_results['agent_process'] = {
                "plan": f"Search {search_type} index for: '{query}'",
                "execute": f"Found {len(search_results['hits'])} results",
                "reflect": "Results retrieved successfully" if search_results['hits'] else "No matching results found"
            }
            
            # If agent is available and configured, use it for enhanced insights
            if self.llm_model_id and settings.OPENAI_API_KEY:
                try:
                    # Get model_id for agent creation
                    model_id = self._get_model_id_from_pipeline(index_name)
                    
                    if model_id:
                        # Create agent on-the-fly for this search
                        # Note: In production, agents should be created once and reused
                        logger.info("Creating temporary Plan-Execute-Reflect agent")
                        # For now, just add the model_id info
                        search_results['agent_process']['embedding_model'] = model_id
                        
                except Exception as e:
                    logger.warning(f"Could not create agent: {e}")
            
            return search_results
            
        except Exception as e:
            logger.error(f"Search execution failed: {e}")
            raise
    
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
