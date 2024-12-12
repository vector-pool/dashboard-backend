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
    miner_hotkey: str = Header(..., alias=cst.MINER_HOTKEY),
    symmetric_key_uuid=Header(..., alias=cst.SYMMETRIC_KEY_UUID),
):
    # Log the encrypted payload received
    encrypted_payload = await request.body()
    print("Encrypted Payload (raw):", encrypted_payload)

    # Decrypt the payload directly

    # Log the decrypted payload
    if decrypted_payload:
        print("Decrypted Payload (parsed):", decrypted_payload.dict())
    else:
        print("Failed to decrypt payload. Check symmetric key or decryption logic.")

    print("The synapse received")

    return decrypted_payload
    # return {"status": "Example request received, haha"}


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