"""
Proactive Customer Engagement Service (Feature 4).

To be wired up by Opus.
"""
import asyncio
from typing import Dict
from datetime import datetime, timedelta

# Avoid circular imports if any, Opus will adjust dependencies
from app.services.llm import GroqService

class EngagementService:
    def __init__(self, db, whatsapp_service):
        self.db = db
        self.whatsapp_service = whatsapp_service
        
    async def check_inactive_customers(self):
        """Re-engage customers who haven't ordered in 7 days."""
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        # Find inactive customers
        cursor = self.db.users.find({
            "last_order_date": {"$lt": seven_days_ago},
            "opt_out": {"$ne": True}
        })
        inactive = await cursor.to_list(length=100)
        
        for user in inactive:
            message = await self._generate_reengagement_message(user)
            await self.whatsapp_service.send_whatsapp_message(user["phone"], message)
            await self._track_engagement_event(user["phone"], "reengagement", message)
    
    async def _generate_reengagement_message(self, user: Dict) -> str:
        """Generate personalized re-engagement message."""
        # Opus to implement favorite items
        favorite_items = ["Veg Biryani"]
        
        prompt = f"""
        Generate a friendly re-engagement message for a customer.
        
        Customer name: {user.get("name", "there")}
        Last order: {user.get("last_order_date")}
        Favorite items: {favorite_items}
        
        Include:
        - Warm greeting
        - Mention we miss them
        - Suggest their favorite item
        - Offer 10% discount
        - Keep it short and friendly
        """
        message = await GroqService.generate_response(
            user_message="[System Prompt Gen]",
            intent="engagement",
            tool_results={"prompt": prompt},
            user_memory={}
        )
        return message
    
    async def send_order_status_update(self, order_id: str):
        """Send proactive order status update."""
        order = await self.db.orders.find_one({"order_id": order_id})
        if not order:
            return
            
        if order["status"] == "preparing":
            message = f"Good news! Your order #{order_id} is being prepared. It'll be ready in 20 minutes! 🍽️"
        elif order["status"] == "ready":
            message = f"Your order #{order_id} is ready for pickup! 🎉"
        elif order["status"] == "delivered":
            message = f"Hope you enjoyed your meal! 😊 We'd love your feedback. Rate your experience: [link]"
        else:
            return
            
        await self.whatsapp_service.send_whatsapp_message(order["customer_phone"], message)
        await self._track_engagement_event(
            order["customer_phone"],
            "order_update",
            message,
            {"order_id": order_id}
        )
    
    async def announce_new_menu_item(self, item_id: str, target_segment: str = "all"):
        """Announce new menu item to customers."""
        item = await self.db.menu_items.find_one({"_id": item_id})
        
        # Get target customers
        if target_segment == "all":
            cursor = self.db.users.find({"opt_out": {"$ne": True}})
            customers = await cursor.to_list(length=1000)
        elif target_segment == "frequent":
            cursor = self.db.users.find({
                "order_count": {"$gte": 5},
                "opt_out": {"$ne": True}
            })
            customers = await cursor.to_list(length=500)
        else:
            customers = []
        
        message = f"🎉 New on our menu!\n\n{item['name']} - ₹{item['price']}\n{item.get('description', '')}\n\nTry it today and let us know what you think!"
        
        for customer in customers:
            await self.whatsapp_service.send_whatsapp_message(customer["phone"], message)
            await asyncio.sleep(1)  # Rate limiting
            await self._track_engagement_event(
                customer["phone"],
                "new_item_announcement",
                message,
                {"item_id": str(item_id)}
            )

    async def _track_engagement_event(self, phone: str, event_type: str, message: str, meta: Dict = None):
        """Utility to track events in DB."""
        await self.db.engagement_events.insert_one({
            "user_phone": phone,
            "event_type": event_type,
            "message": message,
            "metadata": meta or {},
            "sent_at": datetime.now()
        })
