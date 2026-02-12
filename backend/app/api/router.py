"""
API Router - aggregates all API endpoints
"""

from fastapi import APIRouter

from app.api.endpoints import agents, profiles, projects, student, waitlist

api_router = APIRouter()

api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(student.router, prefix="/student", tags=["student"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(waitlist.router, prefix="/waitlist", tags=["waitlist"])
