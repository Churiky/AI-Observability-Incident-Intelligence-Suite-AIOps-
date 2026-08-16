"""
Database seeding script for initial setup.
"""
import argparse
import logging
from datetime import datetime
from app.models.database import *
from app.core.database import SessionLocal, engine, Base
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_session():
    return SessionLocal()


def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def drop_tables():
    """Drop all database tables."""
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("Database tables dropped")


def seed_services(db):
    """Seed initial services."""
    logger.info("Seeding initial services...")

    services = [
        {"name": "payment-service", "environment": "production"},
        {"name": "user-service", "environment": "production"},
        {"name": "api-gateway", "environment": "production"},
        {"name": "database", "environment": "production"},
        {"name": "cache-service", "environment": "production"},
        {"name": "auth-service", "environment": "production"},
        {"name": "notification-service", "environment": "production"},
    ]

    for service_data in services:
        # Check if service already exists
        existing = db.query(Service).filter(Service.name == service_data["name"]).first()
        if not existing:
            service = Service(**service_data)
            db.add(service)
            logger.info(f"Added service: {service_data['name']}")

    db.commit()
    logger.info("Services seeded successfully")


def main():
    parser = argparse.ArgumentParser(description="Seed the database for the observability platform")
    parser.add_argument("--create-tables", action="store_true",
                        help="Create database tables")
    parser.add_argument("--drop-tables", action="store_true",
                        help="Drop database tables (use with caution)")
    parser.add_argument("--seed-services", action="store_true",
                        help="Seed initial services")
    parser.add_argument("--setup-all", action="store_true",
                        help="Run complete database setup")

    args = parser.parse_args()

    if not any([args.create_tables, args.drop_tables, args.seed_services, args.setup_all]):
        # Default to setup-all if nothing specified
        args.setup_all = True

    db = get_db_session()
    try:
        if args.setup_all or args.drop_tables:
            drop_tables()

        if args.setup_all or args.create_tables:
            create_tables()

        if args.setup_all or args.seed_services:
            seed_services(db)

        logger.info("Database setup completed successfully")

    except Exception as e:
        logger.error(f"Error during database setup: {e}")
        db.rollback()
        return 1
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    exit(main())