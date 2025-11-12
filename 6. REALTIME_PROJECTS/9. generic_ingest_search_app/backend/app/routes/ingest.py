"""
Ingestion routes for file upload and data ingestion
"""
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import List

from app.models.schemas import (
    FileUploadResponse,
    DataPreviewRequest,
    DataPreviewResponse,
    DataTypeMappingRequest,
    DataTypeMappingResponse,
    AvailableModelsResponse,
    KNNSelectionRequest,
    KNNSelectionResponse,
    IngestionRequest,
    IngestionResponse,
    ColumnMapping,
    EmbeddingModelInfo
)
from app.services.file_service import FileProcessingService
from app.services.ingest_service import IngestionService
from app.routes.auth import verify_token

logger = logging.getLogger(__name__)
router = APIRouter()


def get_services(request: Request):
    """Get services from app state"""
    return {
        "os_service": request.app.state.os_service,
        "embedding_service": request.app.state.embedding_service,
        "file_service": FileProcessingService(),
        "ingest_service": IngestionService(
            request.app.state.os_service,
            FileProcessingService(),
            request.app.state.embedding_service
        )
    }


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    request: Request = None,
    token: dict = Depends(verify_token)
):
    """
    Upload file (CSV, XLSX, or JSONL)
    
    Returns file_id and sheet names (for XLSX)
    """
    try:
        # Validate file extension
        filename = file.filename
        extension = filename.split('.')[-1].lower()
        
        if f".{extension}" not in ['.csv', '.xlsx', '.jsonl']:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {extension}. Supported: CSV, XLSX, JSONL"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        if len(content) > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 50MB limit"
            )
        
        # Save file
        file_service = FileProcessingService()
        file_id, file_path = file_service.save_uploaded_file(filename, content)
        
        # Get sheets for XLSX
        sheets = None
        columns = None
        column_types = None
        
        if extension == 'xlsx':
            sheets = file_service.get_excel_sheets(file_path)
            # Read first sheet to get columns
            try:
                df = file_service.load_dataframe(file_id, sheets[0] if sheets else None)
                columns = list(df.columns)
                column_types = {
                    col: file_service.pandas_dtype_to_opensearch(str(dtype))
                    for col, dtype in df.dtypes.items()
                }
            except Exception as e:
                logger.warning(f"Could not extract columns: {e}")
        elif extension == 'csv':
            # Read CSV to get columns
            try:
                df = file_service.load_dataframe(file_id)
                columns = list(df.columns)
                column_types = {
                    col: file_service.pandas_dtype_to_opensearch(str(dtype))
                    for col, dtype in df.dtypes.items()
                }
            except Exception as e:
                logger.warning(f"Could not extract columns: {e}")
        
        logger.info(f"File uploaded: {filename} -> {file_id}")
        
        return FileUploadResponse(
            file_id=file_id,
            filename=filename,
            format=extension,
            sheets=sheets,
            columns=columns,
            column_types=column_types,
            message="File uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview", response_model=DataPreviewResponse)
async def preview_data(
    request_data: DataPreviewRequest,
    request: Request = None,
    token: dict = Depends(verify_token)
):
    """
    Preview data from uploaded file
    
    Returns first 10 rows and column information
    """
    try:
        file_service = FileProcessingService()
        preview = file_service.get_data_preview(
            request_data.file_id,
            request_data.sheet_name,
            num_rows=10
        )
        
        return DataPreviewResponse(**preview)
    except Exception as e:
        logger.error(f"Data preview failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get-columns")
async def get_columns(
    request_data: DataPreviewRequest,
    request: Request = None,
    token: dict = Depends(verify_token)
):
    """
    Get columns and types for a specific sheet
    
    Returns column names and inferred types
    """
    try:
        file_service = FileProcessingService()
        df = file_service.load_dataframe(
            request_data.file_id,
            request_data.sheet_name
        )
        
        columns = list(df.columns)
        column_types = {
            col: file_service.pandas_dtype_to_opensearch(str(dtype))
            for col, dtype in df.dtypes.items()
        }
        
        return {
            "columns": columns,
            "column_types": column_types
        }
    except Exception as e:
        logger.error(f"Get columns failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        logger.error(f"Preview failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest-mappings", response_model=DataTypeMappingResponse)
async def suggest_mappings(
    request_data: DataPreviewRequest,
    request: Request = None,
    token: dict = Depends(verify_token)
):
    """
    Suggest OpenSearch field mappings based on pandas dtypes
    """
    try:
        file_service = FileProcessingService()
        
        # Load data first to get dtypes
        file_service.load_dataframe(request_data.file_id, request_data.sheet_name)
        
        # Get suggested mappings
        mappings = file_service.suggest_mappings(request_data.file_id)
        
        return DataTypeMappingResponse(
            mappings=[ColumnMapping(**m) for m in mappings],
            message="Mappings suggested based on data types"
        )
        
    except Exception as e:
        logger.error(f"Suggest mappings failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm-mappings")
async def confirm_mappings(
    request_data: DataTypeMappingRequest,
    request: Request = None,
    token: dict = Depends(verify_token)
):
    """
    Confirm and store user-selected data type mappings
    """
    try:
        file_service = FileProcessingService()
        
        # Convert Pydantic models to dicts
        mappings_dict = [m.dict() for m in request_data.mappings]
        
        # Store mappings
        file_service.store_mappings(request_data.file_id, mappings_dict)
        
        return {
            "message": "Mappings confirmed and stored",
            "file_id": request_data.file_id
        }
        
    except Exception as e:
        logger.error(f"Confirm mappings failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-models", response_model=AvailableModelsResponse)
async def get_available_models(
    request: Request,
    token: dict = Depends(verify_token)
):
    """
    Get list of available embedding models
    """
    try:
        embedding_service = request.app.state.embedding_service
        models = embedding_service.get_available_models()
        
        return AvailableModelsResponse(
            models=[EmbeddingModelInfo(**m) for m in models]
        )
        
    except Exception as e:
        logger.error(f"Get models failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm-knn", response_model=KNNSelectionResponse)
async def confirm_knn_selection(
    request_data: KNNSelectionRequest,
    request: Request = None,
    token: dict = Depends(verify_token)
):
    """
    Confirm KNN column selections
    """
    try:
        file_service = FileProcessingService()
        
        # Convert to dict
        knn_columns = [col.dict() for col in request_data.knn_columns]
        
        # Store selections
        file_service.store_knn_selections(request_data.file_id, knn_columns)
        
        selected = [col['column_name'] for col in knn_columns]
        
        return KNNSelectionResponse(
            message=f"KNN configuration stored for {len(selected)} columns",
            selected_columns=selected
        )
        
    except Exception as e:
        logger.error(f"Confirm KNN failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest-summary")
async def get_ingestion_summary(
    request_data: DataPreviewRequest,
    request: Request = None,
    token: dict = Depends(verify_token)
):
    """
    Get summary of all selections for review before ingestion
    """
    try:
        file_service = FileProcessingService()
        
        # Get metadata
        metadata = file_service.get_file_metadata(request_data.file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get DataFrame info
        df_info_str = file_service.redis_client.get(f"df_info:{request_data.file_id}")
        if not df_info_str:
            raise HTTPException(status_code=404, detail="Data not loaded")
        
        df_info = json.loads(df_info_str)
        
        # Get mappings
        mappings = file_service.get_mappings(request_data.file_id)
        if not mappings:
            raise HTTPException(status_code=404, detail="Mappings not configured")
        
        # Get KNN selections
        knn_columns = file_service.get_knn_selections(request_data.file_id)
        
        summary = {
            "file_id": request_data.file_id,
            "filename": metadata['filename'],
            "total_rows": df_info['shape'][0],
            "columns": df_info['columns'],
            "mappings": mappings,
            "knn_columns": knn_columns,
            "estimated_size": f"{df_info['shape'][0]} documents"
        }
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get summary failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest-stream")
async def ingest_data_stream(
    request_data: IngestionRequest,
    request: Request,
    token: dict = Depends(verify_token)
):
    """
    Start data ingestion with streaming progress updates
    
    Returns SSE (Server-Sent Events) stream
    """
    async def progress_generator():
        """Generator for streaming progress updates"""
        try:
            progress_queue = asyncio.Queue()
            
            def progress_callback(update: dict):
                """Callback to send progress updates"""
                asyncio.create_task(progress_queue.put(update))
            
            # Get services
            services = get_services(request)
            ingest_service = services['ingest_service']
            
            # Start ingestion in background
            async def run_ingestion():
                try:
                    result = ingest_service.ingest_data(
                        request_data.file_id,
                        request_data.index_name,
                        progress_callback
                    )
                    await progress_queue.put({
                        "status": "completed",
                        "message": "Ingestion completed successfully",
                        "progress": 100,
                        "details": result
                    })
                except Exception as e:
                    logger.error(f"Ingestion error: {e}", exc_info=True)
                    await progress_queue.put({
                        "status": "failed",
                        "message": str(e),
                        "progress": 0
                    })
                finally:
                    await progress_queue.put(None)  # Signal completion
            
            # Start ingestion task
            asyncio.create_task(run_ingestion())
            
            # Stream progress updates
            while True:
                update = await progress_queue.get()
                if update is None:
                    break
                
                # Format as SSE
                yield f"data: {json.dumps(update)}\n\n"
                
                if update['status'] in ['completed', 'failed']:
                    break
            
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            error_update = {
                "status": "failed",
                "message": str(e),
                "progress": 0
            }
            yield f"data: {json.dumps(error_update)}\n\n"
    
    return StreamingResponse(
        progress_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/ingest", response_model=IngestionResponse)
async def ingest_data(
    request_data: IngestionRequest,
    request: Request,
    token: dict = Depends(verify_token)
):
    """
    Ingest data into OpenSearch (non-streaming version)
    """
    try:
        services = get_services(request)
        ingest_service = services['ingest_service']
        
        result = ingest_service.ingest_data(
            request_data.file_id,
            request_data.index_name
        )
        
        return IngestionResponse(**result)
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
