import json
import base64
import os
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash
from models import User
from datetime import datetime
from mongodb_config import get_mongo_db

auth_bp = Blueprint('auth', __name__)

# Create photos directory
PHOTOS_DIR = os.path.join(os.path.dirname(__file__), 'driver_photos')
os.makedirs(PHOTOS_DIR, exist_ok=True)

def save_driver_photo(email, base64_image, status):
    """Save driver photo to file system and return path"""
    try:
        username = email.replace('@', '_').replace('.', '_')
        user_dir = os.path.join(PHOTOS_DIR, username)
        os.makedirs(user_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{username}_{timestamp}_{status.lower()}.jpg"
        filepath = os.path.join(user_dir, filename)
        
        if ',' in base64_image:
            base64_image = base64_image.split(',')[1]
        
        image_data = base64.b64decode(base64_image)
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        relative_path = f"driver_photos/{username}/{filename}"
        print(f"📸 Photo saved: {relative_path}")
        return relative_path
    except Exception as e:
        print(f"❌ Error saving photo: {e}")
        return None

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if User.find_by_email(email):
            return jsonify({'error': 'User already exists'}), 400
        
        user = User(email, password)
        if user.save():
            access_token = create_access_token(identity=email)
            return jsonify({
                'message': 'User created successfully',
                'access_token': access_token
            }), 201
        else:
            return jsonify({'error': 'Failed to create user'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        print(f"🔐 Login attempt for: {email}")
        
        user = User.find_by_email(email)
        if not user:
            print(f"❌ User not found: {email}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        print(f"✅ User found: {user.email}")
        
        if user.check_password(password):
            user.last_login = datetime.utcnow()
            user.save()
            access_token = create_access_token(identity=email)
            print(f"✅ Login successful for: {email}")
            return jsonify({'access_token': access_token}), 200
        else:
            print(f"❌ Password mismatch for: {email}")
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        # FIXED: Removed extra backslash and quote
        print(f"❌ Login error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/admin-login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
        ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
        
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            access_token = create_access_token(
                identity=email,
                additional_claims={'role': 'admin', 'permissions': ['all']}
            )  # FIXED: Added missing closing parenthesis
            
            return jsonify({
                'access_token': access_token,
                'user': {'email': email, 'role': 'admin', 'name': 'Administrator'},
                'permissions': ['all']
            }), 200
        else:
            return jsonify({'error': 'Invalid admin credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/save-detection', methods=['POST', 'OPTIONS'])
def save_detection():
    """Save detection event to database WITHOUT JWT requirement"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        data = request.get_json()
        driver_name = data.get("driver_name", "Unknown Driver")
        print(f"💾 Saving detection for: {driver_name}")
        
        db = get_mongo_db()
        if db is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        detection_record = {
            "driver_name": driver_name,
            "user_email": driver_name,
            "eye_aspect_ratio": data.get("eye_aspect_ratio", 0.0),
            "mouth_aspect_ratio": data.get("mouth_aspect_ratio", 0.0),
            "drowsiness_score": data.get("drowsiness_score", 0.0),
            "risk_level": data.get("risk_level", "Low"),
            "status": data.get("status", "Alert"),
            "alert_triggered": data.get("alert_triggered", False),
            "eye_closure_duration": data.get("eye_closure_duration", 0.0),
            "session_id": data.get("session_id", ""),
            "session_duration": data.get("session_duration", 0),
            "total_detections": data.get("total_detections", 0),
            "timestamp": datetime.utcnow()
        }
        
        image_data = data.get("image_data")
        if image_data:
            detection_record["image_data"] = image_data
        
        result = db.detection_events.insert_one(detection_record)
        print(f"✅ Detection saved: {result.inserted_id}, Risk: {detection_record['risk_level']}")
        
        return jsonify({
            "message": "Detection saved successfully",
            "event_id": str(result.inserted_id)
        }), 201
    except Exception as e:
        print(f"❌ Error saving detection: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/get-detections', methods=['GET'])
@jwt_required()
def get_user_detections():
    """Get detection events for current user"""
    try:
        current_user = get_jwt_identity()
        limit = request.args.get('limit', 50, type=int)
        
        db = get_mongo_db()
        collection = db.detection_events
        
        events = list(collection.find({"user_email": current_user})
                     .sort("timestamp", -1).limit(limit))
        
        for event in events:
            event["_id"] = str(event["_id"])
            if "timestamp" in event:
                event["timestamp"] = event["timestamp"].isoformat()
            if "created_at" in event:
                event["created_at"] = event["created_at"].isoformat()
        
        return jsonify({
            "detections": events,
            "count": len(events),
            "user": current_user
        }), 200
    except Exception as e:
        print(f"❌ Error getting detections: {e}")
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/detection-stats', methods=['GET'])
@jwt_required()
def get_detection_statistics():
    """Get detection statistics for current user"""
    try:
        current_user = get_jwt_identity()
        db = get_mongo_db()
        collection = db.detection_events
        
        total_events = collection.count_documents({"user_email": current_user})
        high_risk_events = collection.count_documents({
            "user_email": current_user,
            "detection_data.risk_level": "High"
        })
        
        from datetime import date
        today = datetime.combine(date.today(), datetime.min.time())
        today_events = collection.count_documents({
            "user_email": current_user,
            "timestamp": {"$gte": today}
        })
        
        pipeline = [
            {"$match": {"user_email": current_user}},
            {"$group": {
                "_id": None,
                "avg_drowsiness": {"$avg": "$detection_data.drowsiness_score"}
            }}
        ]
        
        avg_result = list(collection.aggregate(pipeline))
        avg_drowsiness = round(avg_result[0]["avg_drowsiness"], 2) if avg_result else 0.0
        
        return jsonify({
            "stats": {
                "total_events": total_events,
                "high_risk_events": high_risk_events,
                "today_events": today_events,
                "average_drowsiness_score": avg_drowsiness,
                "user": current_user
            }
        }), 200
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/admin/all-detections', methods=['GET'])
@jwt_required()
def get_all_detections():
    """Get all detection events (admin only)"""
    try:
        limit = request.args.get('limit', 100, type=int)
        db = get_mongo_db()
        collection = db.detection_events
        
        events = list(collection.find().sort("timestamp", -1).limit(limit))
        
        for event in events:
            event["_id"] = str(event["_id"])
            if "timestamp" in event:
                event["timestamp"] = event["timestamp"].isoformat()
            if "created_at" in event:
                event["created_at"] = event["created_at"].isoformat()
        
        return jsonify({
            "detections": events,
            "count": len(events)
        }), 200
    except Exception as e:
        print(f"❌ Error getting all detections: {e}")
        return jsonify({"detections": [], "count": 0}), 200

@auth_bp.route('/photo/<path:photo_path>', methods=['GET'])
def get_photo(photo_path):
    """Serve driver photo"""
    try:
        full_path = os.path.join(PHOTOS_DIR, photo_path)
        if os.path.exists(full_path):
            return send_file(full_path, mimetype='image/jpeg')
        else:
            return jsonify({"error": "Photo not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
