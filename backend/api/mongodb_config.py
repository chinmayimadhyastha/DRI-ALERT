from pymongo import MongoClient
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Global client instance
_client = None
_db = None

def get_mongo_db():
    """Get MongoDB database connection"""
    global _client, _db
    
    try:
        if _db is None:
            # Get connection string from environment variable
            connection_string = os.getenv('MONGODB_URI')
            if not connection_string:
                logger.error("❌ MONGODB_URI environment variable not found")
                return None
            
            # Create client with proper settings
            _client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            
            # Connect to database
            _db = _client['drowsiness_detection']
            
            # Test connection
            _client.admin.command('ping')
            logger.info("✅ MongoDB Atlas connection successful")
        
        return _db
        
    except Exception as e:
        logger.error(f"❌ MongoDB Atlas connection failed: {str(e)}")
        return None

def close_mongo_connection():
    """Close MongoDB connection"""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")
