from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from io import StringIO
import csv
import logging
from datetime import datetime

from api import db
from api.models import User, Detection

# Create API Blueprint
api = Blueprint("api", __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@api.route('/status', methods=['GET'])
def status():
    """Health check endpoint"""
    return jsonify({"status": "Server is running"}), 200

@api.route('/detect', methods=['POST'])
@jwt_required()
def detect():
    """Store drowsiness detection status"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        status = data.get("status", "Unknown").strip()
        user_email = get_jwt_identity()
        
        if not status:
            return jsonify({"error": "Status is required"}), 400
            
        user = User.query.filter_by(email=user_email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        new_detection = Detection(user_id=user.id, status=status)
        db.session.add(new_detection)
        db.session.commit()
        
        return jsonify({
            "message": f"Detection saved for {user_email}",
            "status": status
        }), 201
    except Exception as e:
        logger.error(f"Detection error: {str(e)}")
        return jsonify({"error": "Failed to save detection"}), 500

@api.route("/logs", methods=["GET"])
@jwt_required()
def get_logs():
    """Get detection logs for the current user or filtered by status"""
    try:
        status_filter = request.args.get('status')
        user_filter = request.args.get('user')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = Detection.query.order_by(Detection.timestamp.desc())
        
        if status_filter:
            query = query.filter(Detection.status == status_filter)
            
        current_user_email = get_jwt_identity()
        current_user = User.query.filter_by(email=current_user_email).first()
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
            
        if current_user.role != 'admin':
            query = query.filter(Detection.user_id == current_user.id)
        elif user_filter:
            filter_user = User.query.filter_by(email=user_filter).first()
            if filter_user:
                query = query.filter(Detection.user_id == filter_user.id)
                
        paginated_logs = query.paginate(page=page, per_page=per_page)
        
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
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching logs: {str(e)}")
        return jsonify({"error": "Database operation failed"}), 500
    except Exception as e:
        logger.error(f"Unexpected error fetching logs: {str(e)}")
        return jsonify({"error": "Failed to fetch logs"}), 500

@api.route("/analytics", methods=["GET"])
@jwt_required()
def analytics():
    """Get analytics for the current user"""
    try:
        user_email = get_jwt_identity()
        user = User.query.filter_by(email=user_email).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        total = Detection.query.filter_by(user_id=user.id).count()
        
        # Make these case-insensitive for more reliability
        drowsy = Detection.query.filter(
            Detection.user_id == user.id, 
            func.lower(Detection.status) == "drowsy"
        ).count()
        
        awake = Detection.query.filter(
            Detection.user_id == user.id, 
            func.lower(Detection.status) == "awake"
        ).count()
        
        recent = Detection.query.filter_by(user_id=user.id).order_by(Detection.timestamp.desc()).first()
        
        return jsonify({
            "total_detections": total,
            "drowsy_count": drowsy,
            "awake_count": awake,
            "most_recent_status": recent.status if recent else "N/A"
        }), 200
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        return jsonify({"error": "Failed to fetch analytics"}), 500

@api.route("/analytics/timeline", methods=["GET"])
@jwt_required()
def detection_timeline():
    """Get detection timeline for the current user"""
    try:
        user_email = get_jwt_identity()
        user = User.query.filter_by(email=user_email).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        data = (
            db.session.query(
                func.date(Detection.timestamp).label("date"),
                Detection.status,
                func.count().label("count")
            )
            .filter(Detection.user_id == user.id)
            .group_by(func.date(Detection.timestamp), Detection.status)
            .order_by(func.date(Detection.timestamp))
            .all()
        )
        
        timeline = {}
        for row in data:
            date = row.date.strftime("%Y-%m-%d")
            if date not in timeline:
                timeline[date] = {"drowsy": 0, "awake": 0}
            if row.status.lower() == "drowsy":
                timeline[date]["drowsy"] += row.count
            else:
                timeline[date]["awake"] += row.count
                
        timeline_list = [{"date": date, **counts} for date, counts in timeline.items()]
        
        return jsonify({"timeline": timeline_list}), 200
    except Exception as e:
        logger.error(f"Timeline error: {str(e)}")
        return jsonify({"error": "Failed to fetch timeline"}), 500

@api.route("/logs/download", methods=["GET"])
@jwt_required()
def download_logs():
    """Download logs as CSV"""
    try:
        user_email = get_jwt_identity()
        user = User.query.filter_by(email=user_email).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        logs = Detection.query.filter_by(user_id=user.id).order_by(Detection.timestamp.desc()).all()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "user", "status", "timestamp"])
        
        for log in logs:
            writer.writerow([log.id, user_email, log.status, log.timestamp])
            
        output.seek(0)
        
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=detection_logs.csv"}
        )
    except Exception as e:
        logger.error(f"CSV download error: {str(e)}")
        return jsonify({"error": "Failed to generate CSV"}), 500

@api.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        user_email = get_jwt_identity()
        user = User.query.filter_by(email=user_email).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({
            "email": user_email,
            "role": user.role,
            "message": "Profile fetched successfully"
        }), 200
    except Exception as e:
        logger.error(f"Profile error: {str(e)}")
        return jsonify({"error": "Failed to fetch profile"}), 500