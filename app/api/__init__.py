"""API endpoints package.

This package contains all the API endpoint modules for the application.
"""

from fastapi import APIRouter
from app.schemas.build import BuildRequest, BuildResponse

# Create the endpoints router
router = APIRouter()

def register_routers():
    """Register all API routers to avoid circular imports."""
    from .endpoints import build as build_endpoints
    
    router.include_router(build_endpoints.router, prefix="/build", tags=["build"])
    
    # Add a top-level dispatcher endpoint required by the evaluator
    @router.post("/api-endpoint", response_model=BuildResponse, tags=["build"])
    async def api_endpoint_dispatch(payload: BuildRequest):
        if payload.round == 1:
            return await build_endpoints.build_app(payload)
        return await build_endpoints.update_app(payload)
    

# Register routers when this module is imported
register_routers()