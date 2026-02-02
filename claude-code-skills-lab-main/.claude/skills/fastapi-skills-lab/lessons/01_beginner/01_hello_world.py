"""
LESSON 1: Hello World - Your First FastAPI App
================================================

FastAPI is a modern Python web framework. Let's start with the basics!

Key Concepts:
- FastAPI instance
- Route decorators (@app.get, @app.post, etc.)
- Path operations
- Running with uvicorn

To run this lesson:
    cd fastapi-skills-lab
    uv run uvicorn lessons.01_beginner.01_hello_world:app --reload

Then open: http://127.0.0.1:8000
API Docs: http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI

# Create FastAPI instance - this is your application
app = FastAPI(
    title="My First FastAPI App",
    description="Learning FastAPI from scratch",
    version="1.0.0"
)


# Root endpoint - responds to GET requests at "/"
@app.get("/")
def read_root():
    """
    This is the root endpoint.
    The docstring becomes the description in the auto-generated docs!
    """
    return {"message": "Hello, World!", "status": "success"}


# Another endpoint with a different path
@app.get("/about")
def about():
    """Returns information about this API."""
    return {
        "name": "FastAPI Learning Lab",
        "author": "You!",
        "description": "A project to learn FastAPI from beginner to advanced"
    }


# Health check endpoint - common in production APIs
@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


"""
EXERCISE 1:
-----------
Add a new endpoint `/greet` that returns a greeting message.

EXERCISE 2:
-----------
Add an endpoint `/info` that returns your name and favorite programming language.
"""
