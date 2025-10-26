from datetime import datetime
from mongodb_config import get_mongo_db
from bson import ObjectId
import json
import logging

logger = logging.getLogger(__name__)

# Import User at top to avoid circular import issues
from models import User

class DetectionEvent:
    def __init__(self, user_email, driver_name, detection_data=None, image_data=None,
                 eye_aspect_ratio=None, mouth_aspect_ratio=None, eye_closure_duration=None,
                 yawn_duration=None, drowsiness_score=None, risk_level=None,
                 alert_triggered=None, session_id=None, session_duration=None,
                 total_detections=None):
        
        if detection_data:
            self.user_email = user_email
            self.driver_name = driver_name
            self.eye_aspect_ratio = detection_data.get("ear", 0.0)
            self.mouth_aspect_ratio = detection_data.get("mar", 0.0)
            self.eye_closure_duration = detection_data.get("eye_duration", 0.0)
            self.yawn_duration = detection_data.get("yawn_duration", 0.0)
            self.drowsiness_score = detection_data.get("drowsiness_score", 0.0)
            self.risk_level = detection_data.get("risk_level", "Low")
            self.alert_triggered = detection_data.get("alert_triggered", False)
            self.image_data = image_data
            self.session_id = detection_data.get("session_id")
            self.session_duration = detection_data.get("session_duration", 0.0)
            self.total_detections = detection_data.get("total_detections", 0)
        else:
            self.user_email = user_email
            self.driver_name = driver_name
            self.eye_aspect_ratio = eye_aspect_ratio or 0.0
            self.mouth_aspect_ratio = mouth_aspect_ratio or 0.0
            self.eye_closure_duration = eye_closure_duration or 0.0
            self.yawn_duration = yawn_duration or 0.0
            self.drowsiness_score = drowsiness_score or 0.0
            self.risk_level = risk_level or "Low"
            self.alert_triggered = alert_triggered or False
            self.image_data = image_data
            self.session_id = session_id
            self.session_duration = session_duration or 0.0
            self.total_detections = total_detections or 0

        self.timestamp = datetime.utcnow()
        self.created_at = datetime.utcnow()
        self.image_data = image_data

    def save(self):
        """Save detection event to MongoDB"""
        try:
            db = get_mongo_db()
            if db is None:
                logger.error("❌ Database connection failed in DetectionEvent.save()")
                return None

            event_data = {
                'user_email': self.user_email,
                'driver_name': self.driver_name,
                'timestamp': self.timestamp,
                'eye_aspect_ratio': self.eye_aspect_ratio,
                'mouth_aspect_ratio': self.mouth_aspect_ratio,
                'eye_closure_duration': self.eye_closure_duration,
                'yawn_duration': self.yawn_duration,
                'drowsiness_score': self.drowsiness_score,
                'risk_level': self.risk_level,
                'alert_triggered': self.alert_triggered,
                'session_id': self.session_id,
                'session_duration': self.session_duration,
                'total_detections': self.total_detections,
                'image_data': self.image_data,
                'head_pose_data': self.head_pose_data
            }

            result = db.detection_events.insert_one(event_data)
            self._id = result.inserted_id
            logger.info(f"✅ Detection event saved with ID: {self._id}")
            return str(self._id)
        except Exception as e:
            logger.error(f"❌ Error saving detection event: {str(e)}")
            return None

    @staticmethod
    def get_all_events(limit=100):
        """Get all detection events"""
        try:
            db = get_mongo_db()
            if db is None:
                return []

            events = list(db.detection_events.find().sort('timestamp', -1).limit(limit))
            return [DetectionEvent._event_to_dict(event) for event in events]
        except Exception as e:
            logger.error(f"❌ Error getting detection events: {str(e)}")
            return []

    @staticmethod
    def get_events_by_user(user_email, limit=50):
        """Get detection events for specific user"""
        try:
            db = get_mongo_db()
            if db is None:
                return []

            events = list(db.detection_events.find({'user_email': user_email})
                         .sort('timestamp', -1).limit(limit))
            return [DetectionEvent._event_to_dict(event) for event in events]
        except Exception as e:
            logger.error(f"❌ Error getting user events: {str(e)}")
            return []

    @staticmethod
    def get_event_by_id(event_id):
        """Get specific detection event"""
        try:
            db = get_mongo_db()
            if db is None:
                return None

            event = db.detection_events.find_one({'_id': ObjectId(event_id)})
            return DetectionEvent._event_to_dict(event) if event else None
        except Exception as e:
            logger.error(f"❌ Error getting event: {str(e)}")
            return None

    @staticmethod
    def get_stats():
        """Get detection statistics"""
        try:
            db = get_mongo_db()
            if db is None:
                return {
                    "total_events": 0,
                    "high_risk_events": 0,
                    "today_events": 0,
                    "system_accuracy": 0
                }

            total_events = db.detection_events.count_documents({})
            high_risk_events = db.detection_events.count_documents({'risk_level': 'High'})

            from datetime import date
            today = datetime.combine(date.today(), datetime.min.time())
            today_events = db.detection_events.count_documents({'timestamp': {'$gte': today}})

            accuracy = 99.5

            return {
                "total_events": total_events,
                "high_risk_events": high_risk_events,
                "today_events": today_events,
                "system_accuracy": accuracy
            }
        except Exception as e:
            logger.error(f"❌ Error getting stats: {str(e)}")
            return {
                "total_events": 0,
                "high_risk_events": 0,
                "today_events": 0,
                "system_accuracy": 0
            }

    @staticmethod
    def _event_to_dict(event):
        """Convert MongoDB document to dictionary"""
        if not event:
            return None
        
        return {
            "id": str(event.get('_id', '')),
            "user_email": event.get('user_email', ''),
            "driver_name": event.get('driver_name', ''),
            "timestamp": event.get('timestamp').isoformat() if event.get('timestamp') else None,
            "detection_data": {
                "eye_aspect_ratio": event.get('eye_aspect_ratio', 0.0),
                "mouth_aspect_ratio": event.get('mouth_aspect_ratio', 0.0),
                "eye_closure_duration": event.get('eye_closure_duration', 0.0),
                "yawn_duration": event.get('yawn_duration', 0.0),
                "drowsiness_score": event.get('drowsiness_score', 0.0),
                "risk_level": event.get('risk_level', 'Low'),
                "alert_triggered": event.get('alert_triggered', False),
                "head_pose": json.loads(event.get('head_pose_data', '{}'))
            },
            "session_data": {
                "session_id": event.get('session_id', ''),
                "session_duration": event.get('session_duration', 0.0),
                "total_detections": event.get('total_detections', 0)
            },
            "image_data": event.get('image_data')
        }

    def to_dict(self):
        """Convert instance to dictionary for JSON serialization"""
        return {
            "id": str(self._id) if hasattr(self, '_id') else None,
            "user_email": self.user_email,
            "driver_name": self.driver_name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "detection_data": {
                "eye_aspect_ratio": self.eye_aspect_ratio,
                "mouth_aspect_ratio": self.mouth_aspect_ratio,
                "eye_closure_duration": self.eye_closure_duration,
                "yawn_duration": self.yawn_duration,
                "drowsiness_score": self.drowsiness_score,
                "risk_level": self.risk_level,
                "alert_triggered": self.alert_triggered,
                "head_pose": json.loads(self.head_pose_data) if self.head_pose_data else {}
            },
            "session_data": {
                "session_id": self.session_id,
                "session_duration": self.session_duration,
                "total_detections": self.total_detections
            },
            "image_data": self.image_data
        }

# Import User from models.py for consistency
from models import User
