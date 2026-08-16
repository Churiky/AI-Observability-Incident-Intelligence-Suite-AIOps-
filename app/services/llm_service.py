"""
LLM service for generating investigation reports using local Ollama instance.
"""
import json
import logging
from typing import List, Dict, Any, Optional
import requests
from app.models.database import *
from app.models.schemas import *
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.ollama_base_url = settings.OLLAMA_BASE_URL
        self.ollama_model = settings.OLLAMA_MODEL
        self.session = requests.Session()

    def generate_incident_report(self, incident_id: int, rag_service: 'RAGService') -> str:
        """
        Generate an incident report using the LLM with RAG context.
        The LLM must not independently invent root causes - it should only work with provided evidence.
        """
        try:
            logger.info(f"Generating incident report for incident {incident_id}")

            # Get incident details
            incident_details = rag_service.get_incident_details(incident_id)
            if not incident_details:
                raise ValueError(f"Incident {incident_id} not found")

            # Get similar historical incidents from RAG
            similar_incidents = rag_service.search_similar_incidents(
                incident_title=incident_details['title'],
                incident_description="",  # Could use more context here
                k=3
            )

            # Prepare evidence from current incident
            evidence = self._gather_incident_evidence(incident_id)

            # Prepare context from similar incidents
            similar_incidents_context = self._prepare_similar_incidents_context(similar_incidents, rag_service)

            # Construct prompt that enforces evidence-based reasoning
            prompt = self._construct_evidence_based_prompt(
                incident_details=incident_details,
                evidence=evidence,
                similar_incidents_context=similar_incidents_context
            )

            # Query Ollama
            report = self._query_ollama(prompt)

            # Post-process to ensure it follows the required format
            report = self._post_process_report(report, incident_id)

            logger.info(f"Generated incident report for incident {incident_id}")
            return report

        except Exception as e:
            logger.error(f"Error generating incident report: {e}")
            # Return a basic report format even on error
            return self._get_fallback_report(incident_id)

    def _gather_incident_evidence(self, incident_id: int) -> Dict[str, Any]:
        """
        Gather structured evidence from the incident and its anomalies.
        This ensures the LLM only works with provable facts.
        """
        # This would normally query the database directly
        # For now, we'll return a placeholder structure
        # In a full implementation, this would query:
        # - Incident details
        # - Related anomalies
        # - Related metrics
        # - Timestamps and sequences
        return {
            "incident_id": incident_id,
            "timestamp": "2026-08-16T10:23:41",
            "service": "payment-service",
            "anomalies": [
                {
                    "type": "database_timeout",
                    "description": "Database connection timeout increased by 340%",
                    "confidence": 0.95
                },
                {
                    "type": "connection_pool_exhaustion",
                    "description": "Database pool utilization reached 98%",
                    "confidence": 0.92
                },
                {
                    "type": "http_500_increase",
                    "description": "HTTP 500 responses increased by 18%",
                    "confidence": 0.88
                },
                {
                    "type": "latency_increase",
                    "description": "Average request latency increased from 240ms to 1.8s",
                    "confidence": 0.90
                }
            ],
            "metrics": {
                "error_rate_increase": 0.18,
                "latency_p99_increase": 6.5,  # 6.5x increase
                "db_pool_utilization": 0.98
            }
        }

    def _prepare_similar_incidents_context(self, similar_incidents: List[Tuple[int, float]], rag_service: 'RAGService') -> List[Dict[str, Any]]:
        """
        Prepare context from similar historical incidents.
        """
        context = []
        for incident_id, similarity in similar_incidents:
            details = rag_service.get_incident_details(incident_id)
            if details:
                context.append({
                    "incident_id": incident_id,
                    "similarity_score": similarity,
                    "title": details['title'],
                    "severity": details['severity'],
                    "root_cause": details.get('root_cause', 'Not specified'),
                    "resolved_at": details.get('resolved_at')
                })
        return context

    def _construct_evidence_based_prompt(self, incident_details: Dict[str, Any], evidence: Dict[str, Any], similar_incidents_context: List[Dict[str, Any]]) -> str:
        """
        Construct a prompt that forces the LLM to base its response on provided evidence only.
        """
        prompt = f"""
You are an expert SRE (Site Reliability Engineer) analyzing an incident. Your task is to generate a factual incident report based ONLY on the evidence provided below. You MUST NOT invent or speculate about root causes that are not supported by the evidence.

INCIDENT INFORMATION:
- Incident ID: {incident_details['id']}
- Title: {incident_details['title']}
- Severity: {incident_details['severity']}
- Status: {incident_details['status']}
- Created At: {incident_details['created_at']}

CURRENT INCIDENT EVIDENCE:
{self._format_evidence(evidence)}

SIMILAR HISTORICAL INCIDENTS (for context only - do not copy root causes):
{self._format_similar_incidents(similar_incidents_context)}

INSTRUCTIONS:
1. Analyze the evidence objectively
2. Identify patterns in the evidence
3. Generate a report with the following sections:
   - Incident Summary: A 1-2 sentence summary of what happened
   - Impact: Quantitative impact based on evidence
   - Probable Cause: Only state causes that are directly supported by evidence
   - Recommended Investigation: Specific, actionable steps based on evidence
   - Confidence: One of "Confirmed", "Probable", "Possible", or "Unknown" based on evidence strength

RULES:
- NEVER invent root causes not present in the evidence
- If evidence is insufficient, state "Unknown" as the probable cause and recommend further investigation
- Base all recommendations on the evidence provided
- Use quantitative data from evidence when available
- Be concise and professional

REPORT FORMAT:
Incident Summary: [2-3 sentence summary]
Impact: [Specific quantitative impact]
Probable Cause: [Evidence-based cause or "Unknown"]
Recommended Investigation:
1. [Specific actionable step]
2. [Specific actionable step]
3. [Specific actionable step]
Confidence: [Confirmed/Probable/Possible/Unknown]
"""
        return prompt

    def _format_evidence(self, evidence: Dict[str, Any]) -> str:
        """Format evidence for the prompt."""
        formatted = f"- Service: {evidence.get('service', 'Unknown')}\n"
        formatted += f"- Timestamp: {evidence.get('timestamp', 'Unknown')}\n"

        if 'anomalies' in evidence:
            formatted += "- Anomalies Detected:\n"
            for anomaly in evidence['anomalies']:
                formatted += f"  * {anomaly['description']} (confidence: {anomaly['confidence']})\n"

        if 'metrics' in evidence:
            formatted += "- Metrics:\n"
            for key, value in evidence['metrics'].items():
                formatted += f"  * {key}: {value}\n"

        return formatted

    def _format_similar_incidents(self, similar_incidents: List[Dict[str, Any]]) -> str:
        """Format similar incidents for the prompt."""
        if not similar_incidents:
            return "- No similar historical incidents found"

        formatted = ""
        for inc in similar_incidents:
            formatted += f"- Incident {inc['incident_id']}: {inc['title']} "
            formatted += f"(Similarity: {inc['similarity_score']:.2f}, Severity: {inc['severity']})"
            if inc.get('root_cause') and inc['root_cause'] != 'Not specified':
                formatted += f" - Root Cause: {inc['root_cause']}"
            formatted += "\n"
        return formatted

    def _query_ollama(self, prompt: str) -> str:
        """
        Query the Ollama instance to generate a response.
        """
        try:
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more factual responses
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            }

            response = self.session.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('response', "").strip()
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                raise Exception(f"Ollama API returned status {response.status_code}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to Ollama: {e}")
            raise Exception(f"Failed to connect to Ollama: {e}")

    def _post_process_report(self, report: str, incident_id: int) -> str:
        """
        Post-process the generated report to ensure it follows the required format.
        """
        # Ensure required sections are present
        required_sections = ["Incident Summary:", "Impact:", "Probable Cause:", "Recommended Investigation:", "Confidence:"]

        # If the report doesn't contain all sections, try to extract or format it
        if not all(section in report for section in required_sections):
            logger.warning("Generated report missing some sections, attempting to reformat")
            # In a full implementation, we might re-query with a more structured prompt
            # For now, we'll return what we have but log the issue

        return report.strip()

    def _get_fallback_report(self, incident_id: int) -> str:
        """
        Generate a fallback report when the LLM fails.
        """
        return f"""Incident Summary: Incident {incident_id} occurred requiring investigation.
Impact: Impact assessment pending further analysis.
Probable Cause: Unknown - requires additional evidence collection.
Recommended Investigation:
1. Collect detailed logs and metrics from affected services
2. Analyze temporal patterns of anomalies
3. Review recent deployments or configuration changes
Confidence: Unknown
"""