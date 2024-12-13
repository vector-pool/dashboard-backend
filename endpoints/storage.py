from fastapi import Depends, Request, Header  # Added Request import
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
    ensure_database_exists,
    connect_to_db,
    create_tables,
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
    payload = await request.body()
    
    
    miner_uid = payload["miner_uid"]
    total_storage_size = payload["total_storage_size"]
    weight = payload["weight"] 
    request_cicle_score = payload["request_cicle_score"]
    passed_request_count = payload["passed_request_count"]
    
    metagraph = bt.subtensor(network = subtensor_network).metagraph(netuid)
    
    incentive = metagraph.I[miner_uid]
    
    trust = metagraph.T[miner_uid]
    
    miner_status = (miner_uid, total_storage_size, incentive, weight, passed_request_count)
    
    operations = payload["operations"]
    
    ops = []
    for operation in operations:
        request_type = operation["request_type"]
        s_f = operation["s_f"]
        score = operation["score"]
        timestamp = operation["timestamp"]
        if request_type is not "read":
            ops.append(miner_uid, validator_hotkey, request_type, s_f, score, timestamp)
        else:
            ops.append(miner_uid, validator_hotkey, request_type, s_f, score, timestamp, request_cicle_score)

    ensure_database_exists()
    
    conn = connect_to_db()
    
    create_tables(conn)
    
    write_miner_status(conn, miner_uid, total_storage_size, incentive, weight, passed_request_count)
    
    write_operations(conn, ops)
    
    return "Get the miner data correctly."  


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