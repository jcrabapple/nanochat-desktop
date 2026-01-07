"""
Initial database schema migration
Creates conversations and messages tables
"""
import logging
from nanochat.data.models import Base

logger = logging.getLogger(__name__)


def upgrade(engine):
    """Create initial schema"""
    logger.info("Running initial migration: creating tables")
    Base.metadata.create_all(bind=engine)
    logger.info("Initial migration completed")


def downgrade(engine):
    """Drop all tables"""
    logger.info("Rolling back initial migration: dropping tables")
    Base.metadata.drop_all(bind=engine)
    logger.info("Rollback completed")
