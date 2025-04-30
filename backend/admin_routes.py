from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func
import logging

from api import db
from api.models import User, Detection
from api.decorators import admin_required

# Create admin blueprint
admin_bp = Blueprint('admin', __name__)

# Configure logging
logger = logging.getLogger(__name__)

@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@admin_required
def get_users():
    """Get all users (admin only)"""
    try:            
        # Get all users
        users = User.query.all()
        
        user_list = [{
            "id": user.id,
            "email": user.email,
            "role": user.role
        } for user in users]
        
        return jsonify({"users": user_list}), 200
    except Exception as e:
        logger.error(f"Admin users error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/logs", methods=["GET"])
@jwt_required()
@admin_required
def get_all_logs():
    """Get all logs (admin only)"""
    try:
        # Get filtering parameters
        user_filter = request.args.get('user')
        status_filter = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Build query
        query = Detection.query
        
        if user_filter:
            user = User.query.filter_by(email=user_filter).first()
            if user:
                query = query.filter(Detection.user_id == user.id)
            
        if status_filter:
            query = query.filter(Detection.status == status_filter)
            
        # Paginate results
        paginated_logs = query.order_by(Detection.timestamp.desc()).paginate(
            page=page, per_page=per_page
        )
        
        logs_data = []
        for log in paginated_logs.items:
            user = User.query.get(log.user_id)
            logs_data.append({
                "id": log.id,
                "user": user.email if user else "Unknown",
                "status": log.status,
                "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return jsonify({
            "logs": logs_data,
            "total_logs": paginated_logs.total,
            "total_pages": paginated_logs.pages,
            "current_page": page
        }), 200
    except Exception as e:
        logger.error(f"Admin logs error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/analytics", methods=["GET"])
@jwt_required()
@admin_required
def admin_analytics():
    """Get analytics for all users (admin only)"""
    try:
        # Get total counts
        total_users = User.query.count()
        total_detections = Detection.query.count()
        
        # Get counts by status
        status_counts = db.session.query(
            Detection.status, 
            func.count().label('count')
        ).group_by(Detection.status).all()
        
        status_data = {status: count for status, count in status_counts}
        
        # Get top users by detection count
        top_users_query = db.session.query(
            User.email,
            func.count(Detection.id).label('count')
        ).join(
            Detection, User.id == Detection.user_id
        ).group_by(
            User.email
        ).order_by(
            func.count(Detection.id).desc()
        ).limit(5).all()
        
        top_users = [{"user": email, "count": count} for email, count in top_users_query]
        
        return jsonify({
            "total_users": total_users,
            "total_detections": total_detections,
            "status_counts": status_data,
            "top_users": top_users
        }), 200
    except Exception as e:
        logger.error(f"Admin analytics error: {str(e)}")
        return jsonify({"error": str(e)}), 500