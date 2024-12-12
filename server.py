from fastapi import FastAPI
from utils.logging_utils import get_logger
import threading
from contextlib import asynccontextmanager
from db_manage.database_manager import initialize_database, maintain_database
logger = get_logger(__name__)

def factory_app(debug: bool = False) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        initialize_database()
        maintenance_thread = None
        maintenance_thread = threading.Thread(target=maintain_database, daemon=True)
        maintenance_thread.start()

        yield

        logger.info("Shutting down...")

        maintenance_thread.join()

    app = FastAPI(lifespan=lifespan, debug=debug)

    # handshake_router = handshake_factory_router()

    return app