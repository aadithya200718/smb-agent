"""
Idempotency Utilities.

Ensures that repeated webhook calls do not create duplicate orders or payments.
"""

from app.core.database import MongoDB
from app.utils.logger import get_logger
from datetime import datetime, timezone
import hashlib

logger = get_logger(__name__)

class IdempotencyManager:
    """Manages idempotency keys in MongoDB to prevent duplicate actions."""
    
    @staticmethod
    def generate_key(*args) -> str:
        """Generate a deterministic key from input values."""
        key_input = "-".join(str(a) for a in args)
        return hashlib.sha256(key_input.encode()).hexdigest()
        
    @staticmethod
    async def check_and_lock(key: str, action: str) -> bool:
        """
        Check if the key exists, if not create it.
        Returns True if this is a fresh locked action, False if it already exists (duplicate).
        """
        db = MongoDB.get_database()
        try:
            # We use an atomic insert. The collection should have a unique index on 'key'.
            await db.idempotency_keys.insert_one({
                "key": key,
                "action": action,
                "created_at": datetime.now(timezone.utc)
            })
            return True # Successfully locked
        except Exception:
            # DuplicateKeyError or similar
            logger.info(f"Idempotency hit! Action {action} with key {key} already executed.")
            return False
