"""
Metrics endpoints.
"""
from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime
from app.api.v1.endpoints.incidents import MOCK_INCIDENTS

router = APIRouter()

@router.get("/summary", response_model=Dict[str, Any])
async def get_metrics_summary():
    """
    Get summary metrics for the dashboard.
    """
    # Dynamically compute metrics from current incident state
    active_incidents_count = len([inc for inc in MOCK_INCIDENTS if inc["status"] == "ACTIVE"])
    
    # Determine system health status based on number of active incidents
    if active_incidents_count == 0:
        system_health = "EXCELLENT"
    elif active_incidents_count == 1:
        system_health = "GOOD"
    elif active_incidents_count == 2:
        system_health = "FAIR"
    else:
        system_health = "POOR"

    # Static realistic shape for daily anomalies trend
    hourly_anomalies = [12, 15, 18, 14, 10, 8, 5, 4, 6, 8, 12, 15, 20, 22, 18, 15, 12, 10, 14, 16, 18, 15, 11, 9]

    # Incident trend over last 7 days, dynamic for today (index 6)
    incident_trend = [2, 1, 0, 3, 1, 2, active_incidents_count]

    return {
        "total_services": 4,
        "active_incidents": active_incidents_count,
        "anomalies_today": 124 + active_incidents_count * 15,  # scale anomalies slightly
        "avg_mttr": "3.5h" if active_incidents_count == 0 else "4.2h",
        "system_health": system_health,
        "last_updated": datetime.now().isoformat(),
        "hourly_anomalies": hourly_anomalies,
        "incident_trend": incident_trend,
        "service_health": {
            "service-a": "HEALTHY",
            "service-b": "DEGRADED" if active_incidents_count > 0 else "HEALTHY",
            "service-c": "HEALTHY",
            "service-d": "HEALTHY"
        }
    }