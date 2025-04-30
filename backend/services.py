from flask import jsonify
import pymysql
from pymysql import OperationalError
from datetime import datetime
import logging
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection pool
connection_pool = None

def initialize_db_pool():
    """Initialize the database connection pool"""
    global connection_pool
    try:
        connection_pool = pymysql.ConnectionPool(
            min_size=1,
            max_size=5,
            host='localhost',
            user='root',
            password='chinmayi',
            database='drowsiness_db',
            autocommit=True
        )
        logger.info("Database connection pool initialized")
    except OperationalError as e:
        logger.error(f"Failed to initialize connection pool: {e}")
        raise

def db_connection_handler(func):
    """Decorator to handle database connections"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        connection = None
        try:
            connection = connection_pool.get_connection()
            logger.debug("Acquired database connection from pool")
            return func(connection, *args, **kwargs)
        except OperationalError as e:
            logger.error(f"Database operation failed: {e}")
            return jsonify({"error": "Database operation failed"}), 500
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return jsonify({"error": "Internal server error"}), 500
        finally:
            if connection:
                connection.close()
                logger.debug("Returned connection to pool")
    return wrapper

# Initialize the pool when the module loads
try:
    initialize_db_pool()
except OperationalError:
    logger.error("Failed to initialize database pool on startup")

@db_connection_handler
def save_detection_result(connection, drowsy_status, user):
    """Save detection result to the database"""
    try:
        valid_statuses = ['drowsy', 'awake']
        if drowsy_status.lower() not in valid_statuses:
            logger.warning(f"Invalid status received: {drowsy_status}")
            return jsonify({"error": "Invalid status value"}), 400

        with connection.cursor() as cursor:
            query = """
            INSERT INTO detections (user, status, timestamp) 
            VALUES (%s, %s, %s)
            """
            cursor.execute(query, (user, drowsy_status.lower(), datetime.now()))
        
        logger.info(f"Detection saved for user {user}")
        return jsonify({
            "message": "Detection saved successfully",
            "status": drowsy_status,
            "user": user
        }), 201

    except Exception as e:
        logger.error(f"Error saving detection: {e}")
        connection.rollback()
        return jsonify({"error": "Failed to save detection"}), 500

@db_connection_handler
def get_logs(connection):
    """Retrieve all detection logs"""
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
            SELECT id, user, status, 
                   DATE_FORMAT(timestamp, '%%Y-%%m-%%d %%H:%%i:%%s') as timestamp 
            FROM detections 
            ORDER BY timestamp DESC
            """
            cursor.execute(query)
            logs = cursor.fetchall()
        
        logger.info(f"Retrieved {len(logs)} logs")
        return {"logs": logs}
    
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        return jsonify({"error": "Failed to fetch logs"}), 500

# Additional utility functions
def get_user_detections(user_email):
    """Get detections for a specific user"""
    try:
        connection = connection_pool.get_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
            SELECT status, timestamp 
            FROM detections 
            WHERE user = %s 
            ORDER BY timestamp DESC
            """
            cursor.execute(query, (user_email,))
            return cursor.fetchall()
    finally:
        if connection:
            connection.close()