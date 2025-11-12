"""
Pydantic models for API request/response schemas
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum


# ============================================================================
# AUTHENTICATION MODELS
# ============================================================================

class LoginRequest(BaseModel):
    """Login request schema"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str
    token_type: str = "bearer"
    username: str
    email: str


class UserInfo(BaseModel):
    """User information"""
    username: str
    email: str


# ============================================================================
# INGESTION MODELS
# ============================================================================

class FileFormat(str, Enum):
    """Supported file formats"""
    CSV = "csv"
    XLSX = "xlsx"
    JSONL = "jsonl"


class DataTypeEnum(str, Enum):
    """OpenSearch data types"""
    TEXT = "text"
    KEYWORD = "keyword"
    INTEGER = "integer"
    LONG = "long"
    FLOAT = "float"
    DOUBLE = "double"
    BOOLEAN = "boolean"
    DATE = "date"
    OBJECT = "object"
    NESTED = "nested"
    GEO_POINT = "geo_point"


class FileUploadResponse(BaseModel):
    """Response after file upload"""
    file_id: str = Field(..., description="Unique file identifier")
    filename: str
    format: FileFormat
    sheets: Optional[List[str]] = Field(None, description="Sheet names for XLSX files")
    columns: Optional[List[str]] = Field(None, description="Column names (first row for XLSX/CSV)")
    column_types: Optional[Dict[str, str]] = Field(None, description="Inferred column types")
    message: str


class DataPreviewRequest(BaseModel):
    """Request for data preview"""
    file_id: str
    sheet_name: Optional[str] = None


class DataPreviewResponse(BaseModel):
    """Data preview response"""
    columns: List[str]
    data: List[Dict[str, Any]]
    total_rows: int
    preview_rows: int
    dtypes: Dict[str, str] = Field(..., description="Pandas data types")


class ColumnMapping(BaseModel):
    """Column to OpenSearch type mapping"""
    column_name: str
    opensearch_type: DataTypeEnum
    is_knn: bool = False


class DataTypeMappingRequest(BaseModel):
    """Request for data type mapping confirmation"""
    file_id: str
    mappings: List[ColumnMapping]


class DataTypeMappingResponse(BaseModel):
    """Response with suggested mappings"""
    mappings: List[ColumnMapping]
    message: str


class EmbeddingModelInfo(BaseModel):
    """Embedding model information"""
    model_id: str
    name: str
    dimension: int
    description: str
    status: str


class AvailableModelsResponse(BaseModel):
    """Response with available embedding models"""
    models: List[EmbeddingModelInfo]


class KNNColumnSelection(BaseModel):
    """KNN column selection"""
    column_name: str
    model_id: str
    model_name: str


class KNNSelectionRequest(BaseModel):
    """Request for KNN column selection"""
    file_id: str
    knn_columns: List[KNNColumnSelection]


class KNNSelectionResponse(BaseModel):
    """Response after KNN selection"""
    message: str
    selected_columns: List[str]


class IngestionSummary(BaseModel):
    """Ingestion summary for review"""
    file_id: str
    filename: str
    total_rows: int
    columns: List[str]
    mappings: List[ColumnMapping]
    knn_columns: List[KNNColumnSelection]
    estimated_size: str


class IngestionRequest(BaseModel):
    """Final ingestion request"""
    file_id: str
    index_name: str = Field(..., description="OpenSearch index name", min_length=1)
    
    @validator('index_name')
    def validate_index_name(cls, v):
        """Validate index name format"""
        if not v.islower():
            raise ValueError("Index name must be lowercase")
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Index name can only contain lowercase letters, numbers, hyphens, and underscores")
        return v


class IngestionProgress(BaseModel):
    """Ingestion progress update"""
    status: str  # "processing", "completed", "failed"
    message: str
    progress: int = Field(..., ge=0, le=100)
    details: Optional[Dict[str, Any]] = None


class IngestionResponse(BaseModel):
    """Response after ingestion completion"""
    success: bool
    index_name: str
    documents_ingested: int
    pipeline_id: Optional[str] = None
    elapsed_time: float
    errors: Optional[List[str]] = None
    message: str


# ============================================================================
# SEARCH MODELS
# ============================================================================

class SearchType(str, Enum):
    """Search types"""
    SEARCH_AS_YOU_TYPE = "search_as_you_type"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class SearchRequest(BaseModel):
    """Search request"""
    index_name: str
    query: str = Field(..., min_length=1)
    search_type: SearchType
    size: int = Field(10, ge=1, le=100)


class SearchHit(BaseModel):
    """Single search result"""
    id: str
    score: float
    source: Dict[str, Any]


class SearchResponse(BaseModel):
    """Search response"""
    hits: List[SearchHit]
    total: int
    took: int  # milliseconds
    search_type: SearchType


class AvailableIndicesResponse(BaseModel):
    """Response with available indices"""
    indices: List[str]


# ============================================================================
# ERROR MODELS
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    trace: Optional[List[str]] = None
