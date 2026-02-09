"""
API Router - aggregates all API endpoints
"""

from fastapi import APIRouter

from app.api.endpoints import agents, projects, student

api_router = APIRouter()

api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(student.router, prefix="/student", tags=["student"])
