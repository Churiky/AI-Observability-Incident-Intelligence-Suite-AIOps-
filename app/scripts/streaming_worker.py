"""
Streaming analytics worker that consumes logs from Redis,
performs anomaly detection, and publishes results.
"""
print("WORKER SCRIPT STARTING", flush=True)
import os
print("PYTHONPATH from env:", os.environ.get('PYTHONPATH'), flush=True)
import asyncio
import json
import logging
import redis.asyncio as redis
from typing import List
from app.core.config import settings
from app.services.log_parser import LogParserService
from app.services.anomaly_detector import AnomalyDetector
from app.models.schemas import LogCreate
from app.models.database import Log
from app.core.database import SessionLocal, get_db
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamingWorker:
    def __init__(self):
        self.redis_client = None
        self.log_parser = LogParserService()
        self.anomaly_detector = AnomalyDetector()
        self.running = False

    async def initialize(self):
        """Initialize Redis connection."""
        self.redis_client = redis.from_url(settings.REDIS_URL)
        logger.info("Streaming worker initialized")

    async def start(self):
        """Start the streaming worker."""
        await self.initialize()
        self.running = True
        logger.info("Starting streaming worker...")

        # Main processing loop
        while self.running:
            try:
                # Get log from Redis stream (blocking read with timeout)
                result = await self.redis_client.brpop(
                    ["log-stream"],
                    timeout=1
                )

                if result:
                    channel, log_data = result
                    log_json = json.loads(log_data)

                    # Process the log
                    await self.process_log(log_json)

            except Exception as e:
                logger.error(f"Error in streaming worker: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on error

        logger.info("Streaming worker stopped")

    async def stop(self):
        """Stop the streaming worker."""
        self.running = False
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Streaming worker stopping...")

    async def process_log(self, log_data: dict):
        """
        Process a single log entry:
        1. Parse and normalize
        2. Detect anomalies
        3. Persist anomalies to database
        4. Publish anomalies to Redis for WebSocket notification
        """
        try:
            # Convert to LogCreate schema
            log_create = LogCreate(**log_data)

            # Parse and normalize
            parsed_logs = await self.log_parser.parse_logs([log_create])
            if not parsed_logs:
                return

            log = parsed_logs[0]

            # Detect anomaly
            anomaly_score, is_anomaly = self.anomaly_detector.detect_anomaly(log)

            # Update log with anomaly info
            log.anomaly_score = anomaly_score
            log.is_anomaly = is_anomaly

            # Persist if it's an anomaly (to prevent database bloat)
            if is_anomaly:
                await self._persist_anomaly(log)
                # Publish to anomaly-alerts channel for WebSocket clients
                await self._publish_anomaly_alert(log)
            else:
                # For normal logs, we might still want to publish metrics
                # but we don't persist them to prevent bloat
                pass

        except Exception as e:
            logger.error(f"Error processing log: {e}")

    async def _persist_anomaly(self, log: LogCreate):
        """Persist anomaly to database."""
        try:
            # Get database session
            db = SessionLocal()
            try:
                # Ensure service exists
                from app.models.database import Service
                service = db.query(Service).filter(Service.name == log.service).first()
                if not service:
                    service = Service(name=log.service, environment=log.environment or "production")
                    db.add(service)
                    db.commit()
                    db.refresh(service)

                # Create anomaly log entry
                from app.models.database import Log as DBLog
                db_log = DBLog(
                    service_id=service.id,
                    timestamp=log.timestamp,
                    message=log.message,
                    level=log.level.value if hasattr(log.level, 'value') else str(log.level),
                    host=log.host,
                    request_id=log.request_id,
                    status_code=log.status_code,
                    latency_ms=log.latency_ms,
                    endpoint=log.endpoint,
                    exception_type=log.exception_type,
                    environment=log.environment,
                    anomaly_score=log.anomaly_score,
                    is_anomaly=log.is_anomaly
                )
                db.add(db_log)
                db.commit()
                logger.info(f"Persisted anomaly: {log.message} (score: {log.anomaly_score})")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error persisting anomaly: {e}")

    async def _publish_anomaly_alert(self, log: LogCreate):
        """Publish anomaly alert to Redis for WebSocket clients."""
        try
            alert_data = {
                "type": "anomaly",
                "data": {
                    "id": None,  # Will be set after persistence
                    "service": log.service,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    "message": log.message,
                    "level": log.level.value if hasattr(log.level, 'value') else str(log.level),
                    "anomaly_score": log.anomaly_score,
                    "host": log.host
                }
            }
            await self.redis_client.publish("anomaly-alerts", json.dumps(alert_data))
            logger.debug(f"Published anomaly alert for service {log.service}")
        except Exception as e:
            logger.error(f"Error publishing anomaly alert: {e}")


# Entry point for running the worker
if __name__ == "__main__":
    worker = StreamingWorker()
    try:
        asyncio.run(worker.start())
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        asyncio.run(worker.stop())