import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from google.cloud.sql.connector import Connector, IPTypes
from dotenv import load_dotenv

load_dotenv()

# Configuration from environment variables
# Note: User will provide these in Google Cloud console
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

async def getconn():
    """Initializes the Cloud SQL connector and returns a connection."""
    connector = Connector()
    conn = await connector.connect_async(
        INSTANCE_CONNECTION_NAME,
        "asyncpg",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
        ip_type=IPTypes.PUBLIC # or PRIVATE depending on VPC setup
    )
    return conn

# Create async engine using the connector
engine = create_async_engine(
    "postgresql+asyncpg://",
    async_creator=getconn,
)

# Session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    """FastAPI dependency for database sessions."""
    async with async_session() as session:
        yield session
