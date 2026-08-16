"""
Log repository for database operations.
"""
from typing import List, Optional
from app.models.database import Log
from app.core.database import SessionLocal
from app.models.schemas import LogCreate, LogResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc


class LogRepository:
    def __init__(self, db: Session):
        self.db = db

    async def get_logs(self, skip: int = 0, limit: int = 100) -> List[LogResponse]:
        """
        Retrieve logs from database with pagination.
        """
        logs = self.db.query(Log).order_by(desc(Log.timestamp)).offset(skip).limit(limit).all()
        return [LogResponse.from_orm(log) for log in logs]

    async def create_log(self, log: LogCreate) -> LogResponse:
        """
        Create a new log entry in the database.
        """
        db_log = Log(**log.dict())
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        return LogResponse.from_orm(db_log)

    async def create_logs(self, logs: List[LogCreate]) -> List[LogResponse]:
        """
        Create multiple log entries.
        """
        db_logs = [Log(**log.dict()) for log in logs]
        self.db.add_all(db_logs)
        self.db.commit()
        for log in db_logs:
            self.db.refresh(log)
        return [LogResponse.from_orm(log) for log in db_logs]