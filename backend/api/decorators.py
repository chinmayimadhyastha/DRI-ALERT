# api/decorators.py
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from models import User  # FIXED: Changed from api.models

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # FIXED: Changed from SQLAlchemy to MongoDB query
        current_user = User.find_by_email(get_jwt_identity())
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
        
        if current_user.role != 'admin':
            return jsonify({"error": "Admin privileges required"}), 403
        
        return fn(*args, **kwargs)
    return wrapper

def driver_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # FIXED: Changed from SQLAlchemy to MongoDB query
        current_user = User.find_by_email(get_jwt_identity())
        
        if not current_user:
            return jsonify({"error": "User not found"}), 404
        
        if current_user.role != 'driver':
            return jsonify({"error": "Driver privileges required"}), 403
        
        return fn(*args, **kwargs)
    return wrapper
