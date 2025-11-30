"""
Search routes for executing searches
"""
import logging
from fastapi import APIRouter, HTTPException, Request, Depends

from app.models.schemas import (
    SearchRequest,
    SearchResponse,
    AvailableIndicesResponse,
    SearchHit
)
from app.services.search_service import SearchService
from app.routes.auth import verify_token

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/indices", response_model=AvailableIndicesResponse)
async def get_available_indices(
    request: Request,
    token: dict = Depends(verify_token)
):
    """Get list of available indices for search"""
    try:
        os_service = request.app.state.os_service
        indices = os_service.get_all_indices()
        
        return AvailableIndicesResponse(indices=indices)
        
    except Exception as e:
        logger.error(f"Get indices failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=SearchResponse)
async def execute_search(
    search_request: SearchRequest,
    request: Request,
    token: dict = Depends(verify_token)
):
    """
    Execute search based on search type
    
    Search types:
    - search_as_you_type: Real-time prefix matching
    - semantic: Vector similarity search
    - hybrid: Combined keyword + semantic search
    """
    try:
        logger.info(f"Search request: index={search_request.index_name}, query={search_request.query}, type={search_request.search_type}, size={search_request.size}")
        
        os_service = request.app.state.os_service
        search_service = SearchService(os_service)
        
        # Check if index exists
        if not os_service.index_exists(search_request.index_name):
            raise HTTPException(
                status_code=404,
                detail=f"Index '{search_request.index_name}' not found"
            )
        
        # Execute search based on type
        if search_request.search_type.value == "search_as_you_type":
            result = search_service.search_as_you_type(
                search_request.index_name,
                search_request.query,
                search_request.size
            )
        elif search_request.search_type.value == "semantic":
            result = search_service.semantic_search(
                search_request.index_name,
                search_request.query,
                search_request.size
            )
        elif search_request.search_type.value == "hybrid":
            result = search_service.hybrid_search(
                search_request.index_name,
                search_request.query,
                search_request.size
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid search type: {search_request.search_type}"
            )
        
        return SearchResponse(
            hits=[SearchHit(**hit) for hit in result['hits']],
            total=result['total'],
            took=result['took'],
            search_type=result['search_type']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-with-agent", response_model=SearchResponse)
async def execute_search_with_agent(
    search_request: SearchRequest,
    request: Request,
    token: dict = Depends(verify_token)
):
    """
    Execute search with Plan-Execute-Reflect agent
    (Only for semantic and hybrid searches)
    """
    try:
        if search_request.search_type.value == "search_as_you_type":
            raise HTTPException(
                status_code=400,
                detail="Agent not supported for search-as-you-type"
            )
        
        os_service = request.app.state.os_service
        search_service = SearchService(os_service)
        
        # Initialize agent if needed
        if not search_service.llm_model_id:
            await search_service.initialize_agent()
        
        # Execute with agent
        result = search_service.execute_with_agent(
            search_request.index_name,
            search_request.query,
            search_request.search_type.value,
            search_request.size
        )
        
        response = SearchResponse(
            hits=[SearchHit(**hit) for hit in result['hits']],
            total=result['total'],
            took=result['took'],
            search_type=result['search_type']
        )
        
        # Add agent insights if available
        if 'agent_insights' in result:
            response.agent_insights = result['agent_insights']
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
