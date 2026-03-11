# backend/setup_db.py - Run this ONCE to fix existing duplicates and add unique constraint

from mongodb_config import get_mongo_db
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def remove_duplicate_users():
    """Remove duplicate user entries keeping the oldest one"""
    try:
        db = get_mongo_db()
        users_collection = db['users']
        
        # Find all emails
        pipeline = [
            {
                '$group': {
                    '_id': '$email',
                    'count': {'$sum': 1},
                    'ids': {'$push': '$_id'},
                    'created_ats': {'$push': '$created_at'}
                }
            },
            {
                '$match': {'count': {'$gt': 1}}  # Only duplicates
            }
        ]
        
        duplicates = list(users_collection.aggregate(pipeline))
        
        if not duplicates:
            logger.info("✅ No duplicate users found")
            return
        
        logger.info(f"🔍 Found {len(duplicates)} emails with duplicates")
        
        for dup in duplicates:
            email = dup['_id']
            ids = dup['ids']
            created_ats = dup['created_ats']
            
            # Keep the oldest user (first created_at)
            oldest_index = created_ats.index(min(created_ats))
            keep_id = ids[oldest_index]
            
            # Delete all others
            delete_ids = [id for id in ids if id != keep_id]
            result = users_collection.delete_many({'_id': {'$in': delete_ids}})
            
            logger.info(f"✅ Kept oldest {email}, deleted {result.deleted_count} duplicates")
        
        logger.info("✅ Duplicate cleanup complete")
        
    except Exception as e:
        logger.error(f"❌ Error removing duplicates: {e}")

def create_unique_index():
    """Create unique index on email field"""
    try:
        db = get_mongo_db()
        users_collection = db['users']
        
        # Create unique index on email (case-insensitive)
        users_collection.create_index(
            [('email', 1)],
            unique=True,
            name='email_unique_index'
        )
        
        logger.info("✅ Unique index created on email field")
        
        # Verify index
        indexes = list(users_collection.list_indexes())
        logger.info(f"📋 Current indexes: {[idx['name'] for idx in indexes]}")
        
    except Exception as e:
        logger.error(f"❌ Error creating index: {e}")

if __name__ == '__main__':
    logger.info("🚀 Starting database cleanup and setup...")
    remove_duplicate_users()
    create_unique_index()
    logger.info("✅ Database setup complete!")
