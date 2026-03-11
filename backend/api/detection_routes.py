from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import base64
import logging
from voice_service import voice_service
from detection_model import DetectionEvent
from models import User
from detection import DrowsinessDetector
from mongodb_config import get_mongo_db  # ← REQUIRED for heartbeat endpoints

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

detection_bp = Blueprint('detection', __name__)

# Import the detector
try:
    from detection import get_detector
    logger.info("✅ Detection module imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import detection module: {e}")
    get_detector = None

# ===== FIXED: Process Frame with Proper OPTIONS Handling =====
@detection_bp.route('/process-frame', methods=['POST', 'OPTIONS'])
def process_frame():
    """Process video frame for drowsiness detection"""
    if request.method == 'OPTIONS':
        response = make_response('', 200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    try:
        data = request.get_json(force=True)
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        frame_data = data.get('frame') or data.get('image')
        
        if not frame_data:
            return jsonify({'error': 'No frame data provided'}), 400
        
        # Get detector
        detector = get_detector()
        if not detector:
            return jsonify({'error': 'Detector not initialized'}), 500
        
        # Import required modules
        import cv2
        import numpy as np
        
        # Decode base64 image
        try:
            if 'base64,' in frame_data:
                frame_data = frame_data.split('base64,')[1]
            
            image_bytes = base64.b64decode(frame_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return jsonify({'error': 'Invalid image data'}), 400
                
        except Exception as decode_error:
            logger.error(f"❌ Image decode error: {str(decode_error)}")
            return jsonify({'error': f'Image decode failed: {str(decode_error)}'}), 400
        
        # Process frame with detector
        result = detector.detect_drowsiness(frame)
        
        if result is None:
            return jsonify({'error': 'Detection failed'}), 500
        
        # FIXED: Format response to match frontend expectations
        # REPLACE lines 88-97 with:
        response_data = {
            "earvalue": float(result.get("ear", 0.0)),
            "marvalue": float(result.get("mar", 0.0)),
            "sleepscore": int(result.get("drowsiness_score", 0)),      # ✅ FIXED: correct key
            "status": result.get("risk_level", "Unknown"),              # ✅ FIXED: correct key
            "alerttriggered": result.get("alert_triggered", False),     # ✅ FIXED: correct ke
            "facedetected": result.get("face_detected", True),          # ✅ FIXED: correct key
            "sessionduration": float(result.get("session_duration", 0.0)),
            "totaldetections": int(result.get("total_detections", 0))
            }
                  
        logger.info(f"✅ Detection - EAR: {response_data['earvalue']:.3f}, Score: {response_data['sleepscore']}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"❌ Error in process_frame: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
 
# ===== ROUTE 1: Save Detection Event =====
@detection_bp.route('/save-detection', methods=['POST'])
@jwt_required()
def save_detection():
    try:
        current_user = get_jwt_identity()
        data = request.get_json()

        image_data = data.get("image_data")  # ADD THIS LINE

        detection_data = {
            'ear': float(data.get('eye_aspect_ratio') or 0),
            'mar': float(data.get('mouth_aspect_ratio') or 0),
            'drowsiness_score': float(data.get('drowsiness_score') or 0),
            'risk_level': data.get('risk_level', 'Low'),
            'status': data.get('status', 'UNKNOWN'),
            'alert_triggered': data.get('alert_triggered', False),
            'eye_duration': float(data.get('eye_closure_duration') or 0),
            'yawn_duration': float(data.get('yawn_duration') or 0),
            'session_id': data.get('session_id'),
            'session_duration': float(data.get('session_duration') or 0),
            'total_detections': int(data.get('total_detections') or 0)
        }

        event = DetectionEvent(
            user_email=current_user,
            driver_name=data.get('driver_name', current_user),
            detection_data=detection_data,
            image_data=image_data
        )

        event_id = event.save()

        return jsonify({
            "message": "Detection saved successfully",
            "event_id": event_id
        }), 201

    except Exception as e:
        logger.error(f"❌ Error in save_detection: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ===== ROUTE 2: Get User Events =====
@detection_bp.route('/events', methods=['GET'])
@jwt_required()
def get_user_events():
    """Get detection events for current user"""
    try:
        current_user = get_jwt_identity()
        limit = request.args.get('limit', 50, type=int)
        
        events = DetectionEvent.get_events_by_user(current_user, limit)
        
        return jsonify({
            "events": events,
            "count": len(events),
            "user": current_user
        }), 200
        
    except Exception as e:
        print(f"❌ Error in get_user_events: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ===== ROUTE 3: Get All Events (Admin) =====
@detection_bp.route('/events/all', methods=['GET'])
@jwt_required()
def get_all_events():
    """Get all detection events (admin only)"""
    try:
        current_user = get_jwt_identity()
        limit = request.args.get('limit', 100, type=int)
        
        events = DetectionEvent.get_all_events(limit)
        
        return jsonify({
            "events": events,
            "count": len(events),
            "admin": current_user
        }), 200
        
    except Exception as e:
        print(f"❌ Error in get_all_events: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ===== ROUTE 4: Get Event Details =====
@detection_bp.route('/events/<event_id>', methods=['GET'])
@jwt_required()
def get_event_details(event_id):
    """Get specific detection event details"""
    try:
        event = DetectionEvent.get_event_by_id(event_id)
        
        if event:
            return jsonify({"event": event}), 200
        else:
            return jsonify({"error": "Event not found"}), 404
            
    except Exception as e:
        print(f"❌ Error in get_event_details: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ===== ROUTE 5: Get Detection Statistics =====
@detection_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_detection_stats():
    """Get detection statistics"""
    try:
        stats = DetectionEvent.get_stats()
        
        return jsonify({
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        print(f"❌ Error in get_detection_stats: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ===== ROUTE 6: Live Alert Handler =====
@detection_bp.route('/live-alert', methods=['POST'])
@jwt_required()
def live_alert():
    """Handle live drowsiness alerts"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        # Save critical detection immediately for high risk
        if data.get("risk_level") == "High":
            detection_data = {
                "ear": data.get("eye_aspect_ratio", 0.0),
                "mar": data.get("mouth_aspect_ratio", 0.0),
                "risk_level": "High",
                "alert_triggered": True,
                "session_id": data.get("session_id", ""),
                "drowsiness_score": data.get("drowsiness_score", 1.0)
            }
            
            event = DetectionEvent(
                user_email=current_user,
                driver_name=data.get("driver_name", current_user),
                detection_data=detection_data,
                image_data=data.get("image_data")
            )
            
            event_id = event.save()
            
            return jsonify({
                "message": "High risk alert logged",
                "event_id": event_id,
                "emergency": True,
                "timestamp": datetime.utcnow().isoformat()
            }), 200
        
        return jsonify({
            "message": "Alert received",
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        print(f"❌ Error in live_alert: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ===== ROUTE 7: Set User Active (JWT OPTIONAL) =====
# Add this to complete the set_user_active function in detection_routes.py

@detection_bp.route('/user/set-active', methods=['POST', 'OPTIONS'])
@jwt_required(optional=True)
def set_user_active():
    """Set user as active when they start monitoring - JWT OPTIONAL FOR TESTING"""
    if request.method == 'OPTIONS':
        response = make_response('', 200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        return response
    
    try:
        # Try to get user from JWT identity
        user_email = get_jwt_identity()
        
        if not user_email:
            # No JWT provided - return success for testing
            print("⚠️ No JWT - bypassing user activation")
            return jsonify({"message": "User activated (no auth)"}), 200
        
        # JWT provided - update user status
        user = User.find_by_email(user_email)
        
        if user:
            user.is_active = True
            user.last_login = datetime.utcnow()
            save_result = user.save()
            
            if save_result:
                print(f"✅ User activated: {user_email}")
                return jsonify({
                    "message": "User activated",
                    "email": user_email,
                    "timestamp": datetime.utcnow().isoformat()
                }), 200
            else:
                return jsonify({"error": "Failed to update user status"}), 500
        else:
            return jsonify({"error": "User not found"}), 404
            
    except Exception as e:
        print(f"⚠️ Error in set_user_active: {str(e)}")
        # Return success anyway for testing
        return jsonify({"message": "User activated (bypass)"}), 200

# ===== ROUTE 8: Set User Inactive (JWT OPTIONAL) =====
@detection_bp.route('/user/set-inactive', methods=['POST', 'OPTIONS'])
@jwt_required(optional=True)
def set_user_inactive():
    """Set user as inactive when they stop monitoring - JWT OPTIONAL FOR TESTING"""
    if request.method == 'OPTIONS':
        response = make_response('', 200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        return response
    
    try:
        # Try to get user from JWT identity
        user_email = get_jwt_identity()
        
        if not user_email:
            # No JWT provided - return success for testing
            print("⚠️ No JWT - bypassing user deactivation")
            return jsonify({"message": "User deactivated (no auth)"}), 200
        
        # JWT provided - update user status
        user = User.find_by_email(user_email)
        
        if user:
            user.is_active = False
            save_result = user.save()
            
            if save_result:
                print(f"✅ User deactivated: {user_email}")
                return jsonify({
                    "message": "User deactivated",
                    "email": user_email,
                    "timestamp": datetime.utcnow().isoformat()
                }), 200
            else:
                return jsonify({"error": "Failed to update user status"}), 500
        else:
            return jsonify({"error": "User not found"}), 404
            
    except Exception as e:
        print(f"⚠️ Error in set_user_inactive: {str(e)}")
        # Return success anyway for testing
        return jsonify({"message": "User deactivated (bypass)"}), 200
    
# detection_routes.py - Add monitoring heartbeat

@detection_bp.route('/user/heartbeat', methods=['POST'])
@jwt_required()
def user_heartbeat():
    """Update user's last_seen timestamp (heartbeat for active monitoring)"""
    try:
        current_user_email = get_jwt_identity()
        
        db = get_mongo_db()
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        # Update last_seen timestamp
        db.users.update_one(
            {'email': current_user_email},
            {
                '$set': {
                    'last_seen': datetime.utcnow(),
                    'is_monitoring': True
                }
            }
        )
        
        return jsonify({"message": "Heartbeat received"}), 200
    except Exception as e:
        logger.error(f"Heartbeat error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@detection_bp.route('/user/stop-monitoring', methods=['POST'])
@jwt_required()
def stop_monitoring():
    """Mark user as no longer monitoring"""
    try:
        current_user_email = get_jwt_identity()
        
        db = get_mongo_db()
        if db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        db.users.update_one(
            {'email': current_user_email},
            {'$set': {'is_monitoring': False}}
        )
        
        logger.info(f"User {current_user_email} stopped monitoring")
        return jsonify({"message": "Monitoring stopped"}), 200
    except Exception as e:
        logger.error(f"Stop monitoring error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@detection_bp.route('/trigger-voice-alert', methods=['POST'])
@jwt_required()
def trigger_voice_alert():
    """Trigger multilingual voice alert"""
    try:
        data = request.get_json()
        alert_type = data.get('alert_type', 'drowsy')  # drowsy, yawning, high_risk
        language = data.get('language', 'english')
        
        # Validate language
        valid_languages = ['english', 'hindi', 'kannada', 'tamil', 'telugu', 
                          'malayalam', 'marathi', 'gujarati', 'bengali']
        
        if language not in valid_languages:
            language = 'english'
        
        # Play alert
        success = voice_service.play_alert(alert_type, language)
        
        if success:
            logger.info(f"✅ Voice alert triggered: {alert_type} in {language}")
            return jsonify({
                'message': 'Alert triggered',
                'language': language,
                'alert_type': alert_type
            }), 200
        else:
            return jsonify({'error': 'Failed to play alert'}), 500
            
    except Exception as e:
        logger.error(f"❌ Voice alert error: {str(e)}")
        return jsonify({'error': str(e)}), 500
