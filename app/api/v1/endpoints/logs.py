"""
Log ingestion endpoints.
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
from app.models.schemas import LogCreate, LogResponse
from app.services.log_parser import LogParserService
from app.repositories.log_repository import LogRepository
from app.core.database import get_db, SessionLocal
from app.core.config import settings
import redis.asyncio as redis

logger = logging.getLogger(__name__)

print("LOGS MODULE LOADED", flush=True)

router = APIRouter()


async def get_redis_client():
    """
    Dependency to get Redis client.
    """
    client = redis.from_url(settings.REDIS_URL)
    try:
        yield client
    finally:
        await client.close()


@router.post("/ingest", response_model=List[LogCreate])
async def ingest_logs(
    logs: List[LogCreate],
    background_tasks: BackgroundTasks,
    log_parser: LogParserService = Depends(),
    db: SessionLocal = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    """
    Ingest logs and publish them to Redis for streaming analysis.
    Normal logs are discarded; only anomalies are persisted.
    """
    log_repo = LogRepository(db)
    print("INGEST CALLED", flush=True)
    try:
        # Parse and normalize logs
        parsed_logs = await log_parser.parse_logs(logs)

        # Publish to Redis for streaming analysis (handled by background worker)
        for log in parsed_logs:
            # Convert log to JSON and push to Redis list
            log_json = log.json()
            await redis_client.rpush("log-stream", log_json)

        logger.info(f"Published {len(parsed_logs)} logs to Redis stream")

        # Store any anomalies or incidents that were detected during parsing
        # This would be handled by the streaming analytics worker

        return parsed_logs

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[LogResponse])
async def get_logs(
    skip: int = 0,
    limit: int = 100,
    db: SessionLocal = Depends(get_db)
):
    """
    Retrieve stored logs (anomalies and incidents only).
    """
    log_repo = LogRepository(db)
    logs = await log_repo.get_logs(skip=skip, limit=limit)
    return logs