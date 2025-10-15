import logging
from typing import Callable, Awaitable
from fastapi import FastAPI

logger = logging.getLogger(__name__)

async def startup(app: FastAPI) -> None:
    """
    Initialize application services when the server starts.
    
    Args:
        app: The FastAPI application instance
    """
    logger.info("Starting up application...")
    # Initialize any required services here
    try:
        # Example: Initialize database connection
        # await database.connect()
        pass
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

async def shutdown(app: FastAPI) -> None:
    """
    Clean up resources when the server shuts down.
    
    Args:
        app: The FastAPI application instance
    """
    logger.info("Shutting down application...")
    # Clean up resources
    try:
        # Example: Close database connection
        # await database.disconnect()
        pass
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
        raise

def create_start_app_handler(app: FastAPI) -> Callable[[], Awaitable[None]]:
    """
    Create a startup event handler for the application.
    
    Args:
        app: The FastAPI application instance
        
    Returns:
        A coroutine that initializes the application
    """
    async def start_app() -> None:
        await startup(app)
    return start_app

def create_stop_app_handler(app: FastAPI) -> Callable[[], Awaitable[None]]:
    """
    Create a shutdown event handler for the application.
    
    Args:
        app: The FastAPI application instance
        
    Returns:
        A coroutine that cleans up resources
    """
    async def stop_app() -> None:
        await shutdown(app)
    return stop_app
