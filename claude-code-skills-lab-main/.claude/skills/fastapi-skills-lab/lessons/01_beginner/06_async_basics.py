"""
LESSON 6: Async/Await Basics
============================

FastAPI is built on async Python. Understanding async
helps you write high-performance APIs.

Key Concepts:
- async def vs def
- When to use async
- Concurrent operations
- async HTTP clients

To run:
    uv run uvicorn lessons.01_beginner.06_async_basics:app --reload
"""

import asyncio
from fastapi import FastAPI
import httpx

app = FastAPI(title="Async Basics Lesson")


# Synchronous endpoint - blocks the event loop
@app.get("/sync")
def sync_endpoint():
    """
    A synchronous endpoint.

    FastAPI runs this in a thread pool to avoid blocking.
    Use 'def' for:
    - CPU-bound operations
    - Blocking I/O (file operations, sync database calls)
    """
    return {"type": "synchronous", "message": "This uses a regular function"}


# Asynchronous endpoint - non-blocking
@app.get("/async")
async def async_endpoint():
    """
    An asynchronous endpoint.

    Use 'async def' when:
    - Making async HTTP requests (httpx, aiohttp)
    - Using async database drivers (asyncpg, motor)
    - Using async file I/O
    - Calling other async functions
    """
    return {"type": "asynchronous", "message": "This uses async/await"}


# Simulating slow operations
@app.get("/sync-slow")
def sync_slow():
    """
    Simulates a slow synchronous operation.
    Try calling this multiple times - requests are serialized.
    """
    import time
    time.sleep(2)  # Blocks for 2 seconds
    return {"message": "Slow sync operation completed"}


@app.get("/async-slow")
async def async_slow():
    """
    Simulates a slow asynchronous operation.
    Multiple requests can run concurrently!
    """
    await asyncio.sleep(2)  # Non-blocking sleep
    return {"message": "Slow async operation completed"}


# Concurrent async operations
@app.get("/concurrent")
async def concurrent_operations():
    """
    Demonstrates running multiple async operations concurrently.

    Instead of:
        result1 = await operation1()  # Wait 2s
        result2 = await operation2()  # Wait 2s more
        # Total: 4 seconds

    We do:
        results = await asyncio.gather(operation1(), operation2())
        # Total: 2 seconds (run in parallel)
    """
    async def fetch_data(name: str, delay: float):
        await asyncio.sleep(delay)
        return {"source": name, "data": f"Data from {name}"}

    # Run all operations concurrently
    results = await asyncio.gather(
        fetch_data("database", 1.0),
        fetch_data("cache", 0.5),
        fetch_data("external_api", 1.5)
    )

    return {
        "message": "All data fetched concurrently",
        "results": results
    }


# Making async HTTP requests with httpx
@app.get("/fetch-external")
async def fetch_external():
    """
    Make an async HTTP request to an external API.

    httpx is the async alternative to requests.
    Always use async client in async endpoints!
    """
    async with httpx.AsyncClient() as client:
        response = await client.get("https://httpbin.org/json")
        return {
            "status_code": response.status_code,
            "data": response.json()
        }


# Multiple concurrent HTTP requests
@app.get("/fetch-multiple")
async def fetch_multiple():
    """
    Fetch from multiple URLs concurrently.
    Much faster than sequential requests!
    """
    urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1"
    ]

    async with httpx.AsyncClient() as client:
        # Create tasks for all requests
        tasks = [client.get(url) for url in urls]
        # Wait for all to complete
        responses = await asyncio.gather(*tasks)

    return {
        "message": "Fetched 3 URLs that each take 1s",
        "note": "Total time ~1s instead of 3s!",
        "status_codes": [r.status_code for r in responses]
    }


# Background task example
from fastapi import BackgroundTasks

@app.post("/send-notification")
async def send_notification(
    email: str,
    message: str,
    background_tasks: BackgroundTasks
):
    """
    Send notification in the background.

    The response returns immediately while the
    notification is sent asynchronously.
    """
    def send_email_task(email: str, message: str):
        # Simulate sending email (would be real in production)
        import time
        time.sleep(3)  # Simulate slow email sending
        print(f"Email sent to {email}: {message}")

    # Add task to run in background
    background_tasks.add_task(send_email_task, email, message)

    return {
        "message": "Notification queued",
        "email": email
    }


"""
WHEN TO USE ASYNC vs SYNC:
--------------------------

Use async def when:
- Your code uses 'await'
- Making async HTTP requests
- Using async database drivers
- Calling async libraries

Use regular def when:
- No async operations inside
- Using synchronous libraries
- CPU-intensive calculations
- Blocking I/O operations

FastAPI handles both correctly!
"""


"""
EXERCISE 1:
-----------
Create an endpoint that fetches data from 3 different
fake "services" concurrently using asyncio.gather().
Each service should have a different delay.

EXERCISE 2:
-----------
Create an endpoint that uses BackgroundTasks to log
request details to a file (simulated with sleep + print).
"""
