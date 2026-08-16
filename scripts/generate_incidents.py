"""
Synthetic incident generator for creating test scenarios.
"""
import asyncio
import aiohttp
import json
import random
import time
from datetime import datetime, timedelta
import argparse
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IncidentGenerator:
    def __init__(self, api_url: str = "http://localhost:8000/api/v1"):
        self.api_url = api_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def send_log(self, log_data: Dict[str, Any]):
        """Send a single log entry to the ingestion API."""
        try:
            async with self.session.post(
                f"{self.api_url}/logs/ingest",
                json=[log_data]  # API expects a list
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to send log: {response.status}")
                    return False
                return True
        except Exception as e:
            logger.error(f"Error sending log: {e}")
            return False

    def generate_database_failure_scenario(self, duration_minutes: int = 5, intensity: str = "medium") -> List[Dict[str, Any]]:
        """
        Generate a database failure scenario.

        Effects:
        - DB latency increases +300%
        - HTTP 500 rate increases +20%
        - Connection pool utilization reaches +95%
        - Payment service latency increases +250%
        """
        logs = []
        start_time = datetime.utcnow()

        # Parameters based on intensity
        if intensity == "low":
            latency_multiplier = 2.0
            error_rate_increase = 0.05
            pool_utilization = 0.7
            duration_minutes = max(2, duration_minutes // 2)
        elif intensity == "medium":
            latency_multiplier = 4.0  # 300% increase
            error_rate_increase = 0.20  # 20% increase
            pool_utilization = 0.95   # 95% utilization
        elif intensity == "high":
            latency_multiplier = 6.0
            error_rate_increase = 0.40
            pool_utilization = 0.98
        else:
            latency_multiplier = 4.0
            error_rate_increase = 0.20
            pool_utilization = 0.95

        # Generate logs over time
        end_time = start_time + timedelta(minutes=duration_minutes)
        current_time = start_time

        # Normal baseline values
        normal_db_latency = 50  # ms
        normal_http_500_rate = 0.02  # 2%
        normal_payment_latency = 200  # ms
        normal_pool_utilization = 0.3  # 30%

        while current_time < end_time:
            # Progress through the incident (0.0 to 1.0)
            progress = (current_time - start_time).total_seconds() / (duration_minutes * 60)

            # Simulate gradual onset and recovery
            intensity_factor = min(1.0, progress * 2)  # Ramp up
            if progress > 0.7:  # Start recovery after 70% of duration
                intensity_factor = max(0.0, 1.0 - (progress - 0.7) * 3)  # Ramp down

            # Calculate current values
            db_latency = normal_db_latency * (1 + (latency_multiplier - 1) * intensity_factor)
            http_500_rate = normal_http_500_rate * (1 + error_rate_increase * intensity_factor)
            payment_latency = normal_payment_latency * (1 + (latency_multiplier * 0.8) * intensity_factor)  # Slightly less than DB
            pool_utilization = normal_pool_utilization + (pool_utilization - normal_pool_utilization) * intensity_factor

            # Generate database logs
            if random.random() < 0.3:  # 30% chance of DB log per interval
                logs.append({
                    "timestamp": current_time.isoformat(),
                    "service": "database",
                    "level": "ERROR" if random.random() < 0.7 else "WARNING",
                    "message": f"Database connection timeout - latency {db_latency:.1f}ms",
                    "host": f"db-{random.randint(1, 3)}",
                    "latency_ms": db_latency,
                    "environment": "production"
                })

            # Generate HTTP 500 logs
            if random.random() < http_500_rate * 10:  # Scale for logging frequency
                logs.append({
                    "timestamp": current_time.isoformat(),
                    "service": "payment-service",
                    "level": "ERROR",
                    "message": "Internal server error - database connection failed",
                    "host": f"web-{random.randint(1, 5)}",
                    "status_code": 500,
                    "latency_ms": payment_latency,
                    "environment": "production"
                })

            # Generate payment service logs
            if random.random() < 0.4:  # 40% chance of payment log per interval
                logs.append({
                    "timestamp": current_time.isoformat(),
                    "service": "payment-service",
                    "level": "WARNING" if payment_latency < 1000 else "ERROR",
                    "message": f"Payment processing latency high: {payment_latency:.1f}ms",
                    "host": f"web-{random.randint(1, 5)}",
                    "latency_ms": payment_latency,
                    "environment": "production"
                })

            # Generate connection pool logs
            if random.random() < 0.2:  # 20% chance of pool log per interval
                level = "CRITICAL" if pool_utilization > 0.9 else "ERROR" if pool_utilization > 0.8 else "WARNING"
                logs.append({
                    "timestamp": current_time.isoformat(),
                    "service": "database",
                    "level": level,
                    "message": f"Database connection pool utilization: {pool_utilization*100:.1f}%",
                    "host": f"db-{random.randint(1, 3)}",
                    "environment": "production"
                })

            # Advance time
            current_time += timedelta(seconds=random.uniform(1, 3))  # 1-3 second intervals

        logger.info(f"Generated {len(logs)} logs for {intensity} database failure scenario")
        return logs

    def generate_memory_leak_scenario(self, duration_minutes: int = 4, intensity: str = "medium") -> List[Dict[str, Any]]:
        """Generate a memory leak scenario."""
        # Similar structure but for memory leak
        logs = []
        start_time = datetime.utcnow()

        # Parameters
        if intensity == "low":
            memory_growth_rate = 5  # MB per minute
        elif intensity == "medium":
            memory_growth_rate = 15
        elif intensity == "high":
            memory_growth_rate = 30
        else:
            memory_growth_rate = 15

        end_time = start_time + timedelta(minutes=duration_minutes)
        current_time = start_time

        normal_memory = 200  # MB
        normal_latency = 100  # ms

        while current_time < end_time:
            progress = (current_time - start_time).total_seconds() / (duration_minutes * 60)
            intensity_factor = min(1.0, progress * 1.5)

            # Memory grows over time
            current_memory = normal_memory + (memory_growth_rate * progress * duration_minutes)
            latency_increase = 1 + (current_memory - normal_memory) / normal_memory * 2  # Latency increases with memory usage

            # Generate application logs
            if random.random() < 0.3:
                level = "WARNING" if current_memory < 500 else "ERROR" if current_memory < 800 else "CRITICAL"
                logs.append({
                    "timestamp": current_time.isoformat(),
                    "service": "application-service",
                    "level": level,
                    "message": f"High memory usage detected: {current_memory:.1f}MB",
                    "host": f"app-{random.randint(1, 3)}",
                    "environment": "production"
                })

            # Generate latency logs
            if random.random() < 0.4:
                logs.append({
                    "timestamp": current_time.isoformat(),
                    "service": "application-service",
                    "level": "INFO",
                    "message": f"Request processed successfully",
                    "host": f"app-{random.randint(1, 3)}",
                    "latency_ms": normal_latency * latency_increase,
                    "environment": "production"
                })

            current_time += timedelta(seconds=random.uniform(2, 5))

        logger.info(f"Generated {len(logs)} logs for {intensity} memory leak scenario")
        return logs

    async def run_scenario(self, scenario_type: str, duration_minutes: int = 5, intensity: str = "medium", logs_per_second: float = 2.0):
        """
        Run a scenario by sending logs at a specified rate.
        """
        logger.info(f"Starting {scenario_type} scenario ({intensity} intensity) for {duration_minutes} minutes")

        # Generate logs
        if scenario_type == "database_failure":
            logs = self.generate_database_failure_scenario(duration_minutes, intensity)
        elif scenario_type == "memory_leak":
            logs = self.generate_memory_leak_scenario(duration_minutes, intensity)
        else:
            logger.error(f"Unknown scenario type: {scenario_type}")
            return

        # Send logs at specified rate
        total_time = duration_minutes * 60
        delay_between_logs = total_time / len(logs) if logs else 0

        sent_count = 0
        for log in logs:
            success = await self.send_log(log)
            if success:
                sent_count += 1

            # Wait before sending next log (to maintain rate)
            if sent_count < len(logs):
                await asyncio.sleep(delay_between_logs)

        logger.info(f"Sent {sent_count}/{len(logs)} logs for {scenario_type} scenario")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic incidents for testing")
    parser.add_argument("--scenario", type=str, default="database_failure",
                        choices=["database_failure", "memory_leak"],
                        help="Type of incident scenario to generate")
    parser.add_argument("--duration", type=int, default=5,
                        help="Duration of scenario in minutes")
    parser.add_argument("--intensity", type=str, default="medium",
                        choices=["low", "medium", "high"],
                        help="Intensity of the scenario")
    parser.add_argument("--rate", type=float, default=2.0,
                        help="Logs per second to send")
    parser.add_argument("--url", type=str, default="http://localhost:8000/api/v1",
                        help="API URL for log ingestion")

    args = parser.parse_args()

    async def run():
        async with IncidentGenerator(args.url) as generator:
            await generator.run_scenario(
                scenario_type=args.scenario,
                duration_minutes=args.duration,
                intensity=args.intensity,
                logs_per_second=args.rate
            )

    asyncio.run(run())


if __name__ == "__main__":
    main()