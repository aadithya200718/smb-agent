"""
Qdrant vector database connection manager.

Handles client initialization, collection creation, and connection health
checks for the Qdrant vector search engine.
"""

from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, VectorParams

from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VectorDB:
    """Manages the Qdrant client lifecycle."""

    _client: Optional[QdrantClient] = None

    @classmethod
    async def connect(cls) -> None:
        """
        Initialise the Qdrant client and ensure the default collection exists.

        Connection parameters are read from Settings.
        """
        settings = get_settings()
        try:
            cls._client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=10,
            )

            # Create the default collection if it doesn't already exist
            await cls._ensure_collection(
                name=settings.QDRANT_COLLECTION_NAME,
                vector_size=settings.QDRANT_VECTOR_SIZE,
            )

            logger.info(
                "Qdrant connected successfully",
                extra={
                    "url": settings.QDRANT_URL,
                    "collection": settings.QDRANT_COLLECTION_NAME,
                },
            )
        except Exception as exc:
            logger.error("Failed to connect to Qdrant: %s", exc)
            raise

    @classmethod
    async def _ensure_collection(cls, name: str, vector_size: int) -> None:
        """Create a Qdrant collection if it does not already exist."""
        if cls._client is None:
            raise RuntimeError("Qdrant client is not initialised.")

        try:
            cls._client.get_collection(name)
            logger.debug("Qdrant collection '%s' already exists", name)
        except (UnexpectedResponse, Exception):
            cls._client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Created Qdrant collection '%s' (dim=%d)", name, vector_size)

    @classmethod
    async def disconnect(cls) -> None:
        """Close the Qdrant client connection."""
        if cls._client is not None:
            cls._client.close()
            cls._client = None
            logger.info("Qdrant connection closed")

    @classmethod
    def get_client(cls) -> QdrantClient:
        """
        Return the active Qdrant client.

        Raises RuntimeError if called before ``connect()``.
        """
        if cls._client is None:
            raise RuntimeError(
                "Qdrant is not connected. Call VectorDB.connect() first."
            )
        return cls._client

    @classmethod
    async def is_connected(cls) -> bool:
        """Check whether the Qdrant server is reachable."""
        if cls._client is None:
            return False
        try:
            cls._client.get_collections()
            return True
        except Exception:
            return False
