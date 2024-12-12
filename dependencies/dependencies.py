from fastapi import Depends, Header, HTTPException

from utils import constants as cst
from utils.logging_utils import get_logger
import yaml

logger = get_logger(__name__)

from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Optional
from hashlib import sha256
from substrateinterface import Keypair
from datetime import datetime

async def verify_request(request: Request) -> None:
    headers = request.headers
    body = await request.body()
    
    signature = headers.get("Request-Signature")
    timestamp = headers.get("Timestamp")
    uuid = headers.get("Uuid")
    signed_for = headers.get("Signed-For")
    signed_by = headers.get("Signed-By")
    now = round(datetime.utcnow().timestamp() * 1000)

    error_message = _verify_request_internal(
        signature, body, timestamp, uuid, signed_for, signed_by, now
    )
    
    if error_message:
        raise HTTPException(status_code=400, detail=error_message)

async def _verify_request_internal(
    signature, body: bytes, timestamp, uuid, signed_for, signed_by, now
) -> Optional[str]:
    if not isinstance(signature, str):
        return "Invalid Signature"
    try:
        timestamp = int(timestamp)
    except ValueError:
        return "Invalid Timestamp"
    if not isinstance(signed_by, str):
        return "Invalid Sender key"
    if not isinstance(signed_for, str):
        return "Invalid receiver key"
    if not isinstance(uuid, str):
        return "Invalid uuid"
    if not isinstance(body, bytes):
        return "Body is not of type bytes"
    
    ALLOWED_DELTA_MS = 8000
    keypair = Keypair(ss58_address=signed_by)
    if timestamp + ALLOWED_DELTA_MS < now:
        return "Request is too stale"
    
    message = f"{sha256(body).hexdigest()}.{uuid}.{timestamp}.{signed_for}"
    verified = keypair.verify(message, signature)
    if not verified:
        return "Signature Mismatch"
    
    return None

async def white_list(
    validator_hotkey: str = Header(..., alias=cst.VALIDATOR_HOTKEY),
):
    white_validator_hotkeys = yaml.safe_load("config.yaml")
    if validator_hotkey not in white_validator_hotkeys:
        logger.debug("Authentication failed: Hotkey not found in the whitelist.")
        raise HTTPException(
            status_code=401,
            detail="Validator not registered with subnet owner. Please contact the subnet owner to whitelist your hotkey.",
        )
    print(validator_hotkey)