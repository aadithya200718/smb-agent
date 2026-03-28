"""
WhatsApp Webhook Endpoint.

Receives incoming messages (text, voice, images) from Twilio,
validates signatures, stores chat history in MongoDB, triggers
the LangGraph agent in a background task, and sends the response
back via WhatsApp.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, BackgroundTasks, Request, Response, status
from fastapi.responses import PlainTextResponse

from app.core.config import get_settings
from app.core.database import MongoDB
from app.agent.graph import run_agent
from app.models.chat import Chat, Message
from app.services.whatsapp import whatsapp_service
from app.utils.validators import (
    parse_twilio_webhook,
    sanitize_input,
    validate_message_text,
    validate_phone_number,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# In-memory set of processed message SIDs to prevent duplicate processing.
_processed_sids: set[str] = set()


# ── Helper: MongoDB chat history ─────────────────────────────────────

async def _get_or_create_chat(customer_phone: str, business_id: str) -> Dict[str, Any]:
    """
    Fetch the existing chat document for a customer/business pair,
    or create a fresh one if none exists.
    """
    collection = MongoDB.get_collection("chats")
    doc = await collection.find_one(
        {"customer_phone": customer_phone, "business_id": business_id}
    )
    if doc:
        return doc

    chat = Chat(
        chat_id=str(uuid.uuid4()),
        business_id=business_id,
        customer_phone=customer_phone,
    )
    await collection.insert_one(chat.model_dump())
    logger.info("Created new chat record for %s", customer_phone)
    return chat.model_dump()


async def _store_message(
    customer_phone: str,
    business_id: str,
    role: str,
    content: str,
    message_sid: str,
) -> None:
    """Append a message sub-document to the chat's messages array."""
    collection = MongoDB.get_collection("chats")
    msg = Message(
        role=role,
        content=content,
        message_sid=message_sid,
    )
    await collection.update_one(
        {"customer_phone": customer_phone, "business_id": business_id},
        {
            "$push": {"messages": msg.model_dump()},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )





# ── Background task: run agent & reply ───────────────────────────────

async def _process_message_background(
    customer_phone: str,
    business_id: str,
    message_text: str,
    message_sid: str,
) -> None:
    """
    Heavy-lifting background task.

    1. Run the LangGraph agent.
    2. Send the response back to WhatsApp.
    3. Store the assistant response in chat history.
    """
    try:
        logger.info(
            "Background: processing message from %s — '%s'",
            customer_phone, message_text[:60],
        )

        # Run the AI agent pipeline
        final_state = await run_agent(
            message=message_text,
            user_phone=customer_phone,
            business_id=business_id,
        )

        response_text = final_state.get("response") or (
            "Sorry, I couldn't process your request. Please try again."
        )

        # Send response back to the user via WhatsApp
        sent = await whatsapp_service.send_message(
            to=customer_phone,
            body=response_text,
        )

        if sent:
            logger.info("Reply sent to %s (%d chars)", customer_phone, len(response_text))
        else:
            logger.error("Failed to send reply to %s", customer_phone)

        # Store the assistant's response in MongoDB
        await _store_message(
            customer_phone=customer_phone,
            business_id=business_id,
            role="assistant",
            content=response_text,
            message_sid=f"reply-{message_sid}",
        )

    except Exception as exc:
        logger.error("Background processing failed for %s: %s", customer_phone, exc)

        try:
            await whatsapp_service.send_message(
                to=customer_phone,
                body="I'm having a little trouble right now. Could you please try again in a moment?",
            )
        except Exception:
            logger.error("Even the fallback message failed for %s", customer_phone)


# ── Webhook endpoint ─────────────────────────────────────────────────

@router.post("/whatsapp", response_class=Response)
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receive incoming WhatsApp messages from Twilio.
    Supports text, voice (audio/ogg), and image messages.
    """
    # --- 1. Read raw form ------------------------------------------------
    form_data: Dict[str, str] = dict(await request.form())

    # --- 2. Signature validation -----------------------------------------
    signature = request.headers.get("X-Twilio-Signature", "")
    request_url = str(request.url)

    if settings.ENVIRONMENT == "production":
        if not whatsapp_service.validate_signature(request_url, form_data, signature):
            logger.warning("Invalid Twilio signature — rejecting request.")
            return PlainTextResponse("Forbidden", status_code=status.HTTP_403_FORBIDDEN)

    # --- 3. Parse --------------------------------------------------------
    parsed = parse_twilio_webhook(form_data)
    message_sid = parsed["message_sid"]
    customer_phone = parsed["from_phone"]
    message_text = parsed["body"]

    logger.info(
        "Webhook received — SID=%s, from=%s, body=%s",
        message_sid, customer_phone, message_text[:60],
    )

    # --- 4. Duplicate guard ----------------------------------------------
    if message_sid in _processed_sids:
        logger.info("Duplicate SID %s — ignoring", message_sid)
        return Response(content="<Response></Response>", media_type="application/xml")
    _processed_sids.add(message_sid)

    if len(_processed_sids) > 10_000:
        excess = len(_processed_sids) - 10_000
        for _ in range(excess):
            _processed_sids.pop()

    # --- 5. Basic validation ---------------------------------------------
    if not validate_phone_number(customer_phone):
        logger.warning("Invalid phone number received: %s", customer_phone)
        return Response(content="<Response></Response>", media_type="application/xml")

    business_id = "BIZ001"



    # --- 7. Final text validation ----------------------------------------
    if not validate_message_text(message_text):
        logger.warning("Empty or invalid message from %s", customer_phone)
        return Response(content="<Response></Response>", media_type="application/xml")

    message_text = sanitize_input(message_text)

    # --- 8. Ensure user/chat exists in MongoDB ---------------------------
    try:
        await _get_or_create_chat(customer_phone, business_id)
    except Exception as exc:
        logger.error("MongoDB chat lookup failed: %s", exc)

    # --- 9. Store incoming user message ----------------------------------
    try:
        await _store_message(
            customer_phone=customer_phone,
            business_id=business_id,
            role="user",
            content=message_text,
            message_sid=message_sid,
        )
    except Exception as exc:
        logger.error("Failed to persist user message: %s", exc)

    # --- 10. Enqueue background processing -------------------------------
    background_tasks.add_task(
        _process_message_background,
        customer_phone=customer_phone,
        business_id=business_id,
        message_text=message_text,
        message_sid=message_sid,
    )

    # --- 11. Respond immediately to Twilio -------------------------------
    return Response(content="<Response></Response>", media_type="application/xml")
