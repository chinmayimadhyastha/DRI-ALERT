from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from functools import wraps
from models import User
from detection_model import DetectionEvent
from mongodb_config import get_mongo_db
import logging

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_users():
    """Get all users with real-time monitoring status (admin only)"""
    try:
        db = get_mongo_db()
        users_collection = db['users']
        
        # Users are "active" if they sent a heartbeat in last 10 seconds
        active_threshold = datetime.utcnow() - timedelta(seconds=10)
        
        users_cursor = users_collection.find({}, {
            'password_hash': 0,  # Exclude password
            '_id': 0
        })
        
        user_list = []
        for user in users_cursor:
            # Check if user is currently monitoring
            last_seen = user.get('last_seen')
            is_monitoring = user.get('is_monitoring', False)
            
            # Active = heartbeat within last 10 seconds AND is_monitoring flag
            is_active = False
            if last_seen and is_monitoring:
                if isinstance(last_seen, datetime):
                    is_active = last_seen > active_threshold
                elif isinstance(last_seen, str):
                    try:
                        last_seen_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                        is_active = last_seen_dt > active_threshold
                    except:
                        pass
            
            user_list.append({
                'email': user.get('email'),
                'role': user.get('role', 'driver'),
                'is_active': is_active,  # ✅ Real-time monitoring status
                'last_seen': last_seen.isoformat() if isinstance(last_seen, datetime) else last_seen,
                'created_at': user.get('created_at', datetime.now().isoformat())
            })
        
        logger.info(f"✅ Retrieved {len(user_list)} users with real-time status")
        return jsonify({'users': user_list}), 200
        
    except Exception as e:
        logger.error(f"Admin users error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve users', 'details': str(e)}), 500

@admin_bp.route('/analytics', methods=['GET'])
@jwt_required()
@admin_required
def get_analytics():
    """Get system analytics (admin only)"""
    try:
        db = get_mongo_db()
        if db is None:
            return jsonify({"error": "Database not connected"}), 500

        users_collection = db['users']
        detections_collection = db['detection_events']

        total_users = users_collection.count_documents({})
        total_detections = detections_collection.count_documents({})

        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_activity = detections_collection.count_documents({
            'timestamp': {'$gte': week_ago}
        })

        risk_pipeline = [
            {'$group': {
                '_id': '$detection_data.risk_level',
                'count': {'$sum': 1}
            }}
        ]
        
        risk_counts = {}
        for result in detections_collection.aggregate(risk_pipeline):
            risk_level = result['_id'] or 'Unknown'
            risk_counts[risk_level] = result['count']

        for level in ['Low', 'Medium', 'High', 'Critical', 'Unknown']:
            risk_counts.setdefault(level, 0)

        analytics = {
            'total_users': total_users,
            'total_detections': total_detections,
            'recent_activity': recent_activity,
            'status_counts': risk_counts
        }

        logger.info(f"✅ Analytics: {analytics}")
        return jsonify(analytics), 200
    except Exception as e:
        logger.error(f"Admin analytics error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve analytics', 'details': str(e)}), 500

@admin_bp.route('/logs', methods=['GET'])
@jwt_required()
@admin_required
def get_detection_logs():
    """Get detection logs (admin only)"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        db = get_mongo_db()
        detections_collection = db['detection_events']
        
        # Get recent detections, sorted by timestamp descending
        detections_cursor = detections_collection.find({}).sort('timestamp', -1).limit(limit)
        
        logs = []
        for detection in detections_cursor:
            logs.append({
                'id': str(detection.get('_id', '')),
                'user_email': detection.get('user_email', 'Unknown'),
                'timestamp': detection.get('timestamp').isoformat() if isinstance(detection.get('timestamp'), datetime) else str(detection.get('timestamp', '')),
                'detection_data': detection.get('detection_data', {}),
                'session_data': detection.get('session_data', {})
                })

        logger.info(f"✅ Retrieved {len(logs)} detection logs")
        return jsonify({'logs': logs}), 200
        
    except Exception as e:
        logger.error(f"Admin logs error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve logs', 'details': str(e)}), 500

@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
@admin_required
def get_system_stats():
    """Get system statistics (admin only)"""
    try:
        db = get_mongo_db()
        
        # Database stats
        stats = {
            'database': db.name,
            'collections': db.list_collection_names()
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({'error': str(e)}), 500
