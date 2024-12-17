from fastapi import Header, HTTPException, Request
from utils import constants as cst
from hashlib import sha256
from typing import Optional
from substrateinterface import Keypair
from datetime import datetime
from utils.logging_utils import get_logger
import yaml
import json

logger = get_logger(__name__)   

with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

white_validator_hotkeys = config.get("white_validator_hotkeys", [])

async def verify_request(request: Request) -> None:
    headers = request.headers
    body = await request.body()
    
    signature = headers.get("Request-Signature")
    timestamp = headers.get("Timestamp")
    uuid = headers.get("Uuid")
    signed_for = headers.get("Signed-For")
    signed_by = headers.get("Signed-By")
    now = round(datetime.utcnow().timestamp() * 1000)

    error_message = await _verify_request_internal(
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
    
    # Convert body to a dictionary (assuming JSON format)
    try:
        body_data = json.loads(body)
    except json.JSONDecodeError:
        return "Invalid JSON body"
    
    # {'miner_uid': 5, 'total_storage_size': 0.007231179624795914, 'operations': [{'request_type': 'create', 'S_F': 'success', 'score': 1.0, 'timestamp': '2024-12-13T18:29:37.549819'}], 'request_cycle_score': 0.021875000000000002, 'weight': 1.0, 'passed_request_count': 248}
    expected_keys = ["miner_uid", "total_storage_size", "weight", "request_cycle_score", "passed_request_count", "operations"]
    for key in expected_keys:
        if key not in body_data:
            return f"Missing expected body value: {key}"
    operations = body_data["operations"]
    if len(operations) == 0:
        return "The body data don't contains any operation info."
    expected_operation_keys = ["timestamp", "request_type", "s_f", "score"]
    for operation in operations:
        for key in expected_operation_keys:
            if key not in operation:
                return f"operation data missing the value: {key}"
    
    ALLOWED_DELTA_MS = 8000
    keypair = Keypair(ss58_address=signed_by)
    if timestamp + ALLOWED_DELTA_MS < now:
        return "Request is too stale"
    message = f"{sha256(body).hexdigest()}.{uuid}.{timestamp}.{signed_for}"
    verified = keypair.verify(message, signature)
    if not verified:
        return "Signature Mismatch"
    print("Verified Signature")
    return None


async def white_list(
    validator_hotkey: str = Header(..., alias=cst.SIGNED_BY),
):
    if validator_hotkey not in white_validator_hotkeys:
        logger.debug("Authentication failed: Hotkey not found in the whitelist.")
        raise HTTPException(
            status_code=401,
            detail="Validator not registered with subnet owner. Please contact the subnet owner to whitelist your hotkey.",
        )
    print("Verified whitelist")