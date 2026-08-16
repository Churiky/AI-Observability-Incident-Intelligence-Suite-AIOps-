"""
WebSocket connection manager.
"""
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.channel_subscriptions: dict[WebSocket, list[str]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.channel_subscriptions[websocket] = []
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.channel_subscriptions:
            del self.channel_subscriptions[websocket]
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str, channel: str = None):
        disconnected = []
        for connection in self.active_connections:
            try:
                # If channel is specified, only send to subscribers of that channel
                if channel:
                    if connection in self.channel_subscriptions and channel in self.channel_subscriptions[connection]:
                        await connection.send_text(message)
                else:
                    # Send to all connections
                    await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

    def subscribe_to_channel(self, websocket: WebSocket, channel: str):
        if websocket in self.channel_subscriptions:
            if channel not in self.channel_subscriptions[websocket]:
                self.channel_subscriptions[websocket].append(channel)
                logger.info(f"WebSocket subscribed to channel: {channel}")

    def unsubscribe_from_channel(self, websocket: WebSocket, channel: str):
        if websocket in self.channel_subscriptions:
            if channel in self.channel_subscriptions[websocket]:
                self.channel_subscriptions[websocket].remove(channel)
                logger.info(f"WebSocket unsubscribed from channel: {channel}")


manager = ConnectionManager()
