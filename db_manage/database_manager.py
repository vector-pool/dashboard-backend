import psycopg2
from psycopg2 import sql
from typing import List, Optional, Tuple
import json
from dotenv import load_dotenv
import os
from utils.logging_utils import get_logger

logger = get_logger(__name__)

load_dotenv()
db_user_name = os.getenv("POSTGRESQL_VALIDATOR_USER_NAME")
password = os.getenv("VALI_DB_PASSWORD")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

def ensure_database_exists() -> bool:
    """Ensure the database exists, create if not."""
    conn = psycopg2.connect(dbname='postgres', user=db_user_name, password=password, host='localhost', port=db_port)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [db_name])
            exists = cur.fetchone()
            if not exists:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
                return False
            return True
    finally:
        conn.close()

def connect_to_db():
    """Connect to the specified database."""
    conn = psycopg2.connect(dbname=db_name, user=db_user_name, password=password, host='localhost', port=db_port)
    logger.debug("Correctly connected to DATABASE")
    return conn

def create_tables(conn):
    """Create tables if they do not exist."""
    commands = (
        """
        CREATE TABLE IF NOT EXISTS miner_status (
            id SERIAL PRIMARY KEY,
            miner_uid INTEGER NOT NULL UNIQUE,
            total_storage_size FLOAT NOT NULL,
            request_cicle_score FLOAT NOT NULL,
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS operations (
            id SERIAL PRIMARY KEY,
            miner_uid INTEGER NOT NULL REFERENCES miner_status(miner_uid),
            request_type VARCHAR(255) NOT NULL,
            s_f VARCHAR(255) NOT NULL,
            timestamp
        )
        """,
    )
    with conn.cursor() as cur:
        for command in commands:
            cur.execute(command)
        conn.commit()
