"""
File processing service for handling CSV, XLSX, and JSONL files
"""
import logging
import pandas as pd
import json
import os
import uuid
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class FileProcessingService:
    """Service for processing uploaded files"""
    
    def __init__(self):
        """Initialize file processing service"""
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Redis for storing file metadata and temporary data
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True
        )
        logger.info("File processing service initialized")
    
    def save_uploaded_file(self, filename: str, content: bytes) -> Tuple[str, str]:
        """
        Save uploaded file and return file_id and path
        
        Args:
            filename: Original filename
            content: File content as bytes
            
        Returns:
            Tuple of (file_id, file_path)
        """
        file_id = str(uuid.uuid4())
        file_extension = Path(filename).suffix
        file_path = self.upload_dir / f"{file_id}{file_extension}"
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Store metadata in Redis
        metadata = {
            "file_id": file_id,
            "filename": filename,
            "file_path": str(file_path),
            "extension": file_extension
        }
        self.redis_client.setex(
            f"file_metadata:{file_id}",
            3600 * 24,  # 24 hours expiry
            json.dumps(metadata)
        )
        
        logger.info(f"File saved: {filename} -> {file_id}")
        return file_id, str(file_path)
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict]:
        """Get file metadata from Redis"""
        data = self.redis_client.get(f"file_metadata:{file_id}")
        if data:
            return json.loads(data)
        return None
    
    def get_excel_sheets(self, file_path: str) -> List[str]:
        """Get list of sheet names from Excel file"""
        try:
            excel_file = pd.ExcelFile(file_path)
            return excel_file.sheet_names
        except Exception as e:
            logger.error(f"Failed to read Excel sheets: {e}")
            raise ValueError(f"Failed to read Excel file: {str(e)}")
    
    def load_dataframe(
        self,
        file_id: str,
        sheet_name: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load file into pandas DataFrame
        
        Args:
            file_id: File identifier
            sheet_name: Sheet name for Excel files
            
        Returns:
            pandas DataFrame
        """
        metadata = self.get_file_metadata(file_id)
        if not metadata:
            raise ValueError(f"File {file_id} not found")
        
        file_path = metadata['file_path']
        extension = metadata['extension'].lower()
        
        try:
            if extension == '.csv':
                df = pd.read_csv(file_path)
            elif extension == '.xlsx':
                if sheet_name:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                else:
                    # Read first sheet by default
                    df = pd.read_excel(file_path)
            elif extension == '.jsonl':
                df = pd.read_json(file_path, lines=True)
            else:
                raise ValueError(f"Unsupported file format: {extension}")
            
            # Store DataFrame info in Redis
            df_info = {
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "shape": df.shape,
                "sheet_name": sheet_name
            }
            self.redis_client.setex(
                f"df_info:{file_id}",
                3600 * 24,
                json.dumps(df_info)
            )
            
            logger.info(f"DataFrame loaded: {df.shape[0]} rows, {df.shape[1]} columns")
            return df
            
        except Exception as e:
            logger.error(f"Failed to load DataFrame: {e}")
            raise ValueError(f"Failed to load file: {str(e)}")
    
    def get_data_preview(
        self,
        file_id: str,
        sheet_name: Optional[str] = None,
        num_rows: int = 10
    ) -> Dict:
        """
        Get preview of data
        
        Args:
            file_id: File identifier
            sheet_name: Sheet name for Excel files
            num_rows: Number of rows to preview
            
        Returns:
            Dictionary with preview data
        """
        df = self.load_dataframe(file_id, sheet_name)
        
        preview_df = df.head(num_rows)
        
        # Convert to JSON-serializable format
        preview_data = preview_df.to_dict(orient='records')
        
        return {
            "columns": list(df.columns),
            "data": preview_data,
            "total_rows": len(df),
            "preview_rows": len(preview_df),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
    
    def pandas_dtype_to_opensearch(self, pandas_dtype: str) -> str:
        """
        Convert pandas dtype to OpenSearch field type
        
        Args:
            pandas_dtype: Pandas data type string
            
        Returns:
            OpenSearch field type
        """
        dtype_mapping = {
            'int64': 'long',
            'int32': 'integer',
            'float64': 'double',
            'float32': 'float',
            'bool': 'boolean',
            'object': 'text',
            'datetime64': 'date',
            'datetime64[ns]': 'date',
            'timedelta64': 'long',
            'category': 'keyword'
        }
        
        # Handle pandas dtypes
        dtype_str = str(pandas_dtype).lower()
        
        # Check for exact matches
        if dtype_str in dtype_mapping:
            return dtype_mapping[dtype_str]
        
        # Check for partial matches
        if 'int' in dtype_str:
            return 'long'
        elif 'float' in dtype_str:
            return 'double'
        elif 'bool' in dtype_str:
            return 'boolean'
        elif 'datetime' in dtype_str:
            return 'date'
        else:
            return 'text'
    
    def suggest_mappings(self, file_id: str) -> List[Dict]:
        """
        Suggest OpenSearch mappings based on pandas dtypes
        
        Args:
            file_id: File identifier
            
        Returns:
            List of column mappings
        """
        df_info_str = self.redis_client.get(f"df_info:{file_id}")
        if not df_info_str:
            raise ValueError(f"DataFrame info not found for {file_id}")
        
        df_info = json.loads(df_info_str)
        dtypes = df_info['dtypes']
        
        mappings = []
        for column, pandas_dtype in dtypes.items():
            opensearch_type = self.pandas_dtype_to_opensearch(pandas_dtype)
            mappings.append({
                "column_name": column,
                "opensearch_type": opensearch_type,
                "is_knn": False
            })
        
        return mappings
    
    def store_mappings(self, file_id: str, mappings: List[Dict]):
        """Store user-confirmed mappings in Redis"""
        self.redis_client.setex(
            f"mappings:{file_id}",
            3600 * 24,
            json.dumps(mappings)
        )
    
    def get_mappings(self, file_id: str) -> Optional[List[Dict]]:
        """Get stored mappings"""
        data = self.redis_client.get(f"mappings:{file_id}")
        if data:
            return json.loads(data)
        return None
    
    def store_knn_selections(self, file_id: str, knn_columns: List[Dict]):
        """Store KNN column selections"""
        self.redis_client.setex(
            f"knn_columns:{file_id}",
            3600 * 24,
            json.dumps(knn_columns)
        )
    
    def get_knn_selections(self, file_id: str) -> Optional[List[Dict]]:
        """Get KNN column selections"""
        data = self.redis_client.get(f"knn_columns:{file_id}")
        if data:
            return json.loads(data)
        return []
    
    def cleanup_file(self, file_id: str):
        """Clean up file and associated data"""
        metadata = self.get_file_metadata(file_id)
        if metadata:
            # Delete file
            file_path = Path(metadata['file_path'])
            if file_path.exists():
                file_path.unlink()
            
            # Delete Redis keys
            self.redis_client.delete(f"file_metadata:{file_id}")
            self.redis_client.delete(f"df_info:{file_id}")
            self.redis_client.delete(f"mappings:{file_id}")
            self.redis_client.delete(f"knn_columns:{file_id}")
            
            logger.info(f"Cleaned up file: {file_id}")
