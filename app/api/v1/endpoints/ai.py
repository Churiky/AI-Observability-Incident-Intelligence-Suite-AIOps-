"""
AI endpoints for report generation and RAG.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from app.models.schemas import AIInvestigationRequest, AIInvestigationResponse

router = APIRouter()

# Mock data for demonstration - aligned with AIInvestigationResponse schema
MOCK_AI_REPORTS = [
    {
        "incident_id": 1,
        "summary": "Database connection pool exhaustion led to timeout errors.",
        "impact": "Service degradation affecting 40% of user requests.",
        "probable_cause": "Misconfigured connection pool size in recent deployment.",
        "recommended_investigation": [
            "Review database connection pool configuration",
            "Check recent deployment changes to service-a",
            "Monitor connection usage metrics for next 24h"
        ],
        "confidence": "Confirmed"
    }
]

@router.post("/investigate", response_model=AIInvestigationResponse)
async def investigate_incident(request: AIInvestigationRequest):
    """
    Generate an AI-powered investigation report for an incident.
    """
    # In a real implementation, this would use RAG + LLM
    report = {
        "incident_id": request.incident_id,
        "summary": f"Automated analysis of incident {request.incident_id} suggests potential issues in service dependencies.",
        "impact": "Moderate service impact detected based on error rates and latency metrics.",
        "probable_cause": "Requires detailed investigation - initial analysis points to resource exhaustion.",
        "recommended_investigation": [
            "Collect detailed logs from affected services",
            "Review recent deployments and configuration changes",
            "Analyze dependency call patterns and error flows"
        ],
        "confidence": "Probable"
    }
    MOCK_AI_REPORTS.append(report)
    return report

@router.get("/reports/{report_id}", response_model=AIInvestigationResponse)
async def get_ai_report(report_id: int):
    """
    Retrieve a specific AI investigation report.
    Note: Since we don't store report IDs separately in mock data,
    we'll return the first match for incident_id or a default report.
    """
    # For simplicity in mock, we'll return the first report or create one based on report_id as incident_id
    if 1 <= report_id <= len(MOCK_AI_REPORTS):
        return MOCK_AI_REPORTS[report_id - 1]
    else:
        # Generate a mock report on the fly
        return {
            "incident_id": report_id,
            "summary": f"Investigation report for incident {report_id}",
            "impact": "Impact assessment pending detailed analysis.",
            "probable_cause": "Root cause under investigation.",
            "recommended_investigation": [
                "Collect forensic data from time of incident",
                "Analyze service logs and metrics",
                "Review recent changes in related services"
            ],
            "confidence": "Unknown"
        }

@router.get("/reports/", response_model=List[AIInvestigationResponse])
async def get_ai_reports(
    incident_id: Optional[int] = Query(None),
    limit: int = 100
):
    """
    Retrieve AI investigation reports with optional filtering.
    """
    filtered = MOCK_AI_REPORTS
    if incident_id:
        filtered = [rep for rep in filtered if rep["incident_id"] == incident_id]
    return filtered[:limit]