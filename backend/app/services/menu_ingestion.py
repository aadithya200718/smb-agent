"""
Menu Ingestion Pipeline.

Syncs menu data from Petpooja POS into MongoDB and manages
menu versioning and embedding sync for semantic search.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.database import MongoDB
from app.integrations.petpooja import petpooja_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MenuIngestionPipeline:
    """
    Pulls menu data from Petpooja, normalizes it, versions it,
    and stores in MongoDB. Detects changes via content hashing.
    """

    @staticmethod
    def _compute_menu_hash(items: List[Dict[str, Any]]) -> str:
        """Compute a deterministic hash of the menu for change detection."""
        serialized = json.dumps(items, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    @staticmethod
    async def sync_menu(business_id: str = "BIZ001") -> Dict[str, Any]:
        """
        Full menu sync from POS to MongoDB.
        
        Steps:
          1. Fetch menu from Petpooja
          2. Normalize items to our schema
          3. Check if menu has changed (hash comparison)
          4. If changed, create new version + update active menu
          5. Return sync summary
        """
        # 1. Fetch from POS
        pos_items = await petpooja_client.fetch_menu()

        if not pos_items:
            logger.warning("Menu sync: no items returned from POS")
            return {"status": "empty", "items_synced": 0}

        # 2. Normalize
        normalized = []
        for item in pos_items:
            normalized.append({
                "item_id": item.get("item_id", ""),
                "business_id": business_id,
                "name": item.get("name", ""),
                "price": float(item.get("price", 0)),
                "category": item.get("category", "Uncategorized"),
                "description": item.get("description", ""),
                "available": item.get("available", True),
                "stock": item.get("stock", 0),
                "variants": item.get("variants", []),
            })

        # 3. Hash check
        new_hash = MenuIngestionPipeline._compute_menu_hash(normalized)

        db = MongoDB.get_database()
        current_version = await db.menu_versions.find_one(
            {"business_id": business_id, "active": True}
        )

        if current_version and current_version.get("content_hash") == new_hash:
            # No changes detected — update stock only
            for item in normalized:
                await db.menu_items.update_one(
                    {"item_id": item["item_id"], "business_id": business_id},
                    {"$set": {"stock": item["stock"], "available": item["available"]}},
                )
            logger.info("Menu sync: no changes, stock updated only (%d items)", len(normalized))
            return {"status": "stock_updated", "items_synced": len(normalized), "version_changed": False}

        # 4. New version
        version_number = (current_version.get("version", 0) + 1) if current_version else 1

        # Deactivate old version
        await db.menu_versions.update_many(
            {"business_id": business_id},
            {"$set": {"active": False}},
        )

        # Create new version record
        await db.menu_versions.insert_one({
            "business_id": business_id,
            "version": version_number,
            "content_hash": new_hash,
            "active": True,
            "item_count": len(normalized),
            "created_at": datetime.now(timezone.utc),
        })

        # 5. Upsert all items
        for item in normalized:
            await db.menu_items.update_one(
                {"item_id": item["item_id"], "business_id": business_id},
                {"$set": {**item, "updated_at": datetime.now(timezone.utc)}},
                upsert=True,
            )

        logger.info("Menu sync: version %d created with %d items", version_number, len(normalized))
        return {
            "status": "updated",
            "items_synced": len(normalized),
            "version": version_number,
            "version_changed": True,
        }

    @staticmethod
    async def get_menu_version(business_id: str = "BIZ001") -> Optional[Dict[str, Any]]:
        """Get the current active menu version info."""
        db = MongoDB.get_database()
        return await db.menu_versions.find_one(
            {"business_id": business_id, "active": True}
        )

    @staticmethod
    async def get_version_history(business_id: str = "BIZ001", limit: int = 10) -> List[Dict[str, Any]]:
        """Get menu version history."""
        db = MongoDB.get_database()
        cursor = db.menu_versions.find(
            {"business_id": business_id}
        ).sort("version", -1).limit(limit)
        return await cursor.to_list(length=limit)


class EmbeddingSync:
    """
    Syncs menu item embeddings for semantic search.
    Uses sentence-transformers for embedding generation.
    """

    @staticmethod
    async def sync_embeddings(business_id: str = "BIZ001") -> Dict[str, Any]:
        """
        Generate and store embeddings for all menu items.
        Used for semantic menu search (e.g., "something spicy" → Chole Bhature).
        """
        try:
            from sentence_transformers import SentenceTransformer

            db = MongoDB.get_database()
            cursor = db.menu_items.find({"business_id": business_id, "available": True})
            items = await cursor.to_list(length=200)

            if not items:
                return {"status": "no_items", "count": 0}

            # Build text for embedding
            texts = []
            for item in items:
                text = f"{item.get('name', '')} - {item.get('description', '')} - {item.get('category', '')}"
                texts.append(text)

            # Generate embeddings
            model = SentenceTransformer("all-MiniLM-L6-v2")
            embeddings = model.encode(texts)

            # Store embeddings
            for i, item in enumerate(items):
                await db.menu_embeddings.update_one(
                    {"item_id": item["item_id"], "business_id": business_id},
                    {
                        "$set": {
                            "embedding": embeddings[i].tolist(),
                            "text": texts[i],
                            "updated_at": datetime.now(timezone.utc),
                        }
                    },
                    upsert=True,
                )

            logger.info("Embedding sync: %d items embedded", len(items))
            return {"status": "synced", "count": len(items)}

        except Exception as e:
            logger.error("Embedding sync failed: %s", e)
            return {"status": "error", "error": str(e)}


# Singletons
menu_pipeline = MenuIngestionPipeline()
embedding_sync = EmbeddingSync()
