"""
Ingestion service for bulk indexing data into OpenSearch
"""
import logging
import time
import json
from typing import Dict, List, Optional, Callable
from app.services.opensearch_service import OpenSearchService
from app.services.file_service import FileProcessingService
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for ingesting data into OpenSearch"""
    
    def __init__(
        self,
        os_service: OpenSearchService,
        file_service: FileProcessingService,
        embedding_service: EmbeddingService
    ):
        self.os_service = os_service
        self.file_service = file_service
        self.embedding_service = embedding_service
    
    def create_index_mapping(
        self,
        mappings: List[Dict],
        knn_columns: List[Dict]
    ) -> Dict:
        """
        Create OpenSearch index mapping
        
        Args:
            mappings: List of column mappings
            knn_columns: List of KNN column selections
            
        Returns:
            Index mapping dict
        """
        properties = {}
        
        # Create mapping for each column
        for mapping in mappings:
            column_name = mapping['column_name']
            os_type = mapping['opensearch_type']
            
            # Check if this column has KNN
            knn_info = next(
                (knn for knn in knn_columns if knn['column_name'] == column_name),
                None
            )
            
            if knn_info:
                # Add KNN vector field
                model_id = knn_info['model_id']
                dimension = self.embedding_service.get_model_dimension(model_id)
                
                properties[column_name] = {"type": os_type}
                properties[f"{column_name}_embedding"] = {
                    "type": "knn_vector",
                    "dimension": dimension,
                    "method": {
                        "name": "hnsw",
                        "engine": "lucene"
                    }
                }
            else:
                # Regular field
                if os_type == 'text':
                    # Add keyword sub-field for text fields
                    properties[column_name] = {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    }
                else:
                    properties[column_name] = {"type": os_type}
        
        return {
            "mappings": {
                "properties": properties
            },
            "settings": {
                "index": {
                    "knn": "true" if knn_columns else "false",
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                }
            }
        }
    
    def create_ingest_pipeline(
        self,
        pipeline_id: str,
        knn_columns: List[Dict]
    ) -> Optional[str]:
        """
        Create ingest pipeline for text embedding
        
        Args:
            pipeline_id: Pipeline identifier
            knn_columns: List of KNN column selections
            
        Returns:
            Pipeline ID if created, None otherwise
        """
        if not knn_columns:
            return None
        
        # Build field_map for text_embedding processor
        field_map = {}
        for knn_col in knn_columns:
            source_field = knn_col['column_name']
            target_field = f"{source_field}_embedding"
            field_map[source_field] = target_field
        
        # Use the first model_id (all KNN columns use same model)
        model_id = knn_columns[0]['model_id']
        
        pipeline_body = {
            "description": f"Text embedding pipeline for {pipeline_id}",
            "processors": [
                {
                    "text_embedding": {
                        "model_id": model_id,
                        "field_map": field_map
                    }
                }
            ]
        }
        
        self.os_service.create_ingest_pipeline(pipeline_id, pipeline_body)
        logger.info(f"Ingest pipeline created: {pipeline_id}")
        return pipeline_id
    
    def ingest_data(
        self,
        file_id: str,
        index_name: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Ingest data from file into OpenSearch
        
        Args:
            file_id: File identifier
            index_name: Target index name
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with ingestion results
        """
        start_time = time.time()
        
        try:
            # Get mappings and KNN selections
            mappings = self.file_service.get_mappings(file_id)
            knn_columns = self.file_service.get_knn_selections(file_id)
            
            logger.info(f"Retrieved {len(mappings) if mappings else 0} mappings for file {file_id}")
            logger.info(f"Retrieved {len(knn_columns) if knn_columns else 0} KNN columns for file {file_id}")
            if knn_columns:
                logger.info(f"KNN columns details: {knn_columns}")
            
            # If mappings not found, try to auto-generate from file data
            if not mappings:
                logger.warning(f"Mappings not found for file {file_id}, attempting to auto-generate")
                try:
                    # Load the dataframe to infer types
                    df = self.file_service.load_dataframe(file_id)
                    
                    # Generate mappings from dataframe columns
                    mappings = []
                    for col_name, dtype in df.dtypes.items():
                        os_type = self.file_service.pandas_dtype_to_opensearch(str(dtype))
                        mappings.append({
                            'column_name': col_name,
                            'opensearch_type': os_type,
                            'is_knn': False
                        })
                    
                    logger.info(f"Auto-generated {len(mappings)} mappings for file {file_id}")
                    
                    if not mappings:
                        raise ValueError("Unable to generate mappings from file data")
                except Exception as e:
                    logger.error(f"Failed to auto-generate mappings: {e}")
                    raise ValueError(f"Mappings not found and auto-generation failed: {str(e)}")
            
            if progress_callback:
                progress_callback({
                    "status": "processing",
                    "message": "Creating index mapping...",
                    "progress": 10
                })
            
            # Create index
            index_mapping = self.create_index_mapping(mappings, knn_columns)
            logger.info(f"Created index mapping with settings: {index_mapping.get('settings', {})}")
            
            if self.os_service.index_exists(index_name):
                logger.warning(f"Index {index_name} already exists, deleting...")
                self.os_service.delete_index(index_name)
            
            self.os_service.create_index(index_name, index_mapping)
            logger.info(f"Index created: {index_name}")
            
            if progress_callback:
                progress_callback({
                    "status": "processing",
                    "message": "Index created successfully",
                    "progress": 20
                })
            
            # Create ingest pipeline if KNN columns exist
            pipeline_id = None
            if knn_columns:
                pipeline_id = f"{index_name}_pipeline"
                logger.info(f"Creating ingest pipeline {pipeline_id} for {len(knn_columns)} KNN columns")
                self.create_ingest_pipeline(pipeline_id, knn_columns)
                logger.info(f"Pipeline {pipeline_id} created successfully")
                
                if progress_callback:
                    progress_callback({
                        "status": "processing",
                        "message": "Ingest pipeline created",
                        "progress": 30
                    })
            
            # Load DataFrame
            if progress_callback:
                progress_callback({
                    "status": "processing",
                    "message": "Loading data from file...",
                    "progress": 40
                })
            
            df = self.file_service.load_dataframe(file_id)
            total_docs = len(df)
            
            # Prepare bulk data
            if progress_callback:
                progress_callback({
                    "status": "processing",
                    "message": f"Preparing {total_docs} documents for ingestion...",
                    "progress": 50
                })
            
            # Convert DataFrame to bulk format
            bulk_body = []
            batch_size = 500
            
            for idx, row in df.iterrows():
                # Index action
                bulk_body.append({
                    "index": {
                        "_index": index_name,
                        "_id": str(idx)
                    }
                })
                
                # Document data (convert to dict and handle NaN)
                doc = row.to_dict()
                # Replace NaN with None
                doc = {k: (None if pd.isna(v) else v) for k, v in doc.items()}
                bulk_body.append(doc)
                
                # Bulk index in batches
                if len(bulk_body) >= batch_size * 2:  # *2 because each doc has 2 entries
                    logger.debug(f"Indexing batch with pipeline: {pipeline_id}")
                    self.os_service.bulk_index(
                        body=bulk_body,
                        index_name=index_name,
                        pipeline_id=pipeline_id
                    )
                    
                    progress_pct = 50 + int((idx / total_docs) * 40)
                    if progress_callback:
                        progress_callback({
                            "status": "processing",
                            "message": f"Indexed {idx + 1}/{total_docs} documents",
                            "progress": progress_pct
                        })
                    
                    bulk_body = []
            
            # Index remaining documents
            if bulk_body:
                logger.info(f"Indexing final batch of {len(bulk_body)//2} documents with pipeline: {pipeline_id}")
                self.os_service.bulk_index(
                    body=bulk_body,
                    index_name=index_name,
                    pipeline_id=pipeline_id
                )
            
            if progress_callback:
                progress_callback({
                    "status": "processing",
                    "message": "Refreshing index...",
                    "progress": 95
                })
            
            # Refresh index
            self.os_service.refresh_index(index_name)
            
            elapsed_time = time.time() - start_time
            
            result = {
                "success": True,
                "index_name": index_name,
                "documents_ingested": total_docs,
                "pipeline_id": pipeline_id,
                "elapsed_time": elapsed_time,
                "message": f"Successfully ingested {total_docs} documents"
            }
            
            if progress_callback:
                progress_callback({
                    "status": "completed",
                    "message": f"Ingestion completed! {total_docs} documents indexed",
                    "progress": 100,
                    "details": result
                })
            
            logger.info(f"Ingestion completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}", exc_info=True)
            
            if progress_callback:
                progress_callback({
                    "status": "failed",
                    "message": f"Ingestion failed: {str(e)}",
                    "progress": 0,
                    "details": {"error": str(e)}
                })
            
            raise


# Import pandas for NaN handling
import pandas as pd
