"""
Razorpay Webhook Endpoint.

Receives payment events from Razorpay, verifies signatures,
and dispatches to the advanced Razorpay service for auto-confirm/cancel.
"""

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse

from app.integrations.razorpay_advanced import razorpay_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/razorpay", response_class=Response)
async def razorpay_webhook(request: Request):
    """
    Handle incoming Razorpay webhook events.
    
    Supported events:
      - payment.captured → auto-confirm order
      - payment_link.expired → auto-cancel order
      - refund.processed → mark refund complete
    """
    try:
        body = await request.body()
        signature = request.headers.get("X-Razorpay-Signature", "")

        # Verify signature
        if not razorpay_service.verify_webhook_signature(body, signature):
            logger.warning("Razorpay webhook: invalid signature")
            return Response(status_code=status.HTTP_403_FORBIDDEN)

        # Parse event
        import json
        event = json.loads(body)
        event_type = event.get("event", "unknown")

        logger.info("Razorpay webhook received: %s", event_type)

        # Dispatch to handler
        result = await razorpay_service.handle_webhook_event(event)

        return JSONResponse(content=result, status_code=200)

    except Exception as exc:
        logger.error("Razorpay webhook processing failed: %s", exc)
        return JSONResponse(
            content={"error": "processing_failed"},
            status_code=500,
        )
