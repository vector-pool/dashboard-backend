from fastapi import FastAPI
from utils.logging_utils import get_logger
from contextlib import asynccontextmanager
import asyncio
from db_manage.database_manager import startup_db_manager, shutdown_db_manager, maintain_database

logger = get_logger(__name__)

def factory_app(debug: bool = False) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):

        db_pool = await startup_db_manager()
        
        # Start the maintenance task
        maintenance_task = asyncio.create_task(maintain_database(db_pool))
        
        yield
        
        logger.info("Shutting down...")
        
        # Cancel the maintenance task
        maintenance_task.cancel()
        await maintenance_task
        
        await shutdown_db_manager

    app = FastAPI(lifespan=lifespan, debug=debug)

    # handshake_router = handshake_factory_router()

    return app
