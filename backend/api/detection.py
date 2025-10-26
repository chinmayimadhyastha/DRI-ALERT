import cv2
import numpy as np
import mediapipe as mp
from scipy.spatial import distance
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DrowsinessDetector:
    def __init__(self):
        # Detection thresholds
        self.EAR_THRESHOLD = 0.21
        self.EAR_CONSEC_FRAMES = 3
        self.MAR_THRESHOLD = 0.6
        self.MAR_CONSEC_FRAMES = 3
        
        # Scoring system
        self.SLEEP_SCORE_INCREMENT = 10
        self.SLEEP_SCORE_DECREMENT = 2
        self.YAWN_SCORE_INCREMENT = 15
        self.MAX_SLEEP_SCORE = 100
        self.ALERT_THRESHOLD = 30
        
        # State tracking
        self.sleep_score = 0
        self.eye_closed_frames = 0
        self.yawn_frames = 0
        self.eye_closed_duration = 0.0
        self.yawn_duration = 0.0
        self.last_eye_close_time = None
        self.last_yawn_time = None
        self.frame_count = 0
        self.session_id = None
        self.start_time = time.time()
        
        # Initialize MediaPipe FaceMesh
        try:
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            logger.info("✅ MediaPipe FaceMesh initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MediaPipe: {str(e)}")
            raise

    def calculate_ear(self, landmarks, eye_indices):
        """Calculate Eye Aspect Ratio from MediaPipe landmarks"""
        try:
            # Get eye landmark coordinates
            points = [landmarks[i] for i in eye_indices]
            
            # Calculate distances
            # Vertical distances
            A = distance.euclidean([points[1].x, points[1].y], [points[5].x, points[5].y])
            B = distance.euclidean([points[2].x, points[2].y], [points[4].x, points[4].y])
            # Horizontal distance
            C = distance.euclidean([points[0].x, points[0].y], [points[3].x, points[3].y])
            
            # EAR calculation
            ear = (A + B) / (2.0 * C)
            return ear
        except Exception as e:
            logger.error(f"EAR calculation error: {str(e)}")
            return 0.3

    def calculate_mar(self, landmarks, mouth_indices):
        """Calculate Mouth Aspect Ratio from MediaPipe landmarks"""
        try:
            # Get mouth landmark coordinates
            points = [landmarks[i] for i in mouth_indices]
            
            # Calculate distances
            # Vertical distances
            A = distance.euclidean([points[2].x, points[2].y], [points[10].x, points[10].y])
            B = distance.euclidean([points[4].x, points[4].y], [points[8].x, points[8].y])
            # Horizontal distance
            C = distance.euclidean([points[0].x, points[0].y], [points[6].x, points[6].y])
            
            # MAR calculation
            mar = (A + B) / (2.0 * C)
            return mar
        except Exception as e:
            logger.error(f"MAR calculation error: {str(e)}")
            return 0.0

    def detect_drowsiness(self, frame):
        """Detect drowsiness using MediaPipe"""
        try:
            # Validate input frame
            if frame is None or frame.size == 0:
                logger.warning("⚠️ Empty frame received")
                return None
            
            self.frame_count += 1
            current_time = time.time()
            
            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process with MediaPipe
            results = self.face_mesh.process(rgb_frame)
            
            # Check if face detected
            if not results.multi_face_landmarks:
                logger.debug("No face detected in frame")
                return {
                    'ear': 0.3,
                    'mar': 0.0,
                    'eye_duration': 0.0,
                    'yawn_duration': 0.0,
                    'drowsiness_score': self.sleep_score,
                    'risk_level': 'Unknown',
                    'alert_triggered': False,
                    'session_id': self.session_id,
                    'session_duration': current_time - self.start_time,
                    'total_detections': self.frame_count,
                    'face_detected': False
                }
            
            # Get landmarks for first face
            face_landmarks = results.multi_face_landmarks[0].landmark
            
            # MediaPipe landmark indices for eyes and mouth
            # Left eye: 33, 160, 158, 133, 153, 144
            # Right eye: 362, 385, 387, 263, 373, 380
            # Mouth: 61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291
            
            left_eye_indices = [33, 160, 158, 133, 153, 144]
            right_eye_indices = [362, 385, 387, 263, 373, 380]
            mouth_indices = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291]
            
            # Calculate ratios
            left_ear = self.calculate_ear(face_landmarks, left_eye_indices)
            right_ear = self.calculate_ear(face_landmarks, right_eye_indices)
            ear = (left_ear + right_ear) / 2.0
            
            mar = self.calculate_mar(face_landmarks, mouth_indices)
            
            # Eye closure detection
            if ear < self.EAR_THRESHOLD:
                self.eye_closed_frames += 1
                
                if self.last_eye_close_time is None:
                    self.last_eye_close_time = current_time
                
                if self.eye_closed_frames >= self.EAR_CONSEC_FRAMES:
                    self.sleep_score = min(self.sleep_score + self.SLEEP_SCORE_INCREMENT, 
                                          self.MAX_SLEEP_SCORE)
                    self.eye_closed_duration = current_time - self.last_eye_close_time
            else:
                if self.eye_closed_frames > 0:
                    self.sleep_score = max(0, self.sleep_score - self.SLEEP_SCORE_DECREMENT)
                self.eye_closed_frames = 0
                self.last_eye_close_time = None
                self.eye_closed_duration = 0.0
            
            # Yawning detection
            if mar > self.MAR_THRESHOLD:
                self.yawn_frames += 1
                
                if self.last_yawn_time is None:
                    self.last_yawn_time = current_time
                
                if self.yawn_frames >= self.MAR_CONSEC_FRAMES:
                    self.sleep_score = min(self.sleep_score + self.YAWN_SCORE_INCREMENT,
                                          self.MAX_SLEEP_SCORE)
                    self.yawn_duration = current_time - self.last_yawn_time
            else:
                self.yawn_frames = 0
                self.last_yawn_time = None
                self.yawn_duration = 0.0
            
            # Determine risk level
            if self.sleep_score >= 70:
                risk_level = "Critical"
            elif self.sleep_score >= 50:
                risk_level = "High"
            elif self.sleep_score >= 30:
                risk_level = "Medium"
            else:
                risk_level = "Low"
            
            alert_triggered = self.sleep_score >= self.ALERT_THRESHOLD
            session_duration = current_time - self.start_time
            
            logger.info(f"✅ EAR: {ear:.3f}, MAR: {mar:.3f}, Score: {self.sleep_score}, Risk: {risk_level}")
            
            # Return detection results
            return {
                'ear': float(ear),
                'mar': float(mar),
                'eye_duration': float(self.eye_closed_duration),
                'yawn_duration': float(self.yawn_duration),
                'drowsiness_score': float(self.sleep_score),
                'risk_level': risk_level,
                'alert_triggered': bool(alert_triggered),
                'session_id': self.session_id,
                'session_duration': float(session_duration),
                'total_detections': int(self.frame_count),
                'face_detected': True
            }
            
        except Exception as e:
            logger.error(f"❌ Error in detect_drowsiness: {str(e)}", exc_info=True)
            return None

    def reset_session(self):
        """Reset detection session"""
        self.sleep_score = 0
        self.eye_closed_frames = 0
        self.yawn_frames = 0
        self.eye_closed_duration = 0.0
        self.yawn_duration = 0.0
        self.last_eye_close_time = None
        self.last_yawn_time = None
        self.frame_count = 0
        self.start_time = time.time()
        logger.info("✅ Session reset")

# Global detector instance
_detector_instance = None

def get_detector():
    """Get or create detector instance"""
    global _detector_instance
    if _detector_instance is None:
        try:
            _detector_instance = DrowsinessDetector()
            logger.info("✅ Detector instance created")
        except Exception as e:
            logger.error(f"❌ Failed to create detector: {str(e)}")
            raise
    return _detector_instance
