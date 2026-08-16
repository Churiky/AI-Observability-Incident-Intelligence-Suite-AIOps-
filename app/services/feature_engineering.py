"""
Feature engineering service for creating ML features from logs and metrics.
"""
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.models.database import *
from app.models.schemas import *
import logging

logger = logging.getLogger(__name__)


class FeatureEngineeringService:
    def __init__(self, db_session):
        self.db = db_session

    def extract_log_features(self, logs: List[LogCreate], time_window_minutes: int = 60) -> Dict[str, float]:
        """
        Extract ML features from logs.
        Features include:
        - Error count
        - Warning count
        - Error rate
        - Unique exception count
        - Message frequency
        - Message entropy
        - Service error ratio
        - Request failure ratio
        - Average latency
        - P95 latency
        - P99 latency
        """
        if not logs:
            return self._get_empty_log_features()

        # Filter logs within time window
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        recent_logs = [log for log in logs if log.timestamp >= cutoff_time]

        if not recent_logs:
            recent_logs = logs  # Fallback to all logs

        # Basic counts
        total_logs = len(recent_logs)
        error_logs = [log for log in recent_logs
                      if log.level.value if hasattr(log.level, 'value') else str(log.level) == "ERROR"]
        warning_logs = [log for log in recent_logs
                        if log.level.value if hasattr(log.level, 'value') else str(log.level) == "WARNING"]
        critical_logs = [log for log in recent_logs
                         if log.level.value if hasattr(log.level, 'value') else str(log.level) == "CRITICAL"]

        # Error rate
        error_rate = len(error_logs) / total_logs if total_logs > 0 else 0.0

        # Unique exception count
        exceptions = [log.exception_type for log in recent_logs
                      if log.exception_type is not None]
        unique_exceptions = len(set(exceptions))

        # Request failure ratio (non-2xx status codes)
        failed_requests = [log for log in recent_logs
                           if log.status_code is not None and not (200 <= log.status_code < 300)]
        request_failure_ratio = len(failed_requests) / total_logs if total_logs > 0 else 0.0

        # Latency features
        latencies = [log.latency_ms for log in recent_logs if log.latency_ms is not None]
        avg_latency = np.mean(latencies) if latencies else 0.0
        p95_latency = np.percentile(latencies, 95) if latencies else 0.0
        p99_latency = np.percentile(latencies, 99) if latencies else 0.0

        # Message frequency and entropy (simplified)
        messages = [log.message for log in recent_logs]
        unique_messages = len(set(messages))
        message_frequency = total_logs / len(set(messages)) if unique_messages > 0 else 0.0

        # Simplified entropy calculation
        message_entropy = self._calculate_entropy(messages) if messages else 0.0

        # Service error ratio (errors per service)
        service_errors = {}
        service_totals = {}
        for log in recent_logs:
            service_name = log.service or "unknown"
            service_totals[service_name] = service_totals.get(service_name, 0) + 1
            if log.level.value if hasattr(log.level, 'value') else str(log.level) == "ERROR":
                service_errors[service_name] = service_errors.get(service_name, 0) + 1

        service_error_ratios = []
        for service in service_totals:
            error_count = service_errors.get(service, 0)
            total_count = service_totals[service]
            ratio = error_count / total_count if total_count > 0 else 0.0
            service_error_ratios.append(ratio)

        avg_service_error_ratio = np.mean(service_error_ratios) if service_error_ratios else 0.0

        return {
            "error_count": len(error_logs),
            "warning_count": len(warning_logs),
            "error_rate": error_rate,
            "unique_exception_count": unique_exceptions,
            "message_frequency": message_frequency,
            "message_entropy": message_entropy,
            "service_error_ratio": avg_service_error_ratio,
            "request_failure_ratio": request_failure_ratio,
            "average_latency": avg_latency,
            "p95_latency": p95_latency,
            "p99_latency": p99_latency,
            "critical_count": len(critical_logs)
        }

    def extract_time_series_features(self, values: List[float], timestamps: List[datetime] = None) -> Dict[str, float]:
        """
        Extract time-series features from a sequence of values.
        Features include:
        - Rolling mean
        - Rolling standard deviation
        - Rate of change
        - Moving average
        - Difference from baseline
        - Z-score
        - Seasonal deviation
        """
        if not values or len(values) < 2:
            return self._get_empty_time_series_features()

        values_array = np.array(values)

        # Basic statistics
        mean_val = np.mean(values_array)
        std_val = np.std(values_array)

        # Rolling statistics (using last 10 values or all if less)
        window_size = min(10, len(values_array))
        if len(values_array) >= window_size:
            recent_values = values_array[-window_size:]
            rolling_mean = np.mean(recent_values)
            rolling_std = np.std(recent_values)
        else:
            rolling_mean = mean_val
            rolling_std = std_val

        # Rate of change (difference between last and first)
        if len(values_array) >= 2:
            rate_of_change = (values_array[-1] - values_array[0]) / len(values_array)
        else:
            rate_of_change = 0.0

        # Z-score of last value
        if std_val > 0:
            z_score = (values_array[-1] - mean_val) / std_val
        else:
            z_score = 0.0

        # Difference from baseline (using first value as baseline)
        if len(values_array) >= 1:
            baseline = values_array[0]
            diff_from_baseline = values_array[-1] - baseline
        else:
            diff_from_baseline = 0.0

        # Simple seasonal deviation (deviation from median)
        median_val = np.median(values_array)
        seasonal_deviation = np.abs(values_array[-1] - median_val) if len(values_array) >= 1 else 0.0

        return {
            "rolling_mean": rolling_mean,
            "rolling_std": rolling_std,
            "rate_of_change": rate_of_change,
            "z_score": z_score,
            "difference_from_baseline": diff_from_baseline,
            "seasonal_deviation": seasonal_deviation,
            "mean": mean_val,
            "std": std_val,
            "median": median_val
        }

    def _calculate_entropy(self, messages: List[str]) -> float:
        """Calculate Shannon entropy of messages."""
        if not messages:
            return 0.0

        # Count frequency of each message
        freq_dict = {}
        for message in messages:
            freq_dict[message] = freq_dict.get(message, 0) + 1

        # Calculate probabilities
        total_messages = len(messages)
        entropy = 0.0
        for count in freq_dict.values():
            if count > 0:
                p = count / total_messages
                entropy -= p * np.log2(p)

        return entropy

    def _get_empty_log_features(self) -> Dict[str, float]:
        """Return empty log features dict."""
        return {
            "error_count": 0,
            "warning_count": 0,
            "error_rate": 0.0,
            "unique_exception_count": 0,
            "message_frequency": 0.0,
            "message_entropy": 0.0,
            "service_error_ratio": 0.0,
            "request_failure_ratio": 0.0,
            "average_latency": 0.0,
            "p95_latency": 0.0,
            "p99_latency": 0.0,
            "critical_count": 0
        }

    def _get_empty_time_series_features(self) -> Dict[str, float]:
        """Return empty time-series features dict."""
        return {
            "rolling_mean": 0.0,
            "rolling_std": 0.0,
            "rate_of_change": 0.0,
            "z_score": 0.0,
            "difference_from_baseline": 0.0,
            "seasonal_deviation": 0.0,
            "mean": 0.0,
            "std": 0.0,
            "median": 0.0
        }