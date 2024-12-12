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
            total_storage_size DOUBLE PRECISION NOT NULL,
            incentive DOUBLE PRECISION NOT NULL,
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS operations (
            id SERIAL PRIMARY KEY,
            miner_uid INTEGER NOT NULL REFERENCES miner_status(miner_uid),
            validator VARCHAT(255) NOT NULL,
            request_type VARCHAR(255) NOT NULL,
            s_f VARCHAR(255) NOT NULL,
            score DOUBLE PRECISION NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            request_cicle_score DOUBLE PRECISION,
        )
        """,
    )
    with conn.cursor() as cur:
        for command in commands:
            cur.execute(command)
        conn.commit()

def write_miner_status(conn, miner_uid: int, total_storage_size: float, incentive: float):
    """Insert or update the miner_status table."""
    with conn.cursor() as cur:
        # Check if the miner_uid already exists
        cur.execute("""
            SELECT 1 FROM miner_status WHERE miner_uid = %s
        """, (miner_uid,))
        
        exists = cur.fetchone()
        
        if exists:
            # Update existing record
            cur.execute("""
                UPDATE miner_status
                SET total_storage_size = %s,
                    incentive = %s
                WHERE miner_uid = %s
            """, (total_storage_size, incentive, miner_uid))
        else:
            # Insert new record
            cur.execute("""
                INSERT INTO miner_status (miner_uid, total_storage_size, incentive)
                VALUES (%s, %s, %s)
            """, (miner_uid, total_storage_size, incentive))
        
        # Commit the transaction
        conn.commit()
        
def write_operations(conn, operations_list: list):
    """Insert multiple rows into the operations table."""
    with conn.cursor() as cur:
        # Prepare the SQL statement for inserting data
        insert_query = """
            INSERT INTO operations (miner_uid, validator, request_type, s_f, score, timestamp, request_cicle_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        # Execute the insert statement for each pair in the list
        for operation in operations_list:
            cur.execute(insert_query, operation)
        
        # Commit the transaction
        conn.commit()
