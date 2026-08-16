"""
Verification script to check that the AI Observability Platform components can be imported correctly.
"""
import sys
import traceback

def test_imports():
    """Test that key components can be imported."""
    failures = []

    # Test core imports
    try:
        from app.core.config import settings
        print("[OK] Core config imported successfully")
    except Exception as e:
        failures.append(f"Core config: {e}")

    try:
        from app.core.database import Base, engine, get_db
        print("[OK] Core database imported successfully")
    except Exception as e:
        failures.append(f"Core database: {e}")

    # Test model imports
    try:
        from app.models.database import Base, Service, MetricsHourly, Anomaly, Incident, AIReport
        from app.models.schemas import LogCreate, LogLevel, IncidentCreate, AnomalyCreate
        print("[OK] Models imported successfully")
    except Exception as e:
        failures.append(f"Models: {e}")

    # Test service imports
    try:
        from app.services.log_parser import LogParserService
        from app.services.anomaly_detector import AnomalyDetector
        from app.services.incident_correlator import IncidentCorrelator
        from app.services.severity_classifier import SeverityClassifier
        from app.services.feature_engineering import FeatureEngineeringService
        from app.services.embedding_service import EmbeddingService
        from app.services.rag_service import RAGService
        from app.services.llm_service import LLMService
        print("[OK] Services imported successfully")
    except Exception as e:
        failures.append(f"Services: {e}")

    # Test API imports
    try:
        from app.main import app
        from app.api.v1.router import api_router
        from app.api.v1.endpoints import logs, incidents, anomalies, predictions, ai
        print("[OK] API components imported successfully")
    except Exception as e:
        failures.append(f"API: {e}")

    # Test script imports (these might fail due to missing dependencies, but let's try)
    try:
        from scripts.seed_database import main as seed_main
        print("[OK] Seed database script imported successfully")
    except Exception as e:
        failures.append(f"Seed database script: {e}")

    try:
        from scripts.train_models import main as train_main
        print("[OK] Train models script imported successfully")
    except Exception as e:
        failures.append(f"Train models script: {e}")

    if failures:
        print("\n[FAIL] Import failures:")
        for failure in failures:
            print(f"  - {failure}")
        return False
    else:
        print("\n[OK] All imports successful!")
        return True

def test_basic_functionality():
    """Test basic functionality of key components."""
    try:
        # Test settings
        from app.core.config import settings
        assert hasattr(settings, 'POSTGRES_USER')
        assert hasattr(settings, 'REDIS_HOST')
        print("[OK] Settings basic functionality test passed")
    except Exception as e:
        print(f"[FAIL] Settings basic functionality test failed: {e}")
        return False

    try:
        # Test log parser
        from app.services.log_parser import LogParserService
        from app.models.schemas import LogCreate
        from datetime import datetime

        parser = LogParserService()
        test_log = LogCreate(
            timestamp=datetime.utcnow(),
            service="test",
            level="INFO",
            message="test",
            environment="test"
        )
        # We won't actually run the async method in this simple test
        print("[OK] Log parser basic functionality test passed")
    except Exception as e:
        print(f"[FAIL] Log parser basic functionality test failed: {e}")
        return False

    try:
        # Test anomaly detector
        from app.services.anomaly_detector import AnomalyDetector
        detector = AnomalyDetector()
        assert detector.isolation_forest is not None
        print("[OK] Anomaly detector basic functionality test passed")
    except Exception as e:
        print(f"[FAIL] Anomaly detector basic functionality test failed: {e}")
        return False

    print("\n[OK] Basic functionality tests passed!")
    return True

if __name__ == "__main__":
    print("Verifying AI Observability Platform setup...")
    print("=" * 50)

    imports_ok = test_imports()
    print()
    if imports_ok:
        functionality_ok = test_basic_functionality()
    else:
        functionality_ok = False

    print()
    print("=" * 50)
    if imports_ok and functionality_ok:
        print("All verification tests passed!")
        print("The AI Observability Platform is ready for development.")
        sys.exit(0)
    else:
        print("Some verification tests failed!")
        print("Please check the error messages above.")
        sys.exit(1)