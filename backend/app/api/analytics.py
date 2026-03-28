"""
Analytics / dashboard API endpoints.

Provides aggregate insights: overview, daily trends, top items, and customer stats.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query

from app.core.database import MongoDB
from app.core.security import get_current_user, TokenData

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ── Helpers ────────────────────────────────────────────────────────────

def _days_ago(n: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=n)


# ── Endpoints ──────────────────────────────────────────────────────────

@router.get("/overview")
async def overview(current_user: TokenData = Depends(get_current_user)):
    """Headline KPIs: total orders, revenue, customers, avg order value."""
    orders_col = MongoDB.get_collection("orders")
    bid = current_user.sub

    pipeline = [
        {"$match": {"business_id": bid}},
        {
            "$group": {
                "_id": None,
                "total_orders": {"$sum": 1},
                "total_revenue": {
                    "$sum": {
                        "$reduce": {
                            "input": "$items",
                            "initialValue": 0,
                            "in": {
                                "$add": [
                                    "$$value",
                                    {"$multiply": ["$$this.quantity", "$$this.unit_price"]},
                                ]
                            },
                        }
                    }
                },
                "customers": {"$addToSet": "$customer_phone"},
            }
        },
    ]
    results = await orders_col.aggregate(pipeline).to_list(length=1)

    if results:
        r = results[0]
        total_orders = r["total_orders"]
        total_revenue = r["total_revenue"]
        total_customers = len(r["customers"])
        avg_order_value = round(total_revenue / total_orders, 2) if total_orders else 0
    else:
        total_orders = total_revenue = total_customers = avg_order_value = 0

    return {
        "success": True,
        "data": {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "total_customers": total_customers,
            "avg_order_value": avg_order_value,
        },
        "message": "Overview retrieved",
    }


@router.get("/orders-by-day")
async def orders_by_day(
    days: int = Query(7, ge=1, le=90),
    current_user: TokenData = Depends(get_current_user),
):
    """Time-series: number of orders and revenue per day for the last N days."""
    orders_col = MongoDB.get_collection("orders")
    bid = current_user.sub
    since = _days_ago(days)

    pipeline = [
        {"$match": {"business_id": bid, "created_at": {"$gte": since}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                },
                "orders": {"$sum": 1},
                "revenue": {
                    "$sum": {
                        "$reduce": {
                            "input": "$items",
                            "initialValue": 0,
                            "in": {
                                "$add": [
                                    "$$value",
                                    {"$multiply": ["$$this.quantity", "$$this.unit_price"]},
                                ]
                            },
                        }
                    }
                },
            }
        },
        {"$sort": {"_id": 1}},
    ]
    results = await orders_col.aggregate(pipeline).to_list(length=days)
    data = [{"date": r["_id"], "orders": r["orders"], "revenue": r["revenue"]} for r in results]

    return {"success": True, "data": data, "message": f"Orders by day (last {days} days)"}


@router.get("/top-items")
async def top_items(
    limit: int = Query(10, ge=1, le=50),
    current_user: TokenData = Depends(get_current_user),
):
    """Most ordered items ranked by total quantity."""
    orders_col = MongoDB.get_collection("orders")
    bid = current_user.sub

    pipeline = [
        {"$match": {"business_id": bid}},
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.name",
                "total_quantity": {"$sum": "$items.quantity"},
                "total_revenue": {
                    "$sum": {"$multiply": ["$items.quantity", "$items.unit_price"]}
                },
            }
        },
        {"$sort": {"total_quantity": -1}},
        {"$limit": limit},
    ]
    results = await orders_col.aggregate(pipeline).to_list(length=limit)
    data = [
        {"name": r["_id"], "total_quantity": r["total_quantity"], "total_revenue": r["total_revenue"]}
        for r in results
    ]

    return {"success": True, "data": data, "message": f"Top {limit} items"}


@router.get("/customer-stats")
async def customer_stats(current_user: TokenData = Depends(get_current_user)):
    """New vs repeat customers (repeat = placed more than one order)."""
    orders_col = MongoDB.get_collection("orders")
    bid = current_user.sub

    pipeline = [
        {"$match": {"business_id": bid}},
        {"$group": {"_id": "$customer_phone", "order_count": {"$sum": 1}}},
        {
            "$group": {
                "_id": None,
                "total_customers": {"$sum": 1},
                "new_customers": {
                    "$sum": {"$cond": [{"$eq": ["$order_count", 1]}, 1, 0]}
                },
                "repeat_customers": {
                    "$sum": {"$cond": [{"$gt": ["$order_count", 1]}, 1, 0]}
                },
            }
        },
    ]
    results = await orders_col.aggregate(pipeline).to_list(length=1)
    data = results[0] if results else {"total_customers": 0, "new_customers": 0, "repeat_customers": 0}
    data.pop("_id", None)

    return {"success": True, "data": data, "message": "Customer stats retrieved"}
