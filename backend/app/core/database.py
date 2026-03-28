"""
MongoDB async connection manager.

Uses Motor (async wrapper around PyMongo) for fully asynchronous database
operations with connection pooling and graceful shutdown.
"""

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MongoDB:
    """Manages the async MongoDB connection lifecycle."""

    _client: Optional[AsyncIOMotorClient] = None
    _database: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls) -> None:
        """
        Establish the MongoDB connection with connection pooling.

        Reads connection parameters from Settings and pings the server to
        verify the connection is alive.
        """
        settings = get_settings()
        try:
            cls._client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
                maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
            cls._database = cls._client[settings.MONGODB_DB_NAME]

            # Verify the connection by issuing a ping command
            await cls._client.admin.command("ping")
            logger.info(
                "MongoDB connected successfully",
                extra={
                    "database": settings.MONGODB_DB_NAME,
                    "host": settings.MONGODB_URI.split("@")[-1],  # hide credentials
                },
            )
        except Exception as exc:
            logger.error("Failed to connect to MongoDB: %s", exc)
            raise

    @classmethod
    async def disconnect(cls) -> None:
        """Close the MongoDB connection gracefully."""
        if cls._client is not None:
            cls._client.close()
            cls._client = None
            cls._database = None
            logger.info("MongoDB connection closed")

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """
        Return the default database instance.

        Raises RuntimeError if called before ``connect()``.
        """
        if cls._database is None:
            raise RuntimeError(
                "MongoDB is not connected. Call MongoDB.connect() first."
            )
        return cls._database

    @classmethod
    def get_collection(cls, name: str):
        """
        Return a collection from the default database.

        Args:
            name: Collection name.

        Returns:
            An ``AsyncIOMotorCollection`` instance.
        """
        return cls.get_database()[name]

    @classmethod
    async def is_connected(cls) -> bool:
        """Check whether the MongoDB server is reachable."""
        if cls._client is None:
            return False
        try:
            await cls._client.admin.command("ping")
            return True
        except Exception:
            return False
