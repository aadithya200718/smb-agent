"""
Authentication and Business Registration Service.
"""

import uuid
from typing import Optional, Dict, Any

from app.core.database import MongoDB
from app.core.security import hash_password, verify_password, create_access_token
from app.models.business import Business
from app.utils.logger import get_logger

logger = get_logger(__name__)

class AuthService:
    
    @staticmethod
    async def register_business(email: str, password: str, business_name: str, phone: str) -> Business:
        """
        Register a new business and securely hash their password.
        """
        collection = MongoDB.get_collection("businesses")
        
        existing = await collection.find_one({"owner_email": email})
        if existing:
            raise ValueError("Email already registered")
            
        business_id = f"biz_{uuid.uuid4().hex[:12]}"
        hashed_password = hash_password(password)
        
        business = Business(
            business_id=business_id,
            name=business_name,
            owner_email=email,
            owner_password=hashed_password,
            phone=phone
        )
        
        doc = business.model_dump()
        # owner_password has exclude=True on the model (for API safety),
        # so we must add it back explicitly for storage.
        doc["owner_password"] = hashed_password
        await collection.insert_one(doc)
        logger.info("Registered new business: %s", business_id)
        return business

    @staticmethod
    async def authenticate(email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a business owner and return their DB record if valid.
        """
        collection = MongoDB.get_collection("businesses")
        business_data = await collection.find_one({"owner_email": email})
        
        if not business_data:
            return None
            
        if not verify_password(password, business_data["owner_password"]):
            return None
            
        return business_data

    @staticmethod
    def create_tokens(business_id: str, email: str) -> Dict[str, str]:
        """
        Generate a JWT token for the authenticated user.
        """
        access_token = create_access_token(
            data={"sub": business_id, "email": email, "role": "business_owner"}
        )
        return {"access_token": access_token, "token_type": "bearer"}

auth_service = AuthService()
