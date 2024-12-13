import asyncpg
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException

# Environment variables and logging setup
import os
from dotenv import load_dotenv
load_dotenv()

db_user_name = os.getenv("POSTGRESQL_VALIDATOR_USER_NAME")
password = os.getenv("VALI_DB_PASSWORD")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

app = FastAPI()

async def connect_to_db():
    """Establish a connection pool to the database."""
    return await asyncpg.create_pool(
        user=db_user_name,
        password=password,
        database=db_name,
        host="localhost",
        port=db_port,
        min_size=1,
        max_size=10  # Adjust based on your expected load
    )

async def ensure_database_exists():
    """Ensure the database exists."""
    conn = await asyncpg.connect(
        user=db_user_name,
        password=password,
        database="postgres",
        host="localhost",
        port=db_port,
    )
    try:
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if not result:
            await conn.execute(f"CREATE DATABASE {db_name}")
            return False
        return True
    finally:
        await conn.close()

async def create_tables(pool):
    """Create tables if they do not exist."""
    commands = [
        """
        CREATE TABLE IF NOT EXISTS miner_status (
            id SERIAL PRIMARY KEY,
            miner_uid INTEGER NOT NULL UNIQUE,
            coldkey VARCHAR(255) NOT NULL,
            hotkey VARCHAR(255) NOT NULL,
            ip VARCHAR(255) NOT NULL,
            port INTEGER NOT NULL,
            incentive DOUBLE PRECISION NOT NULL,
            trust DOUBLE PRECISION NOT NULL,
            daily_rewards DOUBLE PRECISION NOT NULL,
            passed_request_count INTEGER NOT NULL,
            weight DOUBLE PRECISION NOT NULL,
            total_storage_size DOUBLE PRECISION NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS operations (
            id SERIAL PRIMARY KEY,
            miner_uid INTEGER NOT NULL REFERENCES miner_status(miner_uid),
            validator VARCHAR(255) NOT NULL,
            request_type VARCHAR(255) NOT NULL,
            s_f VARCHAR(255) NOT NULL,
            score DOUBLE PRECISION NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            request_cycle_score DOUBLE PRECISION
        )
        """,
    ]
    async with pool.acquire() as conn:
        for command in commands:
            await conn.execute(command)

async def write_miner_status(
    pool,
    miner_uid: int,
    coldkey: str,
    hotkey: str,
    ip: str,
    port: int,
    incentive: float,
    trust: float,
    daily_rewards: float,
    passed_request_count: int,
    weight: float,
    total_storage_size: float,
):
    """Insert or update the miner_status table using upsert."""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO miner_status (miner_uid, coldkey, hotkey, ip, port, incentive, trust, daily_rewards, passed_request_count, weight, total_storage_size)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (miner_uid) DO UPDATE
            SET coldkey = EXCLUDED.coldkey,
                hotkey = EXCLUDED.hotkey,
                ip = EXCLUDED.ip,
                port = EXCLUDED.port,
                incentive = EXCLUDED.incentive,
                trust = EXCLUDED.trust,
                daily_rewards = EXCLUDED.daily_rewards,
                passed_request_count = EXCLUDED.passed_request_count,
                weight = EXCLUDED.weight,
                total_storage_size = EXCLUDED.total_storage_size
            """,
            miner_uid,
            coldkey,
            hotkey,
            ip,
            port,
            incentive,
            trust,
            daily_rewards,
            passed_request_count,
            weight,
            total_storage_size,
        )

async def write_operations(pool, operations_list: list):
    """Insert multiple rows into the operations table."""
    async with pool.acquire() as conn:
        insert_query = """
            INSERT INTO operations (miner_uid, validator, request_type, s_f, score, timestamp, request_cicle_score)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        await conn.executemany(insert_query, operations_list)

async def maintain_database(pool):
    """Periodically clean up old records in the operations table."""
    while True:
        async with pool.acquire() as conn:
            cutoff_time = datetime.now() - timedelta(days=1)
            await conn.execute(
                "DELETE FROM operations WHERE timestamp < $1", cutoff_time
            )
        await asyncio.sleep(3600)  # Run every hour

async def startup_db_manager():
    """Initialize the database on application startup."""
    await ensure_database_exists()
    global db_pool
    db_pool = await connect_to_db()
    await create_tables(db_pool)

    return db_pool
    # Start the background task for database maintenance
    # asyncio.create_task(maintain_database(db_pool))

async def shutdown_db_manager():
    """Close the database pool on application shutdown."""
    await db_pool.close()

async def update_miner_status(
    miner_uid: int,
    coldkey: str,
    hotkey: str,
    ip: str,
    port: int,
    incentive: float,
    trust: float,
    daily_rewards: float,
    passed_request_count: int,
    weight: float,
    total_storage_size: float,
):
    """Endpoint to update miner status."""
    try:
        await write_miner_status(
            db_pool,
            miner_uid,
            coldkey,
            hotkey,
            ip,
            port,
            incentive,
            trust,
            daily_rewards,
            passed_request_count,
            weight,
            total_storage_size,
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def add_operations(operations: list):
    """Endpoint to add multiple operations."""
    try:
        await write_operations(db_pool, operations)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))