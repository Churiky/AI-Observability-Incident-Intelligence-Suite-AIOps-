"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.core.websocket import manager
from contextlib import asynccontextmanager
import asyncio
import json
import logging
import redis.asyncio as redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def redis_pubsub_listener():
    """
    Background task to listen to Redis Pub/Sub channels and broadcast to WebSocket clients.
    """
    logger.info("Starting Redis Pub/Sub listener background task...")
    while True:
        try:
            redis_client = redis.from_url(settings.REDIS_URL)
            pubsub = redis_client.pubsub()
            await pubsub.subscribe("anomaly-alerts", "incident-updates")
            logger.info("Subscribed to Redis channels: anomaly-alerts, incident-updates")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"].decode("utf-8") if isinstance(message["channel"], bytes) else message["channel"]
                    data = message["data"].decode("utf-8") if isinstance(message["data"], bytes) else message["data"]
                    logger.info(f"Received message from Redis channel {channel}: {data}")
                    await manager.broadcast(data, channel)
        except asyncio.CancelledError:
            logger.info("Redis Pub/Sub listener task was cancelled")
            break
        except Exception as e:
            logger.error(f"Error in Redis Pub/Sub listener: {e}")
            await asyncio.sleep(5)  # Wait before reconnecting


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start Redis Pub/Sub listener
    listener_task = asyncio.create_task(redis_pubsub_listener())
    yield
    # Shutdown: Cancel task
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="AI Observability & Incident Intelligence Platform",
    description="A platform for ingesting logs, detecting anomalies, and generating incident reports",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "AI Observability & Incident Intelligence Platform"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                # Parse incoming message
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "subscribe":
                    channels = message.get("channels", [])
                    for channel in channels:
                        manager.subscribe_to_channel(websocket, channel)
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "channels": channels
                    }))
                elif message_type == "unsubscribe":
                    channels = message.get("channels", [])
                    for channel in channels:
                        manager.unsubscribe_from_channel(websocket, channel)
                    await websocket.send_text(json.dumps({
                        "type": "unsubscribed",
                        "channels": channels
                    }))
                else:
                    # Echo back unknown message types
                    await websocket.send_text(json.dumps({
                        "type": "echo",
                        "original_message": message
                    }))

            except json.JSONDecodeError:
                # Handle plain text messages
                await websocket.send_text(json.dumps({
                    "type": "echo",
                    "message": data
                }))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)