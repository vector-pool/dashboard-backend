from fastapi import Depends, Request, Header
from fastapi.routing import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from dependencies.dependencies import white_list, verify_request
from utils import constants as cst
from utils.logging_utils import get_logger
import bittensor as bt
from db_manage.database_manager import (
    write_miner_status,
    write_operations,
    connect_to_db,
)
from dotenv import load_dotenv
import os


load_dotenv()

subtensor_url = os.getenv("SUBTENSOR_ADDRESS")
subtensor_network = os.getenv("SUBTENSOR_NETWORK")
netuid = os.getenv("NETUID")

logger = get_logger(__name__)

async def handle_miner_data(
    request: Request,
    validator_hotkey: str = Header(..., alias=cst.VALIDATOR_HOTKEY),
):
    # Log the encrypted payload received
    payload = await request.json()  # Use .json() to parse JSON payload

    miner_uid = payload["miner_uid"]
    total_storage_size = payload["total_storage_size"]
    weight = payload["weight"] 
    request_cicle_score = payload["request_cicle_score"]
    passed_request_count = payload["passed_request_count"]

    neuron_info = bt.subtensor(network=subtensor_network).neuron_for_uid(miner_uid, netuid)

    incentive = neuron_info.incentive
    trust = neuron_info.trust
    coldkey = neuron_info.coldkey
    hotkey = neuron_info.hotkey
    ip = neuron_info.axon_info.ip
    port = neuron_info.axon_info.port
    emission = neuron_info.emission
    daily_rewards = emission * 20

    miner_status = (miner_uid, total_storage_size, incentive, weight, passed_request_count)

    operations = payload["operations"]

    ops = []
    for operation in operations:
        request_type = operation["request_type"]
        s_f = operation["s_f"]
        score = operation["score"]
        timestamp = operation["timestamp"]
        if request_type != "read":
            ops.append((miner_uid, validator_hotkey, request_type, s_f, score, timestamp))
        else:
            ops.append((miner_uid, validator_hotkey, request_type, s_f, score, timestamp, request_cicle_score))

    # Use the global db_pool initialized in your startup event
    db_pool = await connect_to_db()
    
    async with db_pool.acquire() as conn:
        await write_miner_status(
            conn, miner_uid, coldkey, hotkey, ip, port, incentive, trust,
            daily_rewards, passed_request_count, weight, total_storage_size
        )

        await write_operations(conn, ops)

    return {"message": "Miner data processed successfully."}

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
