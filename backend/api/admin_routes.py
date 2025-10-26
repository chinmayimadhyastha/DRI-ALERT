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
    """Get all users (admin only)"""
    try:
        users = User.get_all_users()
        user_list = []
        for user in users:
            user_list.append({
                'email': user.get('email'),
                'role': user.get('role'),
                'is_active': user.get('is_active'),
                'created_at': user.get('created_at').isoformat() if user.get('created_at') else None
            })
        return jsonify({'users': user_list}), 200
    except Exception as e:
        logger.error(f"Admin users error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/logs', methods=['GET'])
@jwt_required()
@admin_required
def get_all_logs():
    """Get all detection logs (admin only)"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        events = DetectionEvent.get_all_events(limit=limit)
        logs_data = []
        
        for event in events:
            user_email = event.get('user_email', 'Unknown')
            
            logs_data.append({
                'id': str(event.get('_id', '')),
                'user_email': user_email,
                'detection_data': event.get('detection_data', {}),
                'session_data': event.get('session_data', {}),
                'timestamp': event.get('timestamp')
            })
        
        return jsonify({
            'logs': logs_data,
            'total': len(logs_data)
        }), 200
    
    except Exception as e:
        logger.error(f"Admin logs error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/analytics', methods=['GET'])
@jwt_required()
@admin_required
def admin_analytics():
    """Get system analytics (admin only)"""
    try:
        db = get_mongo_db()
        
        # Get total counts
        total_users = db.users.count_documents({})
        total_detections = db.detection_events.count_documents({})
        
        # FIXED: Properly closed pipeline list
        pipeline = [
            {'$group': {'_id': '$risk_level', 'count': {'$sum': 1}}}
        ]
        
        status_counts = list(db.detection_events.aggregate(pipeline))
        status_data = {item['_id']: item['count'] for item in status_counts}
        
        # Get recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_activity = db.detection_events.count_documents({
            'timestamp': {'$gte': week_ago}
        })
        
        return jsonify({
            'total_users': total_users,
            'total_detections': total_detections,
            'status_counts': status_data,
            'recent_activity': recent_activity
        }), 200
    
    except Exception as e:
        logger.error(f"Admin analytics error: {str(e)}")
        return jsonify({'error': str(e)}), 500
