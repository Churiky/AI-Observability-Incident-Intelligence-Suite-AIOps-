"""
Log parsing and normalization service.
"""
import re
from typing import List, Optional
from datetime import datetime
from app.models.schemas import LogCreate, LogLevel
from app.core.config import settings


class LogParserService:
    def __init__(self):
        # Compile regex patterns for common log formats
        self.json_pattern = re.compile(r'^\s*\{.*\}\s*$', re.DOTALL)

    async def parse_logs(self, logs: List[LogCreate]) -> List[LogCreate]:
        """
        Parse and normalize incoming logs.
        In a full implementation, this would detect format, extract fields, and normalize.
        """
        parsed_logs = []

        for log in logs:
            # Basic normalization - in reality, this would be much more sophisticated
            normalized_log = await self._normalize_log(log)
            parsed_logs.append(normalized_log)

        return parsed_logs

    async def _normalize_log(self, log: LogCreate) -> LogCreate:
        """
        Normalize a single log entry.
        This includes:
        - Validating input
        - Normalizing timestamps
        - Normalizing severity levels
        - Extracting service name
        - Extracting request ID where available
        - Extracting HTTP status code where available
        - Extracting latency where available
        """
        # For now, we'll just return the log as-is since it's already in our schema
        # In a full implementation, we would:
        # 1. Detect if it's JSON, plain text, etc.
        # 2. Extract fields based on format
        # 3. Normalize timestamp to datetime object
        # 4. Normalize level to our LogLevel enum
        # 5. Extract service, host, etc.

        # Ensure timestamp is a datetime object (it should be from Pydantic validation)
        if isinstance(log.timestamp, str):
            try:
                log.timestamp = datetime.fromisoformat(log.timestamp.replace('Z', '+00:00'))
            except ValueError:
                # Handle other formats or use current time as fallback
                log.timestamp = datetime.utcnow()

        # Normalize level to uppercase
        if log.level:
            log.level = LogLevel(log.level.upper())

        return log