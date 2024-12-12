import os

# from dotenv import load_dotenv

# load_dotenv("dev.env")  # Important to load this before importing anything else!

from utils.logging_utils import get_logger
import server
from endpoints.storage import stogate_router

logger = get_logger(__name__)

app = server.factory_app(debug=True)

app.include_router(stogate_router())

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8091)