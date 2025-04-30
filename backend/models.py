from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from api import db

class User(db.Model):
    """User model for authentication and role-based access control"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='driver')
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with Detection model
    detections = db.relationship('Detection', backref='user_rel', lazy=True)

    def __init__(self, email, password, role='driver'):
        self.email = email
        self.password = generate_password_hash(password)
        self.role = role

    def check_password(self, password):
        """Verify password against stored hash"""
        return check_password_hash(self.password, password)

    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<User {self.email}>'

class Detection(db.Model):
    """Detection model for storing drowsiness detection results"""
    __tablename__ = 'detections'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # 'drowsy', 'awake', etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    confidence = db.Column(db.Float, nullable=True)  # Optional confidence score
    image_path = db.Column(db.String(255), nullable=True)  # Optional path to image
    
    def to_dict(self):
        """Convert detection object to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'confidence': self.confidence,
            'image_path': self.image_path
        }

    def __repr__(self):
        return f'<Detection {self.id}>'