"""
Long-term Memory Service.

Interfaces with Qdrant to store and retrieve semantic interactions.
Uses the EmbeddingsService to encode text before storing/searching.
"""

from typing import Any, Dict, List, Optional
import uuid

from qdrant_client.models import Distance, PointStruct, VectorParams
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import get_settings
from app.core.vector_db import VectorDB
from app.services.embeddings import EmbeddingsService
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class MemoryService:
    """Manages storing and querying semantic memories in Qdrant."""

    @classmethod
    async def store_interaction(cls, user_phone: str, interaction_text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store a conversation interaction in the vector database.

        Args:
            user_phone: The customer's WhatsApp number.
            interaction_text: The string content of the memory/message.
            metadata: Any additional key-value JSON data to attach.

        Returns:
            The generated UUID point ID for the stored record.
        """
        point_id = str(uuid.uuid4())
        vector = EmbeddingsService.encode(interaction_text)

        payload = metadata or {}
        payload["user_phone"] = user_phone
        payload["text"] = interaction_text

        client = VectorDB.get_client()

        try:
            client.upsert(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,  # type: ignore
                        payload=payload
                    )
                ]
            )
            logger.debug("Stored interaction for %s (id: %s)", user_phone, point_id)
            return point_id
        except Exception as exc:
            logger.error("Failed to store memory for %s: %s", user_phone, exc)
            raise

    @classmethod
    async def retrieve_memories(cls, user_phone: str, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for semantically similar interactions for a specific user.

        Args:
            user_phone: The customer's WhatsApp number to filter by.
            query_text: The query string to search for.
            limit: Maximum number of results to return.

        Returns:
            A list of dictionary payloads from the matched points.
        """
        query_vector = EmbeddingsService.encode(query_text)
        client = VectorDB.get_client()

        try:
            # We filter by the user's phone number so memories remain isolated
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            user_filter = Filter(
                must=[
                    FieldCondition(
                        key="user_phone",
                        match=MatchValue(value=user_phone)
                    )
                ]
            )
            hits = client.query_points(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query=query_vector,
                query_filter=user_filter,
                limit=limit
            )   

            results = [point.payload for point in hits.points if point.payload]
            logger.debug("Retrieved %d memories for %s matching '%s'", len(results), user_phone, query_text)
            return results  # type: ignore
        except Exception as exc:
            logger.error("Failed to retrieve memories for %s: %s", user_phone, exc)
            return []

    @classmethod
    async def get_user_summary(cls, user_phone: str) -> Dict[str, Any]:
        """
        Aggregate a summary profile of the user from long-term memory.
        In a full implementation, this might call the LLM to summarize recent Qdrant points.
        """
        logger.info("Fetching long-term memory summary for %s", user_phone)
        
        # In a real implementation we would search for all orders or run a rolling summary.
        # This acts as a bridge for the 'get_user_history' tool.
        
        # Stub: Return mock aggregate
        return {
            "user_phone": user_phone,
            "status": "summary_stub",
            "notes": "Full LLM-based summarization deferred to Opus"
        }
