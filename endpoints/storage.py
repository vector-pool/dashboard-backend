from fastapi import Depends, Request, Header  # Added Request import
from fastapi.routing import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from dependencies.dependencies import white_list, verify_request
from utils import constants as cst
from utils.logging_utils import get_logger

logger = get_logger(__name__)

class ContentModel(BaseModel):
    data: Dict[str, Any]

async def handle_miner_data(
    request: Request,
    validator_hotkey: str = Header(..., alias=cst.VALIDATOR_HOTKEY),
):
    # Log the encrypted payload received
    payload = await request.body()
    
    return "get the request correctly"



def stogate_router() -> APIRouter:
    router = APIRouter()
    router.add_api_route(
        "/miner_data_router",
        handle_miner_data,
        tags=["miner_data"],
        dependencies=[Depends(white_list), Depends(verify_request)],
        methods=["POST"],
    )
    return router