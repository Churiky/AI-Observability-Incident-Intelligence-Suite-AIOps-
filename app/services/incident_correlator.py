"""
Incident correlation service that groups related anomalies into incidents.
"""
import numpy as np
from typing import List, Tuple, Optional
from sklearn.cluster import DBSCAN
from datetime import datetime, timedelta
from app.models.database import *
from app.models.schemas import *
from app.services.embedding_service import EmbeddingService
import logging

logger = logging.getLogger(__name__)


class IncidentCorrelator:
    def __init__(self, db_session):
        self.db = db_session
        self.embedding_service = EmbeddingService()

    def cluster_anomalies(self, anomaly_ids: List[int]) -> List[Incident]:
        """
        Group temporal and semantically related anomalies into incidents.
        Uses temporal windowing, service correlation, and semantic similarity.
        """
        # Get anomalies from database
        anomalies = self.db.query(Anomaly).filter(Anomaly.id.in_(anomaly_ids)).all()

        if not anomalies:
            return []

        logger.info(f"Clustering {len(anomalies)} anomalies")

        # Step 1: Temporal windowing - group anomalies within time windows
        temporal_groups = self._group_by_temporal_window(anomalies, window_minutes=5)

        # Step 2: For each temporal group, check service correlation and semantic similarity
        incidents = []
        for group in temporal_groups:
            if len(group) == 1:
                # Single anomaly - create incident if significant
                incident = self._create_incident_from_anomaly(group[0])
                if incident:
                    incidents.append(incident)
            else:
                # Multiple anomalies - check if they're related
                related_groups = self._group_by_service_and_semantic(group)
                for subgroup in related_groups:
                    if len(subgroup) >= 2 or self._is_significant_anomaly(subgroup[0]):
                        incident = self._create_incident_from_anomalies(subgroup)
                        if incident:
                            incidents.append(incident)

        logger.info(f"Created {len(incidents)} incidents from {len(anomalies)} anomalies")
        return incidents

    def _group_by_temporal_window(self, anomalies: List[Anomaly], window_minutes: int = 5) -> List[List[Anomaly]]:
        """Group anomalies by temporal proximity."""
        if not anomalies:
            return []

        # Sort by timestamp
        sorted_anomalies = sorted(anomalies, key=lambda x: x.timestamp)

        groups = []
        current_group = [sorted_anomalies[0]]
        window_delta = timedelta(minutes=window_minutes)

        for i in range(1, len(sorted_anomalies)):
            prev_time = sorted_anomalies[i-1].timestamp
            curr_time = sorted_anomalies[i].timestamp

            if curr_time - prev_time <= window_delta:
                # Same temporal window
                current_group.append(sorted_anomalies[i])
            else:
                # New temporal window
                groups.append(current_group)
                current_group = [sorted_anomalies[i]]

        # Add the last group
        if current_group:
            groups.append(current_group)

        return groups

    def _group_by_service_and_semantic(self, anomalies: List[Anomaly]) -> List[List[Anomaly]]:
        """Group anomalies by service relationship and semantic similarity."""
        if len(anomalies) <= 1:
            return [anomalies]

        # Group by service first
        service_groups = {}
        for anomaly in anomalies:
            service_name = anomaly.service.name if anomaly.service else "unknown"
            if service_name not in service_groups:
                service_groups[service_name] = []
            service_groups[service_name].append(anomaly)

        # For each service group, check semantic similarity
        final_groups = []
        for service_name, group in service_groups.items():
            if len(group) == 1:
                final_groups.append(group)
            else:
                # Check semantic similarity within service group
                semantic_groups = self._group_by_semantic_similarity(group)
                final_groups.extend(semantic_groups)

        return final_groups

    def _group_by_semantic_similarity(self, anomalies: List[Anomaly]) -> List[List[Anomaly]]:
        """Group anomalies by semantic similarity of their messages."""
        if len(anomalies) <= 1:
            return [anomalies]

        try:
            # Get embeddings for all messages
            messages = [a.message for a in anomalies]
            embeddings = self.embedding_service.get_embeddings(messages)

            # Use DBSCAN to cluster by semantic similarity
            clustering = DBSCAN(eps=0.5, min_samples=1, metric='cosine')
            labels = clustering.fit_predict(embeddings)

            # Group by cluster labels
            groups = {}
            for i, label in enumerate(labels):
                if label not in groups:
                    groups[label] = []
                groups[label].append(anomalies[i])

            return list(groups.values())
        except Exception as e:
            logger.warning(f"Semantic clustering failed: {e}. Falling back to individual grouping.")
            return [[a] for a in anomalies]

    def _create_incident_from_anomaly(self, anomaly: Anomaly) -> Optional[Incident]:
        """Create an incident from a single anomaly."""
        try:
            # Determine incident title based on anomaly
            title = self._generate_incident_title(anomaly)

            # Create incident
            incident = Incident(
                title=title,
                severity="PENDING",  # Will be updated by severity prediction
                status="ACTIVE",
                incident_score=0.0,  # Will be calculated
                root_cause=None,
                confidence=None
            )
            self.db.add(incident)
            self.db.flush()  # Get the ID

            # Link anomaly to incident
            incident.anomalies.append(anomaly)

            self.db.commit()
            return incident
        except Exception as e:
            logger.error(f"Error creating incident from anomaly: {e}")
            self.db.rollback()
            return None

    def _create_incident_from_anomalies(self, anomalies: List[Anomaly]) -> Optional[Incident]:
        """Create an incident from multiple related anomalies."""
        try:
            # Generate title based on the anomalies
            title = self._generate_incident_title_from_multiple(anomalies)

            # Create incident
            incident = Incident(
                title=title,
                severity="PENDING",
                status="ACTIVE",
                incident_score=0.0,
                root_cause=None,
                confidence=None
            )
            self.db.add(incident)
            self.db.flush()

            # Link all anomalies to incident
            for anomaly in anomalies:
                incident.anomalies.append(anomaly)

            self.db.commit()
            return incident
        except Exception as e:
            logger.error(f"Error creating incident from multiple anomalies: {e}")
            self.db.rollback()
            return None

    def _generate_incident_title(self, anomaly: Anomaly) -> str:
        """Generate a title for an incident based on a single anomaly."""
        service_name = anomaly.service.name if anomaly.service else "unknown"
        level = anomaly.level.value if hasattr(anomaly.level, 'value') else str(anomaly.level)

        # Extract key info from message
        message = anomaly.message.lower()
        if "database" in message or "db" in message:
            return f"{service_name} Database Issue"
        elif "memory" in message:
            return f"{service_name} Memory Issue"
        elif "cpu" in message:
            return f"{service_name} CPU Spike"
        elif "network" in message or "connection" in message:
            return f"{service_name} Network Issue"
        elif "http" in message or "500" in message or "timeout" in message:
            return f"{service_name} HTTP Error"
        else:
            return f"{service_name} {level} Incident"

    def _generate_incident_title_from_multiple(self, anomalies: List[Anomaly]) -> str:
        """Generate a title for an incident based on multiple anomalies."""
        # Get unique services
        services = list(set([a.service.name for a in anomalies if a.service]))
        service_str = ", ".join(services[:3])  # Limit to 3 services
        if len(services) > 3:
            service_str += f" and {len(services)-3} more"

        # Determine common theme
        messages = [a.message.lower() for a in anomalies]
        combined_message = " ".join(messages)

        if "database" in combined_message or "db" in combined_message:
            return f"Database Issue affecting {service_str}"
        elif "memory" in combined_message:
            return f"Memory Issue affecting {service_str}"
        elif "cpu" in combined_message:
            return f"CPU Spike affecting {service_str}"
        elif "network" in combined_message or "connection" in combined_message:
            return f"Network Issue affecting {service_str}"
        else:
            return f"Multi-service Incident affecting {service_str}"

    def _is_significant_anomaly(self, anomaly: Anomaly) -> bool:
        """Check if an anomaly is significant enough to create an incident on its own."""
        # Significant if high anomaly score or critical level
        if anomaly.anomaly_score >= 0.8:
            return True
        if anomaly.level.value if hasattr(anomaly.level, 'value') else str(anomaly.level) == "CRITICAL":
            return True
        return False