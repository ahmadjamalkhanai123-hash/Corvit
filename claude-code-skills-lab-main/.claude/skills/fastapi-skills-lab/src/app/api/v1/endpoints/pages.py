"""
Pages Endpoints
===============

Public pages for the application: home, history, and about us.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/home")
def home():
    """
    Home page endpoint.

    Returns welcome message and navigation links.
    """
    return {
        "page": "home",
        "title": "Welcome to FastAPI Skills Lab",
        "message": "A comprehensive FastAPI learning project - from beginner to production-ready applications.",
        "features": [
            "Multi-layer Architecture",
            "JWT Authentication",
            "SQLAlchemy ORM",
            "MCP Server Integration",
            "Browser Automation"
        ],
        "navigation": {
            "history": "/api/v1/pages/history",
            "about": "/api/v1/pages/about-us",
            "docs": "/docs"
        }
    }


@router.get("/history")
def history():
    """
    History page endpoint.

    Returns the project history and milestones.
    """
    return {
        "page": "history",
        "title": "Project History",
        "description": "The evolution of FastAPI Skills Lab",
        "milestones": [
            {
                "version": "1.0.0",
                "date": "2024-01",
                "title": "Initial Release",
                "changes": [
                    "Basic FastAPI setup",
                    "Hello World endpoint",
                    "Path and query parameters"
                ]
            },
            {
                "version": "1.1.0",
                "date": "2024-02",
                "title": "Database Integration",
                "changes": [
                    "SQLAlchemy ORM integration",
                    "User and Item models",
                    "CRUD operations"
                ]
            },
            {
                "version": "1.2.0",
                "date": "2024-03",
                "title": "Authentication",
                "changes": [
                    "JWT token authentication",
                    "User registration and login",
                    "Protected routes"
                ]
            },
            {
                "version": "2.0.0",
                "date": "2024-04",
                "title": "MCP Integration",
                "changes": [
                    "MCP server implementation",
                    "Browser automation with Playwright",
                    "Web scraping tools"
                ]
            }
        ]
    }


@router.get("/about-us")
def about_us():
    """
    About Us page endpoint.

    Returns information about the project and team.
    """
    return {
        "page": "about-us",
        "title": "About Us",
        "project": {
            "name": "FastAPI Skills Lab",
            "description": "A comprehensive learning project designed to teach FastAPI development from basics to production-ready applications.",
            "purpose": "To provide hands-on learning experience with modern Python web development."
        },
        "technologies": [
            {"name": "FastAPI", "role": "Web Framework"},
            {"name": "SQLAlchemy", "role": "ORM"},
            {"name": "Pydantic", "role": "Data Validation"},
            {"name": "JWT", "role": "Authentication"},
            {"name": "MCP", "role": "AI Tool Integration"},
            {"name": "Playwright", "role": "Browser Automation"}
        ],
        "contact": {
            "github": "https://github.com/fastapi-skills-lab",
            "docs": "/docs"
        }
    }
