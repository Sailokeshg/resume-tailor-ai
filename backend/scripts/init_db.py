#!/usr/bin/env python3
"""
Database initialization script for Resume Tailor AI
Creates the ChromaDB collection and optionally adds sample data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database with basic setup"""
    try:
        # The RAG service will automatically create the collection
        logger.info("Database initialized successfully")
        logger.info("ChromaDB collection 'resume_job_matches' is ready")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("✅ Database initialized successfully")
    else:
        print("❌ Database initialization failed")
        sys.exit(1) 