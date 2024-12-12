from fastapi import FastAPI
from utils.logging_utils import get_logger

logger = get_logger(__name__)

def factory_app(debug: bool = False) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # config = configuration.factory_config()
        # metagraph = config.metagraph
        sync_thread = None
        # if metagraph.substrate is not None:
            # sync_thread = threading.Thread(target=metagraph.periodically_sync_nodes, daemon=True)
            # sync_thread.start()

        yield

        logger.info("Shutting down...")

        # config.encryption_keys_handler.close()
        # metagraph.shutdown()
        # if metagraph.substrate is not None and sync_thread is not None:
        #     sync_thread.join()

    app = FastAPI(lifespan=lifespan, debug=debug)

    # handshake_router = handshake_factory_router()

    return app