"""
GB Guide — Health Check Router

Provides a lightweight endpoint for connectivity verification.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Returns service health status.

    Used by:
    - Docker health checks
    - Frontend connectivity probe
    - Load balancer readiness checks
    """
    return {"status": "ok"}
